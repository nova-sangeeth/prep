"""
detector.py — pure detection logic, zero I/O.

Why a separate module?
  Stage 1/2 mixed detection with camera + window code. That can't scale.
  Real architecture separates the ALGORITHM (pure, testable, reusable)
  from the TRANSPORT (camera, HTTP, queue). This file is the algorithm.

It takes raw image bytes -> returns a plain dict. No OpenCV windows, no
network. That makes it trivial to call from an API, a worker, or a test.
"""

from __future__ import annotations

from typing import TypedDict

import cv2
import numpy as np

# Detection knobs (same meaning as Stage 2).
MIN_AREA = 800
DEFECT_AREA = 4000
LOWER = np.array([100, 80, 50])    # blue-ish, HSV
UPPER = np.array([130, 255, 255])


class Box(TypedDict):
    x: int
    y: int
    w: int
    h: int
    area: float
    status: str  # "good" | "defect"


class Result(TypedDict):
    count: int
    defects: int
    boxes: list[Box]


def detect_bytes(data: bytes) -> Result:
    """Decode raw image bytes and run the detection pipeline.

    Raises ValueError if the bytes are not a decodable image.
    """
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes")
    return detect(img)


def detect(img: np.ndarray) -> Result:
    """Core pipeline: HSV filter -> clean -> contours -> classify."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER, UPPER)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
    )

    boxes: list[Box] = []
    defects = 0
    for c in contours:
        area = float(cv2.contourArea(c))
        if area < MIN_AREA:
            continue
        x, y, w, h = cv2.boundingRect(c)
        is_good = area >= DEFECT_AREA
        if not is_good:
            defects += 1
        boxes.append(Box(x=x, y=y, w=w, h=h, area=area,
                         status="good" if is_good else "defect"))

    return Result(count=len(boxes), defects=defects, boxes=boxes)
