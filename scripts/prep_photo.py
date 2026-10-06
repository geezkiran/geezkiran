"""Turn a portrait into a high-contrast grayscale plate for ASCII conversion.

1. Cut the background out so the wall does not print as noise.
2. Stretch contrast on the subject (CLAHE) so eyes, hair, and the shirt separate.
3. Composite onto white. White maps to a blank character later.

    python scripts/prep_photo.py source-photo.jpg
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "source-photo.jpg"
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "source-prepped.png"


def main() -> None:
    cut = remove(Image.open(SRC).convert("RGBA"))
    rgb = np.array(cut.convert("RGB"))
    alpha = np.array(cut.split()[-1])
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray).astype(np.float32)

    subject = alpha > 128
    if not subject.any():
        raise SystemExit(f"no subject found in {SRC}")
    lo, hi = np.percentile(contrasted[subject], [2, 96])
    if hi <= lo:
        hi = lo + 1
    tone = np.clip((contrasted - lo) / (hi - lo), 0, 1)

    mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.2)
    plate = (tone * mask + (1.0 - mask)) * 255.0

    ys, xs = np.where(alpha > 20)
    pad = 48
    side = max(int(xs.max() - xs.min()), int(ys.max() - ys.min())) + pad * 2
    cx = int((xs.min() + xs.max()) // 2)
    cy = int((ys.min() + ys.max()) // 2)
    x0, y0 = cx - side // 2, cy - side // 2

    canvas = np.full((side, side), 255, np.uint8)
    src_x0, src_y0 = max(x0, 0), max(y0, 0)
    src_x1 = min(x0 + side, plate.shape[1])
    src_y1 = min(y0 + side, plate.shape[0])
    dst_x0, dst_y0 = src_x0 - x0, src_y0 - y0
    canvas[dst_y0 : dst_y0 + (src_y1 - src_y0), dst_x0 : dst_x0 + (src_x1 - src_x0)] = (
        plate[src_y0:src_y1, src_x0:src_x1].astype(np.uint8)
    )

    Image.fromarray(canvas, mode="L").save(DST)
    print(f"wrote {DST} {canvas.shape[1]}x{canvas.shape[0]}")


if __name__ == "__main__":
    main()
