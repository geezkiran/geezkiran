"""Neofetch-style panel that fades in line by line.

Edit LINES below when the story changes. This file is static — the daily
workflow does not regenerate it.

    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DST = ROOT / "info-card.svg"

CANVAS_W = 840
CANVAS_H = 888
INK = "#c9d1d9"
MUTED = "#7d8590"
KEY = "#7ee787"
FRAME = "#30363d"

LINES = [
    ("now", "Building ForQ"),
    ("role", "Founder & full-stack"),
    ("stack", "Next.js · React · TypeScript"),
    ("also", "Python · Node · Tailwind"),
    ("tools", "Figma · Blender"),
    ("focus", "Design, hardware, and code"),
    ("site", "kirandaily.com"),
]


def svg(static: bool) -> str:
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
            f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            f'role="img" aria-label="Kiran">'
        ),
        (
            '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/>'
            "</linearGradient></defs>"
        ),
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>',
        (
            f'<rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" '
            f'rx="12" fill="none" stroke="{FRAME}"/>'
        ),
        f'<line x1="0" y1="30" x2="{CANVAS_W}" y2="30" stroke="{FRAME}"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{20 + index * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{CANVAS_W / 2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">'
        f"kiran@github ~ $ whoami</text>"
    )

    parts.append(f'<text x="48" y="92" fill="{INK}" font-size="28">kiran</text>')
    parts.append(f'<text x="48" y="124" fill="{MUTED}" font-size="16">founder · full-stack · forq</text>')
    parts.append(f'<line x1="48" y1="148" x2="792" y2="148" stroke="{FRAME}"/>')

    for index, (key, value) in enumerate(LINES):
        y = 210 + index * 78
        begin = 0.35 + index * 0.16
        block = (
            f'<text x="48" y="{y}" fill="{KEY}" font-size="22">{key}</text>'
            f'<text x="190" y="{y}" fill="{INK}" font-size="22">{value}</text>'
        )
        if static:
            parts.append(block)
            continue
        parts.append(
            f'<g opacity="0">{block}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 10" to="0 0" begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>'
            f"</g>"
        )

    if not static:
        parts.append(
            f'<rect x="48" y="760" width="12" height="24" fill="{KEY}">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" '
            f'dur="1.1s" begin="1.6s" repeatCount="indefinite"/>'
            f"</rect>"
        )
    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    DST.write_text(svg(static=bool(os.environ.get("STATIC"))))
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
