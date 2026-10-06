"""Draw data/contributions.json as an animated contribution calendar.

Cells slide in once on a diagonal and then hold. The motion is SMIL inside
the SVG, which GitHub plays when the file is embedded with <img>.

    python scripts/render_heatmap_svg.py
"""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
DST = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
INK = "#c9d1d9"
MUTED = "#7d8590"
FRAME = "#30363d"
CANVAS_W = 860
CELL = 11
STEP = 14
PAD_X = 22
LABEL_W = 32
GRAPH_Y = 46


def weeks_of(days: list[dict]) -> list[list[dict | None]]:
    columns: list[list[dict | None]] = []
    column: list[dict | None] = [None] * 7
    started = False
    for day in days:
        row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
        if row == 0 and started:
            columns.append(column)
            column = [None] * 7
        column[row] = day
        started = True
    if started:
        columns.append(column)
    return columns


def month_labels(columns: list[list[dict | None]]) -> list[tuple[int, str]]:
    labels = []
    seen: set[tuple[int, int]] = set()
    for index, column in enumerate(columns):
        for day in column:
            if not day:
                continue
            current = date.fromisoformat(day["date"])
            key = (current.year, current.month)
            if current.day <= 7 and key not in seen:
                seen.add(key)
                labels.append((index, current.strftime("%b")))
            break
    return labels


def svg(payload: dict) -> str:
    columns = weeks_of(payload["days"])
    origin_x = PAD_X + LABEL_W
    graph_h = 7 * STEP
    legend_y = GRAPH_Y + graph_h + 28
    footer_y = legend_y + 28
    canvas_h = footer_y + 26

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{canvas_h}" '
            f'viewBox="0 0 {CANVAS_W} {canvas_h}" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            f'role="img" aria-label="GitHub contribution graph">'
        ),
        (
            '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/>'
            "</linearGradient></defs>"
        ),
        f'<rect width="{CANVAS_W}" height="{canvas_h}" rx="12" fill="url(#bg)"/>',
        (
            f'<rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{canvas_h - 1}" '
            f'rx="12" fill="none" stroke="{FRAME}"/>'
        ),
    ]

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = GRAPH_Y + row * STEP + CELL - 1
        parts.append(f'<text x="{PAD_X}" y="{y}" fill="{MUTED}" font-size="11">{name}</text>')

    for index, name in month_labels(columns):
        x = origin_x + index * STEP
        parts.append(f'<text x="{x}" y="28" fill="{MUTED}" font-size="12">{name}</text>')

    for col, column in enumerate(columns):
        for row, day in enumerate(column):
            if not day:
                continue
            color = PALETTE[min(day["level"], len(PALETTE) - 1)]
            x = origin_x + col * STEP
            y = GRAPH_Y + row * STEP
            delay = (col + row) * 0.012
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.3f}s" dur="0.28s" fill="freeze"/>'
                f'<animate attributeName="y" from="{y - 8}" to="{y}" begin="{delay:.3f}s" dur="0.28s" fill="freeze"/>'
                f"</rect>"
            )

    total = f'{payload["total"]:,}'
    parts.append(
        f'<text x="{PAD_X}" y="{footer_y}" fill="{INK}" font-size="14">'
        f"{total} contributions in the last year</text>"
    )

    legend_x = CANVAS_W - PAD_X - 150
    parts.append(f'<text x="{legend_x}" y="{legend_y}" fill="{MUTED}" font-size="12">Less</text>')
    for index, color in enumerate(PALETTE):
        x = legend_x + 40 + index * 16
        parts.append(f'<rect x="{x}" y="{legend_y - 10}" width="11" height="11" rx="2" fill="{color}"/>')
    parts.append(
        f'<text x="{legend_x + 40 + len(PALETTE) * 16}" y="{legend_y}" fill="{MUTED}" font-size="12">More</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    payload = json.loads(SRC.read_text())
    DST.write_text(svg(payload))
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
