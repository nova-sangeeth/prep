"""
This module contains the image processor based on OpenCV
"""

__author__ = "novasangeeth@gmail.com"


import cv2
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)


def view_img(img_fp: Path) -> None:
    """
    View the image in a window.

    :param img_fp: The image file path.

    :return: None
    """
    try:
        if img_fp.is_file():
            LOGGER.info(f"Reading the image file from path: {img_fp}")
            raise Exception("Image path not a valid file.")

        image = cv2.imread(filename=img_fp)
        if image:
            cv2.imshow(winname="Image Window.", mat=image)
            cv2.waitKey(delay=0)
            cv2.destroyAllWindows()

    except:
        LOGGER.info("Error while processing the file.")
        raise Exception("Error while processing the image")
