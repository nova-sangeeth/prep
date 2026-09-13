from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np


def crop_image(
    image: np.ndarray,
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
) -> np.ndarray:
    """
    Crop an image using NumPy slicing.

    Args:
        image: Source OpenCV image.
        top_left: (x1, y1) coordinates.
        bottom_right: (x2, y2) coordinates.

    Returns:
        Cropped image.
    """
    x1, y1 = top_left
    x2, y2 = bottom_right

    return image[y1:y2, x1:x2]


def save_image(output_path: Path, image: np.ndarray) -> None:
    """
    Save an image to disk.

    Args:
        output_path: Destination path.
        image: Image to save.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    success = cv2.imwrite(str(output_path), image)

    if not success:
        raise RuntimeError(f"Failed to save image: {output_path}")

    print(f"Saved: {output_path}")


def main() -> None:
    input_path = Path("/home/nova/work/ocv-workout/workouts/data/wallhaven-o5mr25.png")
    output_path = Path("output/cropped.png")

    image = cv2.imread(str(input_path))

    if image is None:
        raise FileNotFoundError(f"Could not read image: {input_path}")

    cropped = crop_image(image=image, top_left=(100, 100), bottom_right=(400, 400))

    # Simulate async upload/save work
    with ThreadPoolExecutor(max_workers=2) as executor:
        future = executor.submit(save_image, output_path, cropped)
        future.result()


if __name__ == "__main__":
    main()
