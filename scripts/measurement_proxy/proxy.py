"""Reverse-proxy chassis — forwards Anthropic-API requests and emits per-turn records.

Usage:
    python -m scripts.measurement_proxy --port 8787 \\
        --out .brain/measurement/turns.jsonl \\
        --condition baseline --surface cc_main --phase dogfood

Clients set ``ANTHROPIC_BASE_URL=http://127.0.0.1:<port>`` and the proxy forwards
to ``https://api.anthropic.com/<path>`` preserving headers and query string.

Logging-only mode. One round-trip ⇒ one record to turns.jsonl. Request-side
``cache_control`` parsing + 3-stream attribution ship in PR-2 (cache_control
module); attribution_confidence is computed per turn from the decomposed-vs-billed
delta and may be ``high`` | ``partial`` | ``fallback_aggregate``.

Streaming (SSE) responses pass through transparently but accumulate across
chunks into the response-side usage payload; streaming_flag is recorded in meta.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import http.client
import json
import logging
import ssl
import sys
import threading
import time
import zlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

from .cache_control import compute_per_stream_attribution, parse_cache_control
from .fairness_pins import FairnessViolation, RunConfig, assert_fairness
from .writer import PerTurnWriter, SchemaValidationError


_UPSTREAM_HOST = "api.anthropic.com"
_HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailers", "upgrade", "host", "content-length"}
_LOG = logging.getLogger("measurement_proxy")


class _TurnCounter:
    """Wall-clock per-session turn counter (meta.turn_counter_source=wall_clock_harness)."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self._lock = threading.Lock()

    def next(self, session_id: str) -> int:
        with self._lock:
            n = self._counts.get(session_id, 0) + 1
            self._counts[session_id] = n
            return n


class _ProxyConfig:
    def __init__(
        self,
        port: int,
        writer: PerTurnWriter,
        condition: str,
        surface_default: str,
        phase: str,
        cli_version_hint: str,
        strip_cache_control: bool = False,
    ) -> None:
        self.port = port
        self.writer = writer
        self.condition = condition
        self.surface_default = surface_default
        self.phase = phase
        self.cli_version_hint = cli_version_hint
        self.turns = _TurnCounter()
        self.strip_cache_control = strip_cache_control


def _strip_cache_control_from_body(body: dict[str, Any]) -> dict[str, Any]:
    """Remove every `cache_control` field from a parsed Anthropic request body.

    Walks system / tools[] / messages[].content[] and drops the
    `cache_control` key wherever it appears. Returns a NEW body dict; does
    not mutate the input. Used by the cache-off control arm to measure what
    the same traffic would cost without prompt caching enabled.
    """
    import copy
    out = copy.deepcopy(body)

    def _strip_block(b: Any) -> None:
        if isinstance(b, dict):
            b.pop("cache_control", None)

    sys_content = out.get("system")
    if isinstance(sys_content, list):
        for b in sys_content:
            _strip_block(b)

    for tool in out.get("tools") or []:
        _strip_block(tool)

    for msg in out.get("messages") or []:
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, list):
            for b in content:
                _strip_block(b)
    return out


def _infer_surface(user_agent: str, default: str) -> str:
    if "Anthropic/Python" in user_agent:
        return "cowork"
    if "claude-cli" in user_agent:
        return default
    return default


def _extract_session_id(headers: dict[str, str], fallback_body: dict[str, Any]) -> str:
    sid = headers.get("x-claude-code-session-id") or headers.get("X-Claude-Code-Session-Id")
    if sid:
        return sid
    md = (fallback_body or {}).get("metadata") or {}
    if isinstance(md, dict) and md.get("user_id"):
        return f"ua:{md['user_id']}"
    ua = headers.get("user-agent", "unknown")
    return f"ua:{hashlib.sha1(ua.encode()).hexdigest()[:12]}"


def _extract_model(body: dict[str, Any]) -> str:
    return body.get("model") or "unknown"


def _extract_thinking_budget(body: dict[str, Any]) -> int:
    thinking = body.get("thinking") or {}
    if isinstance(thinking, dict):
        bt = thinking.get("budget_tokens")
        if isinstance(bt, int):
            return bt
    return 0


def _count_tool_result_bytes(messages: list[Any]) -> int:
    total = 0
    for m in messages or []:
        content = m.get("content") if isinstance(m, dict) else None
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    total += len(json.dumps(b, ensure_ascii=False).encode("utf-8"))
    return total


def _build_record(
    config: _ProxyConfig,
    request_headers: dict[str, str],
    request_body_raw: bytes,
    response_body: bytes,
    response_usage: dict[str, Any],
    streaming: bool,
    ts_iso: str,
) -> dict[str, Any]:
    try:
        req_body = json.loads(request_body_raw) if request_body_raw else {}
    except json.JSONDecodeError:
        req_body = {}

    session_id = _extract_session_id(request_headers, req_body)
    surface = _infer_surface(request_headers.get("user-agent", ""), config.surface_default)
    model = _extract_model(req_body)
    thinking_budget = _extract_thinking_budget(req_body)

    messages = req_body.get("messages") or []
    system = req_body.get("system")
    system_blocks = 1 if system else 0
    message_blocks = len(messages)
    content_block_count = system_blocks + sum(
        len(m.get("content")) if isinstance(m.get("content"), list) else 1
        for m in messages
        if isinstance(m, dict)
    )

    cache_control_blocks = parse_cache_control(req_body)
    response_input = int(response_usage.get("input_tokens", 0) or 0)
    cache_read = int(response_usage.get("cache_read_input_tokens", 0) or 0)
    cache_creation = int(response_usage.get("cache_creation_input_tokens", 0) or 0)
    per_stream = compute_per_stream_attribution(req_body, response_input, cache_read, cache_creation)

    return {
        "schema_version": "v1",
        "turn_index": config.turns.next(session_id),
        "session_id": session_id,
        "surface": surface,
        "condition": config.condition,
        "phase": config.phase,
        "timestamp": ts_iso,
        "provider": "anthropic",
        "model": model,
        "request_usage_counters": {
            "content_block_count": content_block_count,
            "cache_control_blocks": cache_control_blocks,
            "total_input_bytes": len(request_body_raw),
            "messages_block_count": message_blocks,
            "tool_result_bytes_sum": _count_tool_result_bytes(messages),
        },
        "response_usage_counters": {
            "input_tokens": int(response_usage.get("input_tokens", 0) or 0),
            "output_tokens": int(response_usage.get("output_tokens", 0) or 0),
            "cache_creation_input_tokens": int(response_usage.get("cache_creation_input_tokens", 0) or 0),
            "cache_read_input_tokens": int(response_usage.get("cache_read_input_tokens", 0) or 0),
            "reasoning_tokens": int(response_usage.get("reasoning_tokens", 0) or 0),
            "retry_attempt": int(request_headers.get("x-stainless-retry-count", "0") or 0),
        },
        "per_stream_attribution": per_stream,
        "meta": {
            "cli_version": config.cli_version_hint,
            "cli_build_hash": request_headers.get("x-stainless-package-version", "unknown"),
            "mcp_server_state_snapshot_hash": "pr1-unpopulated",
            "parallelism_pattern": "identical_as_baseline",
            "streaming_flag": streaming,
            "thinking_budget_tokens": thinking_budget,
            "turn_counter_source": "wall_clock_harness",
            "non_claudemd_injection_sources": [],
            "request_id": request_headers.get("request-id", ""),
        },
    }


def _decompress_if_needed(body: bytes, content_encoding: str) -> bytes:
    """Return a plaintext body for parsing. Forward path keeps the original bytes."""
    enc = (content_encoding or "").lower().strip()
    if not enc or enc == "identity":
        return body
    try:
        if enc == "gzip":
            return gzip.decompress(body)
        if enc == "deflate":
            return zlib.decompress(body)
    except (OSError, zlib.error) as exc:
        _LOG.warning("decompress failed (encoding=%s): %s — treating as plaintext", enc, exc)
    return body


def _parse_sse_usage(stream_body: bytes) -> dict[str, Any]:
    """Extract final usage counters from a concatenated Anthropic SSE body."""
    usage: dict[str, Any] = {}
    for raw in stream_body.split(b"\n"):
        if not raw.startswith(b"data: "):
            continue
        payload = raw[len(b"data: "):].strip()
        if not payload or payload == b"[DONE]":
            continue
        try:
            evt = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if evt.get("type") in ("message_start", "message_delta"):
            msg_usage = (evt.get("message") or {}).get("usage") or evt.get("usage") or {}
            for k, v in msg_usage.items():
                if isinstance(v, int):
                    usage[k] = v
    return usage


class _Handler(BaseHTTPRequestHandler):
    config: _ProxyConfig  # set via closure factory

    def do_GET(self) -> None:
        if self.path == "/_measurement_health":
            payload = json.dumps({"status": "ok", "port": self.config.port}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self._forward(method="GET", body=b"")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length else b""
        self._forward(method="POST", body=body)

    def _forward(self, method: str, body: bytes) -> None:
        ts_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        headers_in = {k.lower(): v for k, v in self.headers.items()}
        forward_headers = {k: v for k, v in self.headers.items() if k.lower() not in _HOP_BY_HOP}
        forward_headers["Host"] = _UPSTREAM_HOST

        # Cache-off control arm (H4-(b)): strip cache_control from POST /v1/messages
        # bodies before forwarding upstream. Captured turn record retains the
        # ORIGINAL (un-stripped) body for attribution math; only the wire body
        # to Anthropic gets stripped, so response_usage_counters reflects the
        # cache-off reality.
        original_body = body
        if (
            self.config.strip_cache_control
            and method == "POST"
            and self.path.startswith("/v1/messages")
            and body
        ):
            try:
                parsed = json.loads(body)
                stripped = _strip_cache_control_from_body(parsed)
                body = json.dumps(stripped).encode("utf-8")
                forward_headers["Content-Length"] = str(len(body))
            except Exception:  # noqa: BLE001
                _LOG.warning("strip_cache_control parse failed; forwarding original body")

        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(_UPSTREAM_HOST, context=ctx, timeout=600)
        try:
            conn.request(method, self.path, body=body, headers=forward_headers)
            upstream = conn.getresponse()
            resp_body = upstream.read()
            resp_headers = [(k, v) for k, v in upstream.getheaders() if k.lower() not in _HOP_BY_HOP]
            self.send_response(upstream.status)
            for k, v in resp_headers:
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as exc:  # noqa: BLE001
            _LOG.exception("upstream forward failed: %s", exc)
            self.send_response(502)
            self.end_headers()
            return
        finally:
            conn.close()

        if method != "POST" or not self.path.startswith("/v1/messages"):
            return

        content_type = (upstream.headers.get("content-type") or "").lower()
        content_encoding = upstream.headers.get("content-encoding") or ""
        streaming = "event-stream" in content_type
        parse_body = _decompress_if_needed(resp_body, content_encoding)
        if streaming:
            response_usage = _parse_sse_usage(parse_body)
        else:
            try:
                response_usage = (json.loads(parse_body).get("usage") or {}) if parse_body else {}
            except json.JSONDecodeError:
                response_usage = {}

        try:
            # Pass the ORIGINAL (un-stripped) request body to _build_record so
            # the captured record reflects what the client actually sent. The
            # response_usage already reflects cache-off behavior because the
            # forwarded body was stripped.
            record = _build_record(
                self.config, headers_in, original_body, resp_body, response_usage, streaming, ts_iso
            )
            self.config.writer.write(record)
        except SchemaValidationError as exc:
            _LOG.error("dropping record — %s", exc)
        except Exception:  # noqa: BLE001
            _LOG.exception("writer failed")

    def log_message(self, fmt, *args) -> None:  # noqa: D401
        _LOG.debug("proxy %s", fmt % args)


def build_server(config: _ProxyConfig) -> ThreadingHTTPServer:
    handler_cls = type("_ConfiguredHandler", (_Handler,), {"config": config})
    return ThreadingHTTPServer(("127.0.0.1", config.port), handler_cls)


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    default_schema = repo_root / ".brain" / "measurement" / "schema.json"
    default_out = repo_root / ".brain" / "measurement" / "turns.jsonl"
    p = argparse.ArgumentParser(description="Compounding-multiplier measurement proxy (PR-1)")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--schema", type=Path, default=default_schema)
    p.add_argument("--out", type=Path, default=default_out)
    p.add_argument("--condition", choices=["baseline", "experimental", "cache_off"], default="baseline")
    p.add_argument(
        "--strip-cache-control",
        action="store_true",
        help="H4-(b) control arm: remove cache_control fields from request bodies "
             "before forwarding upstream. Use with --condition cache_off and a separate "
             "--out file for clean comparison against the cache_on baseline.",
    )
    p.add_argument("--phase", choices=["dogfood", "swe_bench"], default="dogfood")
    p.add_argument(
        "--surface",
        choices=["cc_main", "cc_peer", "cowork", "swe_bench_runner", "subagent"],
        default="cc_main",
        help="default surface for claude-cli User-Agent when not identifiable by session_id mapping",
    )
    p.add_argument("--cli-version-hint", default="unknown")
    p.add_argument(
        "--fairness-config",
        type=Path,
        default=None,
        help="Path to RunConfig JSON; if set, assert_fairness runs at startup and aborts on violation.",
    )
    p.add_argument(
        "--skip-fairness",
        action="store_true",
        help="Explicitly bypass fairness gate (smoke-test only — baseline runs MUST NOT use this).",
    )
    return p.parse_args(argv)


def _load_fairness_config(path: Path) -> RunConfig:
    payload = json.loads(path.read_text())
    payload["claudemd_path"] = Path(payload["claudemd_path"])
    return RunConfig(**payload)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parse_args(argv)
    if args.fairness_config is not None:
        cfg = _load_fairness_config(args.fairness_config)
        try:
            report = assert_fairness(cfg)
        except FairnessViolation as exc:
            _LOG.error("fairness gate FAILED — aborting: %s", exc)
            return 3
        _LOG.info("fairness gate PASSED (%d pins)", len(report.results))
    elif not args.skip_fairness:
        _LOG.error("refusing to start: pass --fairness-config <path> or --skip-fairness (smoke only)")
        return 4
    writer = PerTurnWriter(args.schema, args.out)
    config = _ProxyConfig(
        args.port, writer, args.condition, args.surface, args.phase, args.cli_version_hint,
        strip_cache_control=args.strip_cache_control,
    )
    server = build_server(config)
    _LOG.info(
        "measurement-proxy listening on http://127.0.0.1:%d "
        "(condition=%s surface=%s phase=%s strip_cache_control=%s)",
        args.port, args.condition, args.surface, args.phase, args.strip_cache_control,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _LOG.info("shutting down")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
