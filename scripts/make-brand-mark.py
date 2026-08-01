#!/usr/bin/env python3
"""Crop the Phantom Equestrian shield from branding/logo.png (drop wordmark text).

Flood-fills near-black background from the edges to transparent (preserves the
black horse silhouette inside the grey shield) and writes:
  branding/mark.png
  frontend/public/branding/mark.png
"""
from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "branding" / "logo.png"
OUT_BRANDING = ROOT / "branding" / "mark.png"
OUT_PUBLIC = ROOT / "frontend" / "public" / "branding" / "mark.png"

BLACK_LUMA = 18


def is_near_black(r: int, g: int, b: int, a: int) -> bool:
    if a < 200:
        return True
    return (r + g + b) / 3 <= BLACK_LUMA


def flood_transparent(im: Image.Image) -> None:
    """Make near-black pixels reachable from the image edge transparent."""
    w, h = im.size
    px = im.load()
    visited = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def try_enqueue(x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            return
        r, g, b, a = px[x, y]
        if not is_near_black(r, g, b, a):
            return
        visited[y][x] = True
        q.append((x, y))

    for x in range(w):
        try_enqueue(x, 0)
        try_enqueue(x, h - 1)
    for y in range(h):
        try_enqueue(0, y)
        try_enqueue(w - 1, y)

    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            try_enqueue(nx, ny)


def main() -> int:
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    px = im.load()

    def is_content(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        return not is_near_black(r, g, b, a)

    row_counts = [0] * h
    for y in range(h):
        for x in range(w):
            if is_content(x, y):
                row_counts[y] += 1

    gap_start = None
    for y in range(int(h * 0.4), int(h * 0.9)):
        if row_counts[y] < 30:
            gap_start = y
            break
    if gap_start is None:
        raise SystemExit("Could not find shield/wordmark gap")

    min_x, min_y, max_x, max_y = w, h, 0, 0
    for y in range(gap_start):
        for x in range(w):
            if is_content(x, y):
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    pad = 24
    box = (
        max(0, min_x - pad),
        max(0, min_y - pad),
        min(w, max_x + 1 + pad),
        min(h, max_y + 1 + pad),
    )
    cropped = im.crop(box)
    flood_transparent(cropped)

    max_side = 512
    if max(cropped.size) > max_side:
        cropped.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    OUT_BRANDING.parent.mkdir(parents=True, exist_ok=True)
    OUT_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(OUT_BRANDING, "PNG")
    shutil.copy2(OUT_BRANDING, OUT_PUBLIC)
    print(f"Wrote {OUT_BRANDING} and {OUT_PUBLIC} ({cropped.size[0]}x{cropped.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
