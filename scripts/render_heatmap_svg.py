"""Render data/contributions.json as an animated 53x7 heatmap SVG (contrib-heatmap.svg)."""

import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end)

WIDTH = 860
CELL, GAP = 12, 3
PITCH = CELL + GAP
X0, Y0 = 46, 44
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
STEP = 0.028  # seconds between diagonals
STATIC = os.environ.get("STATIC") == "1"


def fmt_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    days, stats = data["days"], data["stats"]
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    top = max(d["count"] for d in days)

    cells, months = [], []
    last_month_col = -10
    max_diag = 0
    for i, d in enumerate(days):
        col, row = divmod(i + offset, 7)
        level = d["level"]
        if top > 0 and d["count"] == top:
            level = 5
        diag = col + row
        max_diag = max(max_diag, diag)
        x, y = X0 + col * PITCH, Y0 + row * PITCH
        cells.append(f'<rect class="c d{diag}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                     f'rx="3" fill="{PALETTE[level]}"/>')
        date = dt.date.fromisoformat(d["date"])
        if row == 0 and date.day <= 7 and col - last_month_col >= 3:
            months.append(f'<text class="t" x="{x}" y="{Y0 - 10}">{date.strftime("%b")}</text>')
            last_month_col = col

    grid_bottom = Y0 + 7 * PITCH - GAP
    weekdays = "".join(
        f'<text class="t" x="{X0 - 10}" y="{Y0 + r * PITCH + CELL - 2}" text-anchor="end">{name}</text>'
        for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")))

    foot_y = grid_bottom + 34
    legend_x = WIDTH - 56 - len(PALETTE) * PITCH
    legend = "".join(f'<rect x="{legend_x + k * PITCH}" y="{foot_y - 10}" width="{CELL}" height="{CELL}" '
                     f'rx="3" fill="{c}"/>' for k, c in enumerate(PALETTE))
    legend = (f'<text class="t" x="{legend_x - 8}" y="{foot_y}" text-anchor="end">Less</text>{legend}'
              f'<text class="t" x="{legend_x + len(PALETTE) * PITCH + 4}" y="{foot_y}">More</text>')

    best = stats["best_day"]
    summary = (f'<tspan class="hi">{stats["total"]:,}</tspan> contributions in the last year'
               f'  ·  streak <tspan class="hi">{stats["current_streak"]}d</tspan>'
               f' (best {stats["longest_streak"]}d)')
    if best and best["count"]:
        summary += f'  ·  top day <tspan class="hi">{best["count"]}</tspan> on {fmt_date(best["date"])}'

    height = foot_y + 22
    end = max_diag * STEP + 0.5
    delays = "".join(f".d{k}{{animation-delay:{k * STEP:.3f}s}}" for k in range(max_diag + 1))
    anim = "" if STATIC else (
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
        "animation:drop .5s cubic-bezier(.2,.8,.2,1) forwards}"
        "@keyframes drop{from{opacity:0;transform:translateY(-8px) scale(.5)}to{opacity:1;transform:none}}"
        f"{delays}"
        f".f{{opacity:0;animation:fade .6s ease-out {end:.2f}s forwards}}"
        "@keyframes fade{to{opacity:1}}")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">
<style>
.t{{font:11px {FONT};fill:#8b949e}}
.s{{font:12px {FONT};fill:#8b949e}}
.hi{{fill:#39d353;font-weight:700}}
{anim}
</style>
<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>
{"".join(months)}
{weekdays}
{"".join(cells)}
<g class="f">
<text class="s" x="{X0}" y="{foot_y}">{summary}</text>
{legend}
</g>
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.name} ({len(days)} days)")


if __name__ == "__main__":
    main()
