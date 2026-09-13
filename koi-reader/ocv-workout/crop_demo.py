"""
crop_demo.py — read an image, crop tiles with NumPy slicing, and "upload"
(save) each tile concurrently with a thread pool.

Concepts shown:
  * cv2.imread  -> load image into a NumPy array (H, W, 3) in BGR order
  * NumPy slice -> img[y1:y2, x1:x2] crops with ZERO copy of pixel math
  * ThreadPool  -> tiles saved in parallel. Saving is I/O-bound (disk),
                   so the GIL is released during the write -> threads win
                   here (unlike CPU work, which needs processes).
  * cv2.imwrite -> encode + write the crop to disk

Usage:
    python crop_demo.py input.jpg
    python crop_demo.py input.jpg out_dir 3   # 3x3 grid of tiles
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np


def save_tile(path: str, tile: np.ndarray) -> str:
    """'Upload' = encode + write one tile to disk. I/O-bound work."""
    ok = cv2.imwrite(path, tile)
    if not ok:
        raise IOError(f"Failed to write {path}")
    return path


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python crop_demo.py <image> [out_dir] [grid]")
        sys.exit(1)

    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "tiles"
    grid = int(sys.argv[3]) if len(sys.argv) > 3 else 2  # grid x grid tiles

    # 1. Load. imread returns None (no exception) if the path is bad.
    img = cv2.imread(src)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {src}")
    h, w = img.shape[:2]
    print(f"loaded {src}  ({w}x{h})")

    os.makedirs(out_dir, exist_ok=True)

    # 2. Crop tiles with NumPy slicing: img[y1:y2, x1:x2].
    #    A slice is a VIEW, not a copy — fast and memory-cheap.
    tile_h, tile_w = h // grid, w // grid
    jobs: list[tuple[str, np.ndarray]] = []
    for row in range(grid):
        for col in range(grid):
            y1, x1 = row * tile_h, col * tile_w
            # last row/col grabs the remainder so we don't drop edge px
            y2 = (row + 1) * tile_h if row < grid - 1 else h
            x2 = (col + 1) * tile_w if col < grid - 1 else w
            tile = img[y1:y2, x1:x2]            # <-- the crop
            path = os.path.join(out_dir, f"tile_{row}_{col}.png")
            jobs.append((path, tile))

    # 3. Save all tiles concurrently via thread pool.
    with ThreadPoolExecutor(max_workers=min(8, len(jobs))) as ex:
        futures = [ex.submit(save_tile, p, t) for p, t in jobs]
        for f in as_completed(futures):
            print("saved", f.result())

    print(f"done: {len(jobs)} tiles -> {out_dir}/")


if __name__ == "__main__":
    main()
