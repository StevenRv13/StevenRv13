#!/usr/bin/env python3
"""Prepare a portrait or avatar for clean monochrome ASCII conversion.

Background removal and OpenCV CLAHE are used when their optional dependencies
are installed. A Pillow-only fallback keeps the script useful everywhere.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent.parent


def remove_background(image: Image.Image) -> Image.Image:
    try:
        from rembg import remove
    except ImportError:
        print("rembg is unavailable; keeping the original background")
        return image.convert("RGBA")
    return remove(image.convert("RGBA"))


def enhance_with_opencv(gray: Image.Image) -> Image.Image:
    try:
        import cv2
        import numpy as np
    except ImportError:
        gray = ImageOps.autocontrast(gray, cutoff=1)
        return ImageEnhance.Contrast(gray).enhance(1.25)

    pixels = np.asarray(gray)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    enhanced = clahe.apply(pixels)
    enhanced = cv2.bilateralFilter(enhanced, 7, 38, 7)
    return Image.fromarray(enhanced, mode="L")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default=ROOT / "assets" / "source-photo.png")
    parser.add_argument("output", nargs="?", default=ROOT / "source-prepped.png")
    parser.add_argument("--keep-background", action="store_true")
    args = parser.parse_args()

    source = Image.open(args.input).convert("RGBA")
    cutout = source if args.keep_background else remove_background(source)

    white = Image.new("RGBA", cutout.size, "white")
    white.alpha_composite(cutout)
    gray = white.convert("L")
    gray = enhance_with_opencv(gray)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1.4, percent=125, threshold=3))
    gray = ImageOps.fit(gray, (720, 640), method=Image.Resampling.LANCZOS)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    gray.save(args.output)
    print(f"wrote {args.output} ({gray.width}x{gray.height})")


if __name__ == "__main__":
    main()
