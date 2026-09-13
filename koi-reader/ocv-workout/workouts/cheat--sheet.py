import os
import time
import functools
import cv2
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple, Dict

# ==========================================
# 1. PYTHONIC MASTERY: PERFORMANCE DECORATOR
# ==========================================
def time_profile(func):
    """Decorator to measure and print execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds to execute.")
        return result
    return wrapper

# ==========================================
# 2. CORE IMAGE PROCESSING (RUNS ON A CORE)
# ==========================================
def process_single_frame(task_data: Dict) -> bool:
    """
    Processes a single image: draws rectangles, crops, and saves.
    Using a single dict argument makes it easily compatible with ProcessPoolExecutor.
    """
    image_path: str = task_data["image_path"]
    output_dir: str = task_data["output_dir"]
    crop_dir: str = task_data["crop_dir"]
    
    # Coordinates format: (x_min, y_min, x_max, y_max)
    coords: Tuple[int, int, int, int] = task_data["coords"]
    label: str = task_data["label"]
    
    # Defensive programming: Check if file exists (Context/Error handling)
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} not found.")
        return False
        
    try:
        # Read image into a NumPy array
        img: np.ndarray = cv2.imread(image_path)
        if img is None:
            return False
            
        x1, y1, x2, y2 = coords
        
        # --- OPENCV SLICING (CROP) ---
        # Note: NumPy arrays are indexed as [rows, cols] which means [y, x]
        cropped_img = img[y1:y2, x1:x2]
        
        # Save crop if it's valid
        if cropped_img.size > 0:
            crop_filename = f"crop_{os.path.basename(image_path)}"
            cv2.imwrite(os.path.join(crop_dir, crop_filename), cropped_img)
        
        # --- OPENCV GEOMETRY (DRAW RECTANGLE) ---
        # Determine color based on label (BGR format)
        color: Tuple[int, int, int] = (0, 255, 0) if label == "Person" else (0, 0, 255)
        thickness: int = 2
        
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        
        # Add Text Label
        cv2.putText(
            img, label, (x1, max(y1 - 10, 20)), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )
        
        # Save annotated image
        output_filename = f"annotated_{os.path.basename(image_path)}"
        cv2.imwrite(os.path.join(output_dir, output_filename), img)
        return True
        
    except Exception as e:
        print(f"Failed to process {image_path}: {e}")
        return False

# ==========================================
# 3. CONCURRENCY ENGINE (BYPASSING THE GIL)
# ==========================================
@time_profile
def parallel_image_pipeline(tasks: List[Dict]) -> None:
    """Distributes image processing tasks across multiple CPU cores."""
    # os.cpu_count() grabs all available cores on your laptop
    num_workers = os.cpu_count()
    print("Spawning {num_workers} parallel workers for processing...")
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # map handles passing the list of dicts to the function asynchronously
        results = executor.map(process_single_frame, tasks)
        
    success_count = sum(1 for r in results if r)
    print(f"Processed {success_count}/{len(tasks)} images successfully.")

# ==========================================
# 4. MOCK EXECUTION BLOCK
# ==========================================
if __name__ == "__main__":
    # Setup dummy directory structure for testing
    os.makedirs("frames", exist_ok=True)
    os.makedirs("output_frames", exist_ok=True)
    os.makedirs("crops", exist_ok=True)
    
    # Create a solid black test image using NumPy if it doesn't exist
    test_img_path = "frames/frame_001.jpg"
    if not os.path.exists(test_img_path):
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.imwrite(test_img_path, dummy_img)
    
    # Mock task payload (In the test, you'd populate this by parsing a CSV/JSON)
    mock_tasks = [
        {
            "image_path": test_img_path,
            "output_dir": "output_frames",
            "crop_dir": "crops",
            "coords": (100, 100, 300, 400), # x1, y1, x2, y2
            "label": "Person"
        }
    ] * 10  # Simulating 10 image tasks
    
    # Kick off the pipeline
    parallel_image_pipeline(mock_tasks)

