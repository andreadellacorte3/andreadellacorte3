"""Convert source-prepped.png into a monochrome ASCII SVG that types itself in (ascii-portrait.svg).

usage: python scripts/make_ascii_svg.py                 # from source-prepped.png
       python scripts/make_ascii_svg.py --text "ADC"    # placeholder: ASCII-shade a text banner
STATIC=1 writes a frozen frame for local previews.
"""

import argparse
import os
import re
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "ascii-portrait.svg"
CARD = ROOT / "info-card.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#       ^ leading space clears the background to nothing

COLS = 86
CHAR_W, LINE_H = 3.9, 7.0      # px per glyph / per row
FONT_SIZE = 6.5
WIDTH = 370
PAD, BAR = 14, 28              # inner padding, title-bar height
FILL = "#c9d1d9"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
ROW_STEP, ROW_DUR = 0.055, 0.28
STATIC = os.environ.get("STATIC") == "1"


def text_image(text):
    font = None
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            font = ImageFont.truetype(name, 220)
            break
        except OSError:
            continue
    font = font or ImageFont.load_default()
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    box = [int(v) for v in probe.multiline_textbbox((0, 0), text, font=font, align="center", spacing=20)]
    img = Image.new("L", (box[2] - box[0] + 80, box[3] - box[1] + 80), 255)
    draw = ImageDraw.Draw(img)
    draw.multiline_text((40 - box[0], 40 - box[1]), text, font=font, fill=0, align="center", spacing=20)
    # soft vertical shading so the glyph ramp has something to work with
    arr = np.array(img).astype(float)
    shade = np.linspace(0, 45, arr.shape[0])[:, None]
    arr = np.where(arr < 128, arr + shade, 255)
    return Image.fromarray(arr.clip(0, 255).astype("uint8"))


def to_rows(img):
    w, h = img.size
    rows = max(1, round(COLS * (CHAR_W / LINE_H) * h / w))
    small = np.array(img.convert("L").resize((COLS, rows), Image.LANCZOS)).astype(float) / 255
    idx = ((1 - small) * len(RAMP)).astype(int).clip(0, len(RAMP) - 1)
    lines = ["".join(RAMP[i] for i in row) for row in idx]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def card_height():
    # the info card sits next to the portrait at native size, so match its height
    if not CARD.exists():
        return 0
    match = re.search(r'data-content-height="(\d+)"', CARD.read_text(encoding="utf-8"))
    return int(match.group(1)) if match else 0


def render(lines, title):
    text_w = COLS * CHAR_W
    x0 = (WIDTH - text_w) / 2
    content_h = round(BAR + 2 * PAD + len(lines) * LINE_H)
    height = max(content_h, card_height())
    y0 = BAR + PAD + (height - content_h) / 2
    clips, texts = [], []
    for k, line in enumerate(lines):
        y = y0 + k * LINE_H
        t = k * ROW_STEP
        attrs = (f'x="{x0:.1f}" y="{y + LINE_H - 1.5:.1f}" textLength="{text_w:.1f}" '
                 f'lengthAdjust="spacingAndGlyphs"')
        if STATIC:
            texts.append(f'<text {attrs}>{escape(line)}</text>')
            continue
        clips.append(
            f'<clipPath id="r{k}"><rect x="{x0:.1f}" y="{y:.1f}" width="0" height="{LINE_H}">'
            f'<animate attributeName="width" from="0" to="{text_w:.1f}" begin="{t:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>')
        texts.append(
            f'<text {attrs} clip-path="url(#r{k})">{escape(line)}</text>'
            f'<rect x="{x0:.1f}" y="{y + 0.5:.1f}" width="3.5" height="{LINE_H - 1}" fill="{FILL}" opacity="0">'
            f'<animate attributeName="x" from="{x0:.1f}" to="{x0 + text_w:.1f}" begin="{t:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.9" begin="{t:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{t + ROW_DUR:.3f}s"/></rect>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" data-content-height="{content_h}">
<style>text{{font:{FONT_SIZE}px {FONT};fill:{FILL};white-space:pre}} .bar{{font:11px {FONT};fill:#8b949e}}</style>
<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>
<path d="M0.5 {BAR}H{WIDTH - 0.5}" stroke="#30363d"/>
<circle cx="16" cy="14" r="5" fill="#ff5f56"/><circle cx="32" cy="14" r="5" fill="#ffbd2e"/><circle cx="48" cy="14" r="5" fill="#27c93f"/>
<text class="bar" x="{WIDTH / 2}" y="18" text-anchor="middle">{escape(title)}</text>
<defs>{"".join(clips)}</defs>
<g xml:space="preserve">{"".join(texts)}</g>
</svg>
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", help="render a text banner instead of source-prepped.png")
    args = parser.parse_args()
    img = text_image(args.text.replace("\\n", "\n")) if args.text else Image.open(SRC)
    lines = to_rows(img)
    OUT.write_text(render(lines, "~/portrait.txt"), encoding="utf-8")
    print(f"wrote {OUT.name}: {len(lines)} rows x {COLS} cols")


if __name__ == "__main__":
    main()
