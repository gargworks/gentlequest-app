import os
import subprocess
from pathlib import Path


def test_prod_smoke_uses_base_url_and_passes_with_fake_curl(tmp_path):
    fake_curl = tmp_path / "curl"
    calls = tmp_path / "calls.txt"
    fake_curl.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
args = sys.argv[1:]
out = None
url = ""
for i, arg in enumerate(args):
    if arg == "-o":
        out = args[i + 1]
    elif arg.startswith("http"):
        url = arg
if out:
    body = {"ok": True}
    if url.endswith("/api/journal"):
        body = {"id": "journal-smoke-id", "body": "smoke test"}
    Path(out).write_text(json.dumps(body))
calls_path = Path(os.environ["CALLS_FILE"])
with calls_path.open("a") as fh:
    fh.write(url + "\\n")
print("200 0.010")
"""
    )
    fake_curl.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["BASE_URL"] = "http://example.test"
    env["SMOKE_SESSION_ID"] = "smoke-session"
    env["CALLS_FILE"] = str(calls)

    result = subprocess.run(
        ["bash", "scripts/prod_smoke.sh", "--cleanup"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "failed=0" in result.stdout
    assert "http://example.test/api/health" in calls.read_text()
    assert "http://example.test/api/user" in calls.read_text()
    assert "http://example.test/api/user/push-tokens/smoke-token" in calls.read_text()
