"""
OpenCV : Workout : Test 1
==========================
This module contains the practice session code for learning OpenCV.
"""

__author__ = "novasangeeth@gmail.com"

import cv2
import logging
from pathlib import Path
import numpy as np
from PIL import Image

# Initiate Logger.
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Base file path.
base_dir: Path = Path.cwd()
data_dir: Path = Path(base_dir, "data")


def view_img(image: cv2.Mat, wait_duration: int = 0) -> None:
    """
    Function to view the images.

    :param image: The image matrix.
    :param wait_duration: The window wait duration.

    :return: None
    """

    cv2.imshow(winname="Show Image", mat=image)
    cv2.waitKey(delay=wait_duration)
    cv2.destroyAllWindows()


def crop_img(image: cv2.Mat, wait_duration: int = 0) -> None:
    """
    Function to crop the image.

    :param image: The image matrix.
    :param wait_duration: The window wait duration.

    :return: None
    """
    # Crop the image [y1:y2, x1:x2]
    cropped_img = image[120:150, 150:170]
    cv2.imshow(winname="Cropped Image", mat=cropped_img)
    cv2.waitKey(delay=wait_duration)
    cv2.destroyAllWindows()


def resize_img(image: cv2.Mat, height: int = 100, width: int = 100, wait_duration: int = 0) -> None:
    """
    Function to resize the image.

    :param image: The image matrix.
    :param wait_duration: The window wait duration.

    :return: None
    """
    # Construct the diemension.
    diemensions = (height, width)
    # Resize the image.
    resized_image = cv2.resize(src=image, dsize=diemensions, interpolation=cv2.INTER_LINEAR)
    cv2.imshow(winname="Resized Image", mat=resized_image)
    cv2.waitKey(delay=wait_duration)
    cv2.destroyAllWindows()


def face_identifier(image: cv2.Mat, wait_duration: int = 0) -> None:
    """
    Function to bound the image.

    :param image: The image matrix.
    :param wait_duration: The wait duration

    :return: None
    """
    face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    face = face_classifier.detectMultiScale(image=image, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    for x, y, width, height in face:
        # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 4)
        cv2.rectangle(img=image, pt1=(x, y), pt2=(x + width, y + height), color=(0, 233, 255), thickness=2)
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


LOGGER.info("Show the working directories")
LOGGER.info("Show the Base Directory")
LOGGER.info(base_dir)
LOGGER.info("Show the Data Directory")
LOGGER.info(data_dir)

for filename in data_dir.iterdir():
    LOGGER.info(filename)
    # Read the image file.
    image = cv2.imread(filename=filename)
    face_identifier(image=image)
    view_img(image=image, wait_duration=0)
    # break
    # crop_img(image=image)
    # resize_img(image=image, height=400, width=400)
