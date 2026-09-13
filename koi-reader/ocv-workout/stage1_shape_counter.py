"""
Stage 1: Shape Counter
----------------------
Goal: open the webcam, find distinct objects (shapes) on a plain
background, draw a box around each one, and show a live count.

This teaches the core OpenCV pipeline you will reuse forever:
    capture -> grayscale -> blur -> threshold -> contours -> draw

Run:
    python stage1_shape_counter.py

Controls:
    q  = quit
    t  = toggle the threshold debug window on/off

Tip: hold up dark objects against a light wall (or light objects
against a dark desk) for the cleanest detection.
"""

import cv2

# --- Tunable knobs (change these and watch what happens) ---------------
MIN_AREA = 800        # ignore tiny blobs (noise). raise if too many boxes.
BLUR_KERNEL = (5, 5)  # bigger = smoother but loses small detail
THRESH_VALUE = 0      # 0 means "let Otsu pick the value automatically"


def main() -> None:
    # 0 = default camera. Use a filename here instead to test on a video.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera. Is another app using it?")

    show_thresh = False

    while True:
        ok, frame = cap.read()
        if not ok:
            break  # camera dropped / video ended

        # 1. Grayscale: color is noise for shape-finding. 1 channel = faster.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 2. Blur: kills speckle noise so threshold edges are clean.
        blur = cv2.GaussianBlur(gray, BLUR_KERNEL, 0)

        # 3. Threshold: split image into black/white (object vs background).
        #    THRESH_OTSU auto-picks the split point from the histogram.
        _, thresh = cv2.threshold(
            blur, THRESH_VALUE, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
        )

        # 4. Contours: outlines of every white blob.
        #    RETR_EXTERNAL = only outer shapes, ignore holes inside them.
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
        )

        # 5. Draw a box + count the ones big enough to be real.
        count = 0
        for c in contours:
            if cv2.contourArea(c) < MIN_AREA:
                continue  # skip noise
            count += 1
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Overlay the live count.
        cv2.putText(
            frame, f"Objects: {count}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2,
        )

        cv2.imshow("Stage 1 - Shape Counter", frame)
        if show_thresh:
            cv2.imshow("threshold (debug)", thresh)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("t"):
            show_thresh = not show_thresh
            if not show_thresh:
                cv2.destroyWindow("threshold (debug)")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
