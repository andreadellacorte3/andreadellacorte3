"""Prep a portrait for ASCII conversion: remove background, boost local contrast, flatten onto white.

usage: python scripts/prep_photo.py source-photo.jpg [--top 0.5]   ->  source-prepped.png
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"


def key_out_backdrop(img):
    """Fallback for studio shots: mask pixels close to the backdrop colour sampled from the border."""
    lab = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2LAB).astype(float)
    border = np.concatenate([lab[:20].reshape(-1, 3), lab[:, :20].reshape(-1, 3), lab[:, -20:].reshape(-1, 3)])
    dist = np.linalg.norm(lab - np.median(border, axis=0), axis=2)
    spread = np.percentile(np.linalg.norm(border - np.median(border, axis=0), axis=1), 95)

    # seed GrabCut: near-backdrop pixels are probable background, the rest probable foreground
    mask = np.where(dist > 2 * spread, cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype("uint8")
    mask[dist > 5 * spread] = cv2.GC_FGD
    mask[:10], mask[:, :10], mask[:, -10:] = cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(np.array(img)[:, :, ::-1].copy(), mask, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
    fg = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype("uint8")

    # keep only the largest blob (the subject) and fill any holes inside it
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        fg = (labels == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype("uint8")
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(fg, contours, -1, 1, thickness=cv2.FILLED)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    alpha = cv2.GaussianBlur(fg * 255, (5, 5), 0)
    rgba = img.convert("RGBA")
    rgba.putalpha(Image.fromarray(alpha))
    return rgba


def remove_background(img):
    try:
        from rembg import remove  # optional: pip install rembg (downloads a ~170MB model once)
    except ImportError:
        print("rembg not installed - keying out the backdrop colour instead")
        return key_out_backdrop(img)
    return remove(img)


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("photo")
    parser.add_argument("--top", type=float, default=1.0,
                        help="keep only this top fraction of the photo (e.g. 0.5 for head and shoulders)")
    args = parser.parse_args()
    img = Image.open(args.photo)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = img.crop((0, 0, img.width, round(img.height * args.top)))
    img = remove_background(img)

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

    # crop to the subject; keep the cut-out as alpha so the ASCII step knows what is background
    ys, xs = np.where(alpha >= 40)
    if len(xs):
        pad = 10
        box = (slice(max(ys.min() - pad, 0), ys.max() + pad), slice(max(xs.min() - pad, 0), xs.max() + pad))
        boosted, alpha = boosted[box], alpha[box]

    Image.merge("LA", (Image.fromarray(boosted), Image.fromarray(alpha))).save(OUT)
    print(f"wrote {OUT.name} {boosted.shape[1]}x{boosted.shape[0]}")


if __name__ == "__main__":
    main()
