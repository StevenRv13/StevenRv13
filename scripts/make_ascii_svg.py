#!/usr/bin/env python3
"""Convert the prepared portrait into a one-shot, self-typing ASCII SVG."""

from __future__ import annotations

import html
import os
from pathlib import Path

from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "source-prepped.png"
OUTPUT = ROOT / "avi-ascii.svg"

COLS = int(os.environ.get("COLS", "112"))
ROWS = 60
RAMP = " .`:-=+*cs#%@"
ART_W = 720
ART_H = 620
PAD = 20
TITLE_H = 42
STATUS_H = 58
WIDTH = ART_W + PAD * 2
HEIGHT = TITLE_H + ART_H + STATUS_H

BG = "#0d1117"
BG_TOP = "#111827"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#d1d5db"


def ascii_rows() -> list[str]:
    image = Image.open(SOURCE).convert("L")
    image = ImageEnhance.Contrast(image).enhance(1.12)
    image = image.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    pixels = image.load()
    rows = []
    for y in range(ROWS):
        line = []
        for x in range(COLS):
            luminance = (pixels[x, y] / 255.0) ** 1.08
            if luminance > 0.94:
                line.append(" ")
            else:
                index = round((1.0 - luminance) * (len(RAMP) - 1))
                line.append(RAMP[max(0, min(index, len(RAMP) - 1))])
        rows.append("".join(line))
    return rows


def render() -> str:
    static = bool(os.environ.get("STATIC"))
    rows = ascii_rows()
    cell_h = ART_H / ROWS
    cell_w = ART_W / COLS
    row_duration = 0.07

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="14" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{WIDTH}" y2="{TITLE_H}" stroke="{FRAME}"/>',
    ]
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + 18 * i}" cy="21" r="6" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="26" fill="{MUTED}" font-size="14" text-anchor="middle">'
        'steven@github: ~$ ./portrait.sh</text>'
    )

    for row_index, line in enumerate(rows):
        row_y = TITLE_H + row_index * cell_h
        text_y = row_y + cell_h * 0.8
        safe = html.escape(line)
        text = (
            f'<text xml:space="preserve" x="{PAD}" y="{text_y:.2f}" fill="{INK}" '
            f'font-size="{cell_h * 0.9:.2f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>'
        )
        if static:
            parts.append(text)
            continue
        delay = row_index * row_duration
        parts.append(
            f'<clipPath id="row-{row_index}"><rect x="{PAD}" y="{row_y:.2f}" height="{cell_h:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.2f}s" dur="{row_duration:.2f}s" fill="freeze"/>'
            '</rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#row-{row_index})">{text}</g>')
        parts.append(
            f'<rect y="{row_y + 1:.2f}" width="{cell_w:.2f}" height="{cell_h - 2:.2f}" fill="{INK}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W}" begin="{delay:.2f}s" dur="{row_duration:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.9" begin="{delay:.2f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay + row_duration:.2f}s"/></rect>'
        )

    status_y = TITLE_H + ART_H
    parts.extend(
        [
            f'<line x1="0" y1="{status_y}" x2="{WIDTH}" y2="{status_y}" stroke="{FRAME}"/>',
            f'<text x="{PAD}" y="{status_y + 34}" fill="{MUTED}" font-size="16">steven@github:~$ whoami '
            f'<tspan fill="{INK}">Steven Ramirez</tspan></text>',
            f'<rect x="342" y="{status_y + 19}" width="9" height="18" fill="{INK}">'
            '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>',
            '</svg>',
        ]
    )
    return "".join(parts)


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUTPUT}")
