"""Per-turn record writer with synchronous disk flush (P2 SPOF mitigation)."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

import jsonschema


class SchemaValidationError(ValueError):
    """Raised when a record fails schema validation. Fail-loud by contract."""


class PerTurnWriter:
    """Validates records against schema v1 and flushes synchronously per turn.

    Late-session crash without fsync invalidates a 50-turn run; the writer
    therefore calls os.fsync() on every append. Cross-process serialization is
    provided by an in-process lock — one writer instance per proxy process.
    """

    def __init__(self, schema_path: Path, out_path: Path) -> None:
        self.schema = json.loads(schema_path.read_text())
        self._validator = jsonschema.Draft202012Validator(self.schema)
        self._out_path = out_path
        self._out_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def write(self, record: dict[str, Any]) -> None:
        errors = sorted(self._validator.iter_errors(record), key=lambda e: e.path)
        if errors:
            detail = "; ".join(f"{list(e.absolute_path)}: {e.message}" for e in errors[:5])
            raise SchemaValidationError(f"per-turn record failed schema v1: {detail}")
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock:
            with open(self._out_path, "a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
