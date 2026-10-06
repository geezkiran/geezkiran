"""Render source-prepped.png as a monochrome ASCII portrait that types itself.

GitHub strips scripts from READMEs, but an SVG referenced with <img> still
runs SMIL. Each row is a left-to-right clip, with a cursor on the wipe edge.
The portrait prints once and holds.

    python scripts/make_ascii_svg.py
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, no animation
"""

import html
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(os.environ.get("ASCII_SRC", ROOT / "source-prepped.png"))
DST = Path(os.environ.get("ASCII_OUT", ROOT / "kiran-ascii.svg"))

COLS = int(os.environ.get("COLS", "168"))
ART_W = 800.0
CELL_W = ART_W / COLS
CELL_H = CELL_W * 15 / 8
ROWS = round(COLS * 8 / 15)
RAMP = " .:-=+*#%@"
WHITE_FLOOR = 200

PAD = 20.0
TITLE_H = 30.0
STATUS_H = 34.0
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLE_H + ART_H + STATUS_H + PAD

INK = "#c9d1d9"
FRAME = "#30363d"
MUTED = "#7d8590"
PROMPT = "kiran@github: ~$ ./portrait.sh"
STATUS = "kiran@github:~$ whoami  Kiran"


def portrait_plate(path: Path) -> np.ndarray:
    """Crop toward the head and keep eyes, smile, and hair as dark strokes.

    A plain resize turns shirt weave and skin texture into static, and thin
    features disappear. Smoothing, then thickening only the dark strokes,
    is what still reads as a face at character resolution.
    """
    gray = np.array(Image.open(path).convert("L"))
    subject = gray < 245
    ys, xs = np.where(subject)
    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    side = int((bottom - top) * 0.80)
    cx = (left + right) // 2
    y0 = max(0, top - int(side * 0.03))
    x0 = max(0, cx - side // 2)
    crop = np.full((side, side), 255, np.uint8)
    patch = gray[y0 : y0 + side, x0 : x0 + side]
    crop[: patch.shape[0], : patch.shape[1]] = patch

    smooth = crop
    for _ in range(6):
        smooth = cv2.bilateralFilter(smooth, 9, 80, 80)
    fine = cv2.GaussianBlur(smooth, (0, 0), 1.4).astype(np.float32)
    coarse = cv2.GaussianBlur(smooth, (0, 0), 5.5).astype(np.float32)
    edges = np.clip((coarse - fine) / 16.0, 0, 1)
    edges[edges <= 0.22] = 0
    tone = np.clip((smooth.astype(np.float32) - 20) / 180.0, 0, 1)
    plate = np.clip(tone - 1.15 * edges, 0, 1)
    plate[plate < 0.42] = np.minimum(plate[plate < 0.42], 0.22)
    plate = np.where(edges > 0.35, np.minimum(plate, 0.15), plate)
    ink = (np.clip(plate, 0, 1) * 255).astype(np.uint8)

    speck = (ink < 180).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(speck, 8)
    for index in range(1, count):
        if stats[index, cv2.CC_STAT_AREA] < 80:
            ink[labels == index] = 255

    thick = cv2.erode(ink, np.ones((5, 5), np.uint8), iterations=1)
    return np.where(ink < 90, thick, ink).astype(np.uint8)


def sample_rows(path: Path) -> list[str]:
    small = cv2.resize(portrait_plate(path), (COLS, ROWS), interpolation=cv2.INTER_AREA)
    last = len(RAMP) - 1
    rows: list[str] = []
    for y in range(ROWS):
        chars: list[str] = []
        for x in range(COLS):
            lum = int(small[y, x])
            if lum >= WHITE_FLOOR:
                chars.append(" ")
                continue
            index = round((1.0 - lum / 255.0) * last)
            chars.append(RAMP[max(0, min(last, index))])
        rows.append("".join(chars))
    return rows


def svg_for(rows: list[str], static: bool) -> str:
    art_top = TITLE_H + 7
    font_size = CELL_H * 0.86
    row_dur = 6.0 / ROWS
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W:.0f}" height="{CANVAS_H:.0f}" '
            f'viewBox="0 0 {CANVAS_W:.1f} {CANVAS_H:.1f}" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            f'role="img" aria-label="Kiran ASCII portrait">'
        ),
        (
            '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#111722"/>'
            '<stop offset="1" stop-color="#0d1117"/>'
            "</linearGradient></defs>"
        ),
        f'<rect width="{CANVAS_W:.1f}" height="{CANVAS_H:.1f}" rx="12" fill="url(#bg)"/>',
        (
            f'<rect x="0.5" y="0.5" width="{CANVAS_W - 1:.1f}" height="{CANVAS_H - 1:.1f}" '
            f'rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>'
        ),
        f'<line x1="0" y1="{TITLE_H:.0f}" x2="{CANVAS_W:.1f}" y2="{TITLE_H:.0f}" stroke="{FRAME}"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        cx = 20 + index * 16
        parts.append(f'<circle cx="{cx}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{CANVAS_W / 2:.1f}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">{PROMPT}</text>'
    )

    cursor_w = CELL_W * 0.9
    cursor_h = font_size * 0.9
    for row_index, line in enumerate(rows):
        y = art_top + row_index * CELL_H
        baseline = y + CELL_H * 0.78
        begin = row_index * row_dur
        end = begin + row_dur
        text = (
            f'<text xml:space="preserve" x="{PAD:.0f}" y="{baseline:.1f}" fill="{INK}" '
            f'font-size="{font_size:.2f}" textLength="{ART_W:.1f}" lengthAdjust="spacing">'
            f"{html.escape(line)}</text>"
        )
        if static:
            parts.append(text)
            continue
        parts.append(
            f'<clipPath id="r{row_index}"><rect x="{PAD:.0f}" y="{y:.1f}" height="{CELL_H:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W:.1f}" '
            f'begin="{begin:.3f}s" dur="{row_dur:.3f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#r{row_index})">{text}</g>')
        parts.append(
            f'<rect y="{y + (CELL_H - cursor_h) / 2:.1f}" width="{cursor_w:.2f}" height="{cursor_h:.2f}" '
            f'fill="{INK}" opacity="0">'
            f'<animate attributeName="x" from="{PAD:.0f}" to="{PAD + ART_W:.1f}" '
            f'begin="{begin:.3f}s" dur="{row_dur:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{begin:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.3f}s"/>'
            f"</rect>"
        )

    status_rule = TITLE_H + ART_H + 8
    parts.append(
        f'<line x1="0" y1="{status_rule:.1f}" x2="{CANVAS_W:.1f}" y2="{status_rule:.1f}" stroke="{FRAME}"/>'
    )
    parts.append(
        f'<text xml:space="preserve" x="{PAD:.0f}" y="{status_rule + 22:.1f}" fill="{INK}" font-size="13">'
        f"{html.escape(STATUS)}</text>"
    )
    if not static:
        blink_x = PAD + len(STATUS) * 7.8
        parts.append(
            f'<rect x="{blink_x:.1f}" y="{status_rule + 10:.1f}" width="8" height="14" fill="{INK}">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" '
            f'dur="1.1s" begin="{ROWS * row_dur:.3f}s" repeatCount="indefinite"/>'
            f"</rect>"
        )
    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC} — run scripts/prep_photo.py first")
    static = bool(os.environ.get("STATIC"))
    markup = svg_for(sample_rows(SRC), static)
    DST.write_text(markup)
    print(f"wrote {DST} ({len(markup)} bytes, {CANVAS_W:.0f}x{CANVAS_H:.0f})")


if __name__ == "__main__":
    main()
