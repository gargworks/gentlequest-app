"""Lever contract: modular operator over the .brain/ substrate.

A Lever is a small, self-contained unit that:
  1. reads a declarative manifest (YAML)
  2. observes current state via the .brain/ ledger
  3. takes one well-defined action
  4. returns an observation dict that the dispatcher appends to the ledger

Levers must not keep private state outside .brain/. That is how modular
operators compound — through a shared substrate, not through each other.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class Lever(ABC):
    name: str = ""

    @abstractmethod
    def run(self, manifest: Dict[str, Any], brain_path: Path) -> Dict[str, Any]:
        """Execute the lever.

        Returns:
          {
            "outcome": "clean" | "found" | "error",
            "detail": <lever-specific payload>,
          }
        """
        ...
