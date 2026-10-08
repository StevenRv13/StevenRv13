#!/usr/bin/env python3
"""Render contribution data as an animated, self-contained SVG heatmap."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL, GAP, STEP = 12, 3, 15
PAD, LABEL_W, LABEL_H, TITLE_H = 22, 30, 20, 42
BG, BG_TOP, FRAME = "#0a0e14", "#0d1420", "#1f6feb"
MUTED, TEXT, ACCENT, GREEN, GOLD = "#7d8590", "#e6edf3", "#22d3ee", "#39d353", "#f2cc60"


def level_for(count: int) -> int:
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 10:
        return 3
    if count <= 20:
        return 4
    return 5


def build_grid(days: list[dict]) -> list[list[dict | None]]:
    first = dt.date.fromisoformat(days[0]["date"])
    column: list[dict | None] = [None] * ((first.weekday() + 1) % 7)
    grid = []
    for day in days:
        weekday = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7
        while len(column) < weekday:
            column.append(None)
        column.append(day)
        if len(column) == 7:
            grid.append(column)
            column = []
    if column:
        grid.append(column + [None] * (7 - len(column)))
    return grid[-53:]


def render(data: dict) -> str:
    static = bool(os.environ.get("STATIC"))
    grid = build_grid(data["days"])
    width = PAD + LABEL_W + len(grid) * STEP + PAD
    grid_top = TITLE_H + LABEL_H
    grid_left = PAD + LABEL_W
    grid_height = 7 * STEP
    height = grid_top + grid_height + 116
    css = "" if static else """
@keyframes reveal { from { opacity: 0; transform: translateY(-7px); } to { opacity: 1; transform: translateY(0); } }
.cell { opacity: 0; animation: reveal .42s cubic-bezier(.2,.8,.2,1) both; }
"""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="14" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="none" stroke="{FRAME}" stroke-opacity=".55"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{width}" y2="{TITLE_H}" stroke="{FRAME}" stroke-opacity=".35"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + 18 * index}" cy="21" r="6" fill="{color}"/>')
    parts.append(
        f'<text x="{width / 2}" y="26" fill="{MUTED}" font-size="14" text-anchor="middle">'
        'steven@github: ~/contributions --graph</text>'
    )

    seen_months = set()
    for column_index, column in enumerate(grid):
        first_day = next((day for day in column if day), None)
        if not first_day:
            continue
        date = dt.date.fromisoformat(first_day["date"])
        month = (date.year, date.month)
        if month not in seen_months and date.day <= 7:
            seen_months.add(month)
            parts.append(
                f'<text x="{grid_left + column_index * STEP}" y="{TITLE_H + 14}" fill="{MUTED}" font-size="10">{date:%b}</text>'
            )

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{PAD}" y="{grid_top + row * STEP + 9}" fill="{MUTED}" font-size="9">{name}</text>'
        )

    for column_index, column in enumerate(grid):
        for row_index, day in enumerate(column):
            if not day:
                continue
            x = grid_left + column_index * STEP
            y = grid_top + row_index * STEP
            level = level_for(day["count"])
            delay = column_index * 0.018 + row_index * 0.045
            animation = "" if static else f' style="animation-delay:{delay:.3f}s"'
            noun = "contribution" if day["count"] == 1 else "contributions"
            title = html.escape(f'{day["date"]}: {day["count"]} {noun}')
            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[level]}"{animation}>'
                f'<title>{title}</title></rect>'
            )

    legend_y = grid_top + grid_height + 5
    legend_x = width - PAD - 105
    parts.append(f'<text x="{legend_x}" y="{legend_y + 10}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    cursor = legend_x + 8
    for color in PALETTE:
        parts.append(f'<rect x="{cursor}" y="{legend_y}" width="11" height="11" rx="2" fill="{color}"/>')
        cursor += 13
    parts.append(f'<text x="{cursor + 3}" y="{legend_y + 10}" fill="{MUTED}" font-size="10">More</text>')

    separator_y = legend_y + 28
    stats_y = separator_y + 27
    parts.append(f'<line x1="0" y1="{separator_y}" x2="{width}" y2="{separator_y}" stroke="{FRAME}" stroke-opacity=".25"/>')
    parts.append(
        f'<text x="{PAD}" y="{stats_y}" font-size="13" fill="{GREEN}"><tspan font-weight="700">{data["total_contributions"]:,}</tspan>'
        f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>'
    )
    parts.append(
        f'<text x="{width - PAD}" y="{stats_y}" font-size="12" fill="{MUTED}" text-anchor="end">'
        f'{data["range"]["start"]} &#8594; {data["range"]["end"]}</text>'
    )
    stats_y += 26
    parts.append(
        f'<text x="{PAD}" y="{stats_y}" font-size="13" fill="{MUTED}">current streak '
        f'<tspan fill="{ACCENT}" font-weight="700">{data["current_streak"]["length"]} days</tspan>'
        f'<tspan>  &#183;  longest </tspan><tspan fill="{ACCENT}" font-weight="700">{data["longest_streak"]["length"]} days</tspan></text>'
    )
    parts.append(
        f'<text x="{width - PAD}" y="{stats_y}" font-size="12" fill="{MUTED}" text-anchor="end">best day '
        f'<tspan fill="{GOLD}" font-weight="700">{data["best_day"]["count"]}</tspan> on {data["best_day"]["date"]}</text>'
    )
    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    OUTPUT.write_text(render(data), encoding="utf-8")
    print(f"wrote {OUTPUT}")
