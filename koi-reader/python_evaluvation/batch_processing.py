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
import time

#: Configure the Logger
logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)

# Create a file handler that saves to a .csv file
file_handler = logging.FileHandler("report.csv")

# Define a CSV-style formatter (comma-separated)
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,"%(message)s"')
file_handler.setFormatter(formatter)

LOGGER.addHandler(file_handler)

#: File directory path
INPUT_DIR = "input"
OUTPUT_DIR = "output"

#: Constants
DIEMENSIONS: Tuple[int] = (640, 640)
NUM_OF_WORKERS: int = 3


def resize_image(input_path: str, output_path: str) -> None:
    """
    Resize Image.

    :param image: A numpy array.
    :param input_path: The filepath of the input image.
    :param output_path: The filepath of the output image.

    :return: None
    """
    image = cv2.imread(filename=input_path)
    resized_image = cv2.resize(image, dsize=DIEMENSIONS)
    cv2.imwrite(filename=output_path, img=resized_image)
    return


def run_batch():
    """
    Resize images and save the files in the output directory.
    """

    # Create a new dir if it doesn't exist.
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    input_paths = list(Path(INPUT_DIR).iterdir())
    output_paths = []

    # Construct Output paths
    for i in input_paths:
        path = f"{OUTPUT_DIR}/{i.name}"
        output_paths.append(path)

    # max_workers defaults to min(32, os.cpu_count() + 4) in recent Python versions
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Option 1: Map (returns results in order)
        executor.map(resize_image, input_paths, output_paths)
        queue_size = executor._work_queue.qsize()
        thread_count = len(executor._threads)
        max_workers = executor._max_workers
        
        LOGGER.info(f"Number of images: {queue_size}")
        LOGGER.info(f"Number of Threads: {thread_count}")
        LOGGER.info(f"Number of Workers: {max_workers}")

def main():
    start_time = time.perf_counter()

    # Call your function
    run_batch()

    end_time = time.perf_counter()
    duration_in_seconds = end_time - start_time
    duration_in_milli_seconds = duration_in_seconds * 1000
    LOGGER.info(
        f"Execution time: {duration_in_seconds:.4f} seconds {duration_in_milli_seconds:.2f} milli seconds"
    )


if __name__ == "__main__":
    main()
