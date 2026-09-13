"""
Stage 2: Color Detection + Classification + Tracking
----------------------------------------------------
Builds on Stage 1. Three new ideas:

  1. HSV color filtering  -> detect objects by COLOR, not just shape.
  2. Good/bad classify    -> a "defect" rule (here: object too small).
  3. Centroid tracking    -> give each object an ID so we count each
                             object ONCE even as it moves across frames.

Why HSV instead of BGR?
  HSV separates color (Hue) from brightness. A "blue" object stays blue
  in shadow or glare, so color filtering is far more robust than RGB.

Why tracking?
  In Stage 1 the count jumped every frame. Real conveyor counting needs
  "how many UNIQUE parts passed", not "how many blobs this frame".

Run:
    python stage2_tracker.py

Controls:
    q = quit
    t = toggle the mask debug window
"""

import math

import cv2
import numpy as np

# --- Detection knobs ---------------------------------------------------
MIN_AREA = 800          # ignore blobs smaller than this (noise)
DEFECT_AREA = 4000      # object smaller than this = "bad" (defect rule)

# HSV range for the color you want to track. These defaults catch BLUE.
# Hue in OpenCV is 0-179 (not 0-359). Tune for your object's color.
LOWER = np.array([100, 80, 50])
UPPER = np.array([130, 255, 255])

# --- Tracking knobs ----------------------------------------------------
MAX_MATCH_DIST = 60     # px: a detection within this of a known track
                        # is treated as the SAME object (else it's new)
MAX_MISSING = 15        # frames a track survives unseen before deleted


class CentroidTracker:
    """Minimal nearest-neighbor tracker.

    Each frame we get a list of (cx, cy) centroids. We match them to
    existing tracks by closest distance. Unmatched detections become new
    tracks with a fresh ID. Tracks not seen for a while are dropped.
    """

    def __init__(self) -> None:
        self.next_id = 0
        self.tracks: dict[int, dict] = {}  # id -> {pos, missing}

    def update(self, centroids: list[tuple[int, int]]) -> dict[int, tuple[int, int]]:
        # No known tracks yet -> every centroid is a new object.
        if not self.tracks:
            for c in centroids:
                self._register(c)
            return self._positions()

        track_ids = list(self.tracks.keys())
        track_pts = [self.tracks[i]["pos"] for i in track_ids]
        unmatched = set(range(len(centroids)))

        # Greedy match: for each existing track, grab nearest detection.
        for ti, tid in enumerate(track_ids):
            best_j, best_d = None, MAX_MATCH_DIST + 1
            for j in unmatched:
                d = math.dist(track_pts[ti], centroids[j])
                if d < best_d:
                    best_d, best_j = d, j
            if best_j is not None and best_d <= MAX_MATCH_DIST:
                self.tracks[tid]["pos"] = centroids[best_j]
                self.tracks[tid]["missing"] = 0
                unmatched.discard(best_j)
            else:
                self.tracks[tid]["missing"] += 1

        # Leftover detections = brand new objects.
        for j in unmatched:
            self._register(centroids[j])

        # Drop stale tracks (object left the frame).
        for tid in [t for t, v in self.tracks.items() if v["missing"] > MAX_MISSING]:
            del self.tracks[tid]

        return self._positions()

    def _register(self, pos: tuple[int, int]) -> None:
        self.tracks[self.next_id] = {"pos": pos, "missing": 0}
        self.next_id += 1

    def _positions(self) -> dict[int, tuple[int, int]]:
        return {tid: v["pos"] for tid, v in self.tracks.items()}


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera. Is another app using it?")

    tracker = CentroidTracker()
    show_mask = False

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # 1. BGR -> HSV, then keep only pixels inside the color range.
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, LOWER, UPPER)

        # 2. Clean the mask: open removes specks, close fills holes.
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 3. Contours of the colored blobs.
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
        )

        centroids: list[tuple[int, int]] = []
        boxes: list[tuple[int, int, int, int, bool]] = []  # x,y,w,h,is_good
        for c in contours:
            area = cv2.contourArea(c)
            if area < MIN_AREA:
                continue
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w // 2, y + h // 2
            centroids.append((cx, cy))
            is_good = area >= DEFECT_AREA      # classify: big enough = good
            boxes.append((x, y, w, h, is_good))

        # 4. Tracking: convert this frame's centroids into stable IDs.
        positions = tracker.update(centroids)

        # 5. Draw boxes (green = good, red = defect).
        for (x, y, w, h, is_good) in boxes:
            color = (0, 255, 0) if is_good else (0, 0, 255)
            label = "good" if is_good else "DEFECT"
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label, (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw the tracking ID near each tracked centroid.
        for tid, (cx, cy) in positions.items():
            cv2.circle(frame, (cx, cy), 4, (255, 255, 0), -1)
            cv2.putText(frame, f"#{tid}", (cx + 6, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        # next_id == total unique objects ever seen.
        cv2.putText(frame, f"Total unique: {tracker.next_id}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, f"On screen: {len(boxes)}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        cv2.imshow("Stage 2 - Track + Classify", frame)
        if show_mask:
            cv2.imshow("mask (debug)", mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("t"):
            show_mask = not show_mask
            if not show_mask:
                cv2.destroyWindow("mask (debug)")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
