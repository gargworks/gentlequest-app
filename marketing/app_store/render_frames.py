#!/usr/bin/env python3
"""Render each .frame-col from screenshots_source.html to a 1290x2796 PNG
suitable for App Store Connect upload (iPhone 6.7" display size).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "screenshots_source.html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

FRAMES = [
    (1, "mood_entry"),
    (2, "chat_first_turn"),
    (3, "journal"),
    (4, "weekly_review"),
    (5, "crisis"),
    (6, "settings"),
]

OVERRIDE = """<style id="export-override">
  html, body { background: transparent !important; }
  .canvas-wrap { display: block !important; padding: 0 !important; gap: 0 !important; }
  .frame-col { display: none !important; gap: 0 !important; }
  .frame-col[data-frame-active] { display: block !important; }
  .frame-col[data-frame-active] .frame-label { display: none !important; }
  .screenshot {
    transform: none !important;
    margin: 0 !important;
    box-shadow: none !important;
  }
</style>
"""


def render(idx: int, name: str, src_html: str) -> None:
    seen = [0]

    def activate(match: re.Match[str]) -> str:
        seen[0] += 1
        if seen[0] == idx:
            return match.group(0).replace(
                '<div class="frame-col"', '<div data-frame-active class="frame-col"'
            )
        return match.group(0)

    out_html = re.sub(r'<div class="frame-col"', lambda m: m.group(0), src_html)
    out_html = re.sub(r'<div class="frame-col"[^>]*>', activate, out_html)
    out_html = out_html.replace("</head>", OVERRIDE + "</head>", 1)

    tmp = HERE / f"_tmp_frame_{idx}.html"
    tmp.write_text(out_html, encoding="utf-8")

    out = HERE / f"frame_{idx}_{name}.png"
    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1290,2796",
            f"--screenshot={out}",
            f"file://{tmp}",
        ],
        check=False,
        stderr=subprocess.DEVNULL,
    )
    tmp.unlink(missing_ok=True)
    print(f"Rendered frame {idx}: {name} -> {out.name}")


def main() -> int:
    if not SRC.exists():
        print(f"FATAL: source HTML not found: {SRC}", file=sys.stderr)
        return 1
    src_html = SRC.read_text(encoding="utf-8")
    for idx, name in FRAMES:
        render(idx, name, src_html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
