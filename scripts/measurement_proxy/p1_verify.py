"""P1 empirical verify — ANTHROPIC_BASE_URL http://localhost acceptance.

Build-blocker probe per cowork's build-fire (relay_20260421_015057_54a3ff87).
Spec: compounding_multiplier_wedge.md §4.1 reverse-proxy chassis.

Tests two clients:
    (a) anthropic Python SDK — flagged as the Cowork surface's transport
    (b) Claude Code Node CLI — flagged as CC-main / CC-peer surfaces' transport

For each, we set ANTHROPIC_BASE_URL=http://127.0.0.1:<ephemeral> pointing at a
localhost HTTP server that returns a minimal valid-shaped Anthropic response.
We then observe whether the client (1) rejects plaintext http:// with a TLS
error, (2) accepts http:// and sends the request, or (3) fails for an
unrelated reason.

Exit behavior:
    - Prints a structured report.
    - Exits 0 on either success (http:// accepted) or documented failure;
      exits non-zero only on unexpected test harness errors.
"""

from __future__ import annotations

import json
import os
import socketserver
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler


CAPTURED: list[dict] = []


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        CAPTURED.append(
            {
                "path": self.path,
                "method": "POST",
                "headers": {k: v for k, v in self.headers.items()},
                "body_bytes": len(body),
            }
        )
        resp = json.dumps(
            {
                "id": "msg_p1_test",
                "type": "message",
                "role": "assistant",
                "model": "claude-haiku-4-5-20251001",
                "content": [{"type": "text", "text": "ok"}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def do_GET(self) -> None:
        CAPTURED.append({"path": self.path, "method": "GET"})
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args) -> None:
        pass


def _start_server() -> tuple[socketserver.TCPServer, int]:
    server = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _probe_python_sdk(base_url: str) -> dict:
    """Probe anthropic Python SDK. Runs in-process."""
    os.environ["ANTHROPIC_BASE_URL"] = base_url
    os.environ["ANTHROPIC_API_KEY"] = "sk-test-dummy-p1-probe"
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError as exc:
        return {"status": "SKIP", "reason": f"import failed: {exc}"}

    try:
        client = Anthropic()
        result = client.messages.create(
            model="claude-haiku-4-5-20251001",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=10,
        )
        return {
            "status": "ACCEPTED",
            "reason": f"http:// reached server, SDK parsed response id={result.id}",
        }
    except Exception as exc:  # noqa: BLE001
        name = type(exc).__name__
        msg = str(exc)
        tls_markers = ("TLS", "SSL", "HTTPS", "certificate", "SSLError")
        looks_like_tls = any(m.lower() in msg.lower() or m in name for m in tls_markers)
        return {
            "status": "REJECTED_TLS" if looks_like_tls else "OTHER_ERROR",
            "reason": f"{name}: {msg[:200]}",
        }


def _probe_node_cli(base_url: str, claude_bin: str = "claude") -> dict:
    """Probe Claude Code Node CLI via `claude -p` (non-interactive print mode)."""
    env = dict(os.environ)
    env["ANTHROPIC_BASE_URL"] = base_url
    env["ANTHROPIC_API_KEY"] = "sk-test-dummy-p1-probe"
    env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    try:
        result = subprocess.run(
            [claude_bin, "-p", "ping", "--model", "claude-haiku-4-5-20251001"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
    except FileNotFoundError:
        return {"status": "SKIP", "reason": f"{claude_bin} not on PATH"}
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "reason": "claude -p exceeded 30s"}

    combined = (result.stdout or "") + (result.stderr or "")
    tls_markers = ("TLS", "SSL", "HTTPS", "certificate", "SELF_SIGNED")
    looks_like_tls = any(m.lower() in combined.lower() for m in tls_markers)
    return {
        "status": "ACCEPTED" if result.returncode == 0 else ("REJECTED_TLS" if looks_like_tls else "OTHER_ERROR"),
        "reason": f"rc={result.returncode} stdout_head={result.stdout[:140]!r} stderr_head={result.stderr[:240]!r}",
    }


def main() -> int:
    server, port = _start_server()
    base_url = f"http://127.0.0.1:{port}"
    print(f"[P1] Local HTTP server listening on {base_url}")

    report = {
        "base_url": base_url,
        "python_sdk": _probe_python_sdk(base_url),
        "captured_after_python": list(CAPTURED),
    }

    CAPTURED.clear()
    report["node_cli"] = _probe_node_cli(base_url)
    report["captured_after_node"] = list(CAPTURED)

    server.shutdown()

    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
