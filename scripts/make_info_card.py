#!/usr/bin/env python3
"""Generate an animated neofetch-style developer profile card."""

from __future__ import annotations

import html
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "info-card.svg"

WIDTH = 1000
HEIGHT = 720
BG = "#0d1117"
BG_TOP = "#111827"
FRAME = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
CYAN = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"

ROWS = [
    ("Role", "Freelance Developer", CYAN),
    ("Focus", "Web & mobile experiences", GREEN),
    ("Learning", "React Native", GOLD),
    ("Frontend", "JavaScript · React · Tailwind CSS", CYAN),
    ("Backend", "Java · PHP · Laravel · Python", GREEN),
    ("Data", "PostgreSQL · MySQL", GOLD),
    ("Tools", "Docker · Azure · Figma", CYAN),
    ("Building", "Useful products with clean interfaces", GREEN),
]


def render() -> str:
    static = bool(os.environ.get("STATIC"))
    css = "" if static else """
@keyframes line-in {
  from { opacity: 0; transform: translateX(-16px); }
  to { opacity: 1; transform: translateX(0); }
}
.line { opacity: 0; animation: line-in .42s cubic-bezier(.2,.8,.2,1) both; }
"""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="14" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="42" x2="{WIDTH}" y2="42" stroke="{FRAME}"/>',
    ]
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{20 + 18 * i}" cy="21" r="6" fill="{color}"/>')
    parts.extend(
        [
            f'<text x="{WIDTH / 2}" y="26" fill="{MUTED}" font-size="14" text-anchor="middle">steven@github: ~$ neofetch</text>',
            f'<text x="54" y="102" fill="{CYAN}" font-size="29" font-weight="700">Steven Ramirez</text>',
            f'<text x="54" y="136" fill="{MUTED}" font-size="16">StevenRv13@github</text>',
            f'<line x1="54" y1="159" x2="946" y2="159" stroke="{FRAME}"/>',
        ]
    )

    start_y = 205
    for index, (key, value, color) in enumerate(ROWS):
        y = start_y + index * 54
        delay = 0.18 + index * 0.13
        animation = "" if static else f' style="animation-delay:{delay:.2f}s"'
        parts.append(
            f'<g class="line"{animation}><text x="54" y="{y}" fill="{color}" font-size="18" font-weight="700">{html.escape(key)}</text>'
            f'<text x="206" y="{y}" fill="{TEXT}" font-size="18">{html.escape(value)}</text></g>'
        )

    palette_y = 665
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f", CYAN, "#a78bfa", "#f778ba", TEXT)):
        parts.append(f'<rect x="{54 + index * 43}" y="{palette_y}" width="30" height="18" rx="3" fill="{color}"/>')
    parts.append(
        f'<text x="946" y="{palette_y + 15}" fill="{MUTED}" font-size="14" text-anchor="end">always learning, always building</text>'
    )
    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUTPUT}")
