"""
Koireader - Assignment - Image Resize
======================================
This module contains the code to resize images using OpenCV.
"""

__author__ = "novasangeeth@gmail.com"

import logging
from pathlib import Path
import numpy as np
import cv2
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
import time
import psutil
import os
from functools import wraps

#: Configure the Logger
logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)

# Create a file handler that saves to a .csv file
file_handler = logging.FileHandler("report.csv")

# Define a CSV-style formatter (comma-separated)
# formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,"%(message)s"')
# file_handler.setFormatter(formatter)

LOGGER.addHandler(file_handler)

#: File directory path
INPUT_DIR = "input"
OUTPUT_DIR = "output"
OUTPUT_DIR_PPE = "output_ppe"

#: Constants
DIEMENSIONS: Tuple[int] = (640, 640)
NUM_OF_WORKERS: int = 3



LOGGER.info(f"current_pid,cpu_percentage,duration_in_seconds")


def perf_monitor(func):
    """
    Decorator for performance monitoring.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get current PID
        current_pid = os.getpid()
        # Get the current process
        current_process = psutil.Process(current_pid)
        
        cpu_percentage = current_process.cpu_percent()

        start_time = time.perf_counter()

        result = func(*args, **kwargs)

        end_time = time.perf_counter()
        
        duration_in_seconds = end_time - start_time

        LOGGER.info(f"{current_pid},{cpu_percentage},{duration_in_seconds:.4f}")
        return result

    return wrapper


def resize_image(input_path: str, output_path: str) -> None:
    """
    Resize Image.

    :param image: A numpy array.
    :param input_path: The filepath of the input image.
    :param output_path: The filepath of the output image.

    :return: None
    """
    LOGGER.info(f"resize-image: {input_path}")
    LOGGER.info(f"resize-image: {output_path}")
    image = cv2.imread(filename=input_path)
    resized_image = cv2.resize(image, dsize=DIEMENSIONS)
    cv2.imwrite(filename=output_path, img=resized_image)
    LOGGER.info(f"Wrote the file to the output dir: {output_path}.")
    return

@perf_monitor
def resize_image_2(paths: tuple[str, str]) -> None:
    """
    Resize Image. with Tuple args

    :param paths: The input and output paths as a tuple.

    :return: None
    """
    # Unpack the input and output paths.
    input_path: str = paths[0]
    output_path: str = paths[1]

    image = cv2.imread(filename=input_path)
    resized_image = cv2.resize(image, dsize=DIEMENSIONS)
    cv2.imwrite(filename=output_path, img=resized_image)
    return


def run_ppe_batch() -> None:
    """
    Resize the images and save the fiesl in the output directory
    :: Using ProcessPoolExecutor.
    """
    Path(OUTPUT_DIR_PPE).mkdir(exist_ok=True)
    input_paths: list = list(Path(INPUT_DIR).iterdir())
    output_paths: list[tuple] = []

    # Construct Output paths
    for input_path in input_paths:
        filename = input_path.name
        path = f"{OUTPUT_DIR_PPE}/{filename}"
        # Construct a tuple.
        params = (str(input_path), path)
        output_paths.append(params)

    with ProcessPoolExecutor(max_workers=10) as pp_executor:
        pp_executor.map(resize_image_2, output_paths)


def main():
    # Call your function
    run_ppe_batch()


if __name__ == "__main__":
    main()
