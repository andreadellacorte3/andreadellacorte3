"""Prep a portrait for ASCII conversion: remove background, boost local contrast, flatten onto white.

usage: python scripts/prep_photo.py source-photo.jpg   ->  source-prepped.png
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"


def remove_background(img):
    try:
        from rembg import remove  # optional: pip install rembg (downloads a ~170MB model once)
    except ImportError:
        print("rembg not installed - keeping the original background")
        return img.convert("RGBA")
    return remove(img)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    img = remove_background(Image.open(sys.argv[1]).convert("RGB"))

    # composite onto pure white so the background maps to the blank end of the ramp
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(white, img).convert("L")

    # CLAHE gives a flatly-lit face real highlights and shadows
    gray = np.array(flat)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)

    # keep the background pure white after equalization
    alpha = np.array(img.split()[-1])
    boosted[alpha < 40] = 255

    # crop to the subject
    ys, xs = np.where(boosted < 245)
    if len(xs):
        pad = 10
        boosted = boosted[max(ys.min() - pad, 0):ys.max() + pad, max(xs.min() - pad, 0):xs.max() + pad]

    Image.fromarray(boosted).save(OUT)
    print(f"wrote {OUT.name} {boosted.shape[1]}x{boosted.shape[0]}")


if __name__ == "__main__":
    main()
