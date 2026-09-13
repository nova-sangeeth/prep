"""
Koireader - Assignment - Dummy Image Generation
==================================================
This module contains the code to generate images using OpenCV.
"""

__author__ = "novasangeeth@gmail.com"

import logging
from pathlib import Path
import numpy as np
import cv2

#: Configure the Logger
logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)

#: File directory path
INPUT_DIR = "input"

#: Constants
NUM_OF_FILES: int = 500
HEIGHT: int = 1024
WIDTH: int = 1024


def create_dummy_image(height: int, width: int) -> np.ndarray:
    """
    Create dummy image.

    :param height: The height of the image.
    :param width: The width of the image.

    :return: A numpy array.
    """

    image = np.random.randint(low=0, high=255, size=(width, height, 1))

    return image


def write_dummy_image(filepath: str, image: np.ndarray) -> None:
    """
    Write dummy image.

    :param filepath: The filepath for the generated image.
    :return: None
    """
    cv2.imwrite(filename=filepath, img=image)

    return


def main():
    """
    Generate Dummy images and save the files in the input directory.
    """

    # Create a new dir if it doesn't exist.
    Path(INPUT_DIR).mkdir(exist_ok=True)
    
    for i in range(1, NUM_OF_FILES + 1):
        image: np.ndarray = create_dummy_image(height=HEIGHT, width=WIDTH)
        # Construct the file path
        img_path = f"{INPUT_DIR}/{i}.png"

        LOGGER.info(img_path)
        # Write the images
        write_dummy_image(filepath=img_path, image=image)


if __name__ == "__main__":
    main()
