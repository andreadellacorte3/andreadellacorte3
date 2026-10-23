"""Hand-authored neofetch-style info card (info-card.svg). Edit CONTENT below and re-run.

STATIC=1 writes a frozen frame for local previews.
"""

import os
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
PORTRAIT = ROOT / "ascii-portrait.svg"

USER, HOST = "andreadellacorte3", "github"
CONTENT = [
    ("Role", "MSc student · Italy"),
    ("Now", "MSc Transport, Infrastructure & Logistics"),
    ("", "TU Delft · 2025 - present"),
    ("Prev", "BSc Industrial Engineering"),
    ("", "Univ. of Salerno · 2021 - 2024"),
    ("Code", "Python"),
    ("Tools", "AutoCAD · SolidWorks · Excel · Canva"),
]

WIDTH = 490
BAR, PAD = 28, 22
LINE_H = 21
KEY_W = 62
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
STEP = 0.12
STATIC = os.environ.get("STATIC") == "1"
SWATCHES = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]


def portrait_height():
    if not PORTRAIT.exists():
        return 0
    # both SVGs render at native size side by side, so keep their heights equal
    match = re.search(r'data-content-height="(\d+)"', PORTRAIT.read_text(encoding="utf-8"))
    return int(match.group(1)) if match else 0


def main():
    x = 26
    y = BAR + PAD + 12
    lines = []

    head = f"{USER}@{HOST}"
    lines.append(f'<text x="{x}" y="{y}"><tspan class="u">{USER}</tspan><tspan class="v">@</tspan>'
                 f'<tspan class="u">{HOST}</tspan></text>')
    y += LINE_H - 4
    lines.append(f'<text class="v" x="{x}" y="{y}">{"-" * len(head)}</text>')
    y += LINE_H

    for key, value in CONTENT:
        label = f'<tspan class="k">{escape(key)}</tspan>' + ('<tspan class="v">:</tspan>' if key else "")
        lines.append(f'<text x="{x}" y="{y}">{label}</text>'
                     f'<text class="v" x="{x + KEY_W}" y="{y}">{escape(value)}</text>')
        y += LINE_H

    y += 6
    swatches = "".join(f'<rect x="{x + i * 26}" y="{y - 14}" width="22" height="14" rx="2" fill="{c}"/>'
                       for i, c in enumerate(SWATCHES))
    lines.append(swatches)
    y += 6

    height = max(round(y + PAD), portrait_height())
    groups = "".join(f'<g class="l" style="animation-delay:{0.3 + i * STEP:.2f}s">{ln}</g>'
                     for i, ln in enumerate(lines))
    anim = "" if STATIC else (
        ".l{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" data-content-height="{round(y + PAD)}">
<style>
text{{font:12.5px {FONT};fill:#c9d1d9;white-space:pre}}
.u{{fill:#39d353;font-weight:700}} .k{{fill:#58a6ff;font-weight:700}} .v{{fill:#c9d1d9}}
.bar{{font:11px {FONT};fill:#8b949e}}
{anim}
</style>
<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>
<path d="M0.5 {BAR}H{WIDTH - 0.5}" stroke="#30363d"/>
<circle cx="16" cy="14" r="5" fill="#ff5f56"/><circle cx="32" cy="14" r="5" fill="#ffbd2e"/><circle cx="48" cy="14" r="5" fill="#27c93f"/>
<text class="bar" x="{WIDTH / 2}" y="18" text-anchor="middle">{USER}@{HOST}: ~ $ neofetch</text>
{groups}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.name} ({WIDTH}x{height})")


if __name__ == "__main__":
    main()
