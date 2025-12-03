import cv2
from ultralytics import YOLO
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import threading
from collections import deque, OrderedDict
import queue
import numpy as np
import os
import sys
import django
import hashlib
from PIL import Image
from datetime import timedelta
import math
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SRAS_Project.settings')
django.setup()

# Import Django models after setup
from SRAS_App.models import Violation, Camera
from django.utils import timezone

# Load both models
custom_model = YOLO("customyolov8n.pt")  # your custom model with "no helmet", "plate_*", etc
pretrained_model = YOLO("yolov8n.pt")    # base model for person/motorcycle
cap = cv2.VideoCapture("http://192.168.1.5:8080/video")  # Your IP camera

# Configuration for smoother streaming
TARGET_FPS = 30
FRAME_INTERVAL = 1.0 / TARGET_FPS
SKIP_INFERENCE = 1  # Run YOLO every N frames
BUFFER_SIZE = 10     # Number of frames to buffer
JPEG_QUALITY = 100   # JPEG encode quality
DETECTION_RESIZE = (640, 360)  # Resize for detection (w, h)

# Duplicate detection settings
NO_HELMET_IOU_THRESH = 0.7
TIME_WINDOW = 300   # seconds (5 minutes)
SPATIAL_WINDOW = 60 # frames

# Speed detection settings
MIN_SPEED_KPH = 2.0  # Minimum speed in km/h to capture violation (ignore stationary riders)
PIXELS_PER_METER = 20  # Calibration: approximate pixels per meter (adjust based on camera)
SPEED_SMOOTHING_FRAMES = 1  # Number of frames to average speed over


# Camera check
if not cap.isOpened():
    print("❌ Error: Camera feed could not be opened. Check your camera URL and network connection.")
else:
    print("✅ Camera feed opened successfully.")

# Globals
annotated_frame = None
inference_lock = threading.Lock()
stop_inference = False
frame_queue = queue.Queue(maxsize=5)
recent_no_helmet = deque(maxlen=100)

# In-memory hash tracking for faster duplicate detection
recent_hashes = set()
hash_lock = threading.Lock()

# Speed tracking: {rider_id: deque of (frame_idx, center_x, center_y, timestamp)}
rider_tracks = {}
track_lock = threading.Lock()
next_rider_id = 0


def get_default_camera():
    try:
        camera, _ = Camera.objects.get_or_create(
            name="Default Camera",
            defaults={'stream_url': "http://192.168.1.5:8080/video"}
        )
        return camera
    except Exception as e:
        print(f"Error getting camera: {e}")
        return None


def create_rider_hash(rider_crop, plate_number=None):
    try:
        resized = cv2.resize(rider_crop, (32, 32))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        image_hash = hashlib.md5(blurred.tobytes()).hexdigest()
        if plate_number and plate_number.strip():
            combined = f"{image_hash}_{plate_number.strip()}"
            return hashlib.md5(combined.encode()).hexdigest()
        return image_hash
    except Exception as e:
        print(f"Error creating rider hash: {e}")
        return None


def is_duplicate_violation(rider_hash, time_window_seconds=TIME_WINDOW):
    if not rider_hash:
        return False
    try:
        with hash_lock:
            if rider_hash in recent_hashes:
                print(f"⚠️ Duplicate (memory): {rider_hash[:8]}...")
                return True
        recent_time = timezone.now() - timedelta(seconds=time_window_seconds)
        exists = Violation.objects.filter(rider_hash=rider_hash, timestamp__gte=recent_time).exists()
        if exists:
            print(f"⚠️ Duplicate (database): {rider_hash[:8]}...")
            with hash_lock:
                recent_hashes.add(rider_hash)
            return True
        return False
    except Exception as e:
        print(f"Error checking duplicate violation: {e}")
        return False


def cleanup_old_hashes():
    try:
        cutoff_time = timezone.now() - timedelta(minutes=10)
        old_hashes = Violation.objects.filter(timestamp__lt=cutoff_time).values_list('rider_hash', flat=True)
        with hash_lock:
            for h in old_hashes:
                if h in recent_hashes:
                    recent_hashes.remove(h)
    except Exception as e:
        print(f"Error cleaning up old hashes: {e}")


def save_violation_to_db(image_data, plate_number=None, rider_hash=None, plate_image_data=None):
    """Save violation with annotated frame + optional cropped plate bytes."""
    try:
        camera = get_default_camera()
        if camera is None:
            print("No camera available for violation recording")
            return False

        if rider_hash and is_duplicate_violation(rider_hash):
            print(f"[LOG] Duplicate violation detected for hash: {rider_hash}")
            return False

        violation = Violation.objects.create(
            camera=camera,
            plate_number=plate_number,
            image=image_data,
            plate_image=plate_image_data,  # NEW
            rider_hash=rider_hash,
            timestamp=timezone.now()
        )

        if rider_hash:
            with hash_lock:
                recent_hashes.add(rider_hash)

        print(f"✅ Violation saved: {violation.id} @ {violation.timestamp}")
        return True
    except Exception as e:
        print(f"❌ Error saving violation to database: {e}")
        return False


def frame_capture_worker():
    while not stop_inference:
        success, frame = cap.read()
        if not success:
            time.sleep(0.01)
            continue
        # keep only latest
        while not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                break
        frame_queue.put(frame)
        time.sleep(0.001)


def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    unionArea = boxAArea + boxBArea - interArea
    return interArea / unionArea if unionArea > 0 else 0.0


def calculate_speed_kph(track_history, fps=TARGET_FPS):
    """
    Calculate speed in km/h based on position history.
    
    Args:
        track_history: deque of (frame_idx, center_x, center_y, timestamp)
        fps: frames per second
    
    Returns:
        speed in km/h, or 0 if insufficient data
    """
    if len(track_history) < 2:
        return 0.0
    
    # Get first and last positions
    first_frame, first_x, first_y, first_time = track_history[0]
    last_frame, last_x, last_y, last_time = track_history[-1]
    
    # Calculate pixel distance
    pixel_distance = math.sqrt((last_x - first_x)**2 + (last_y - first_y)**2)
    
    # Convert to meters
    distance_meters = pixel_distance / PIXELS_PER_METER
    
    # Calculate time difference in seconds
    time_diff = (last_time - first_time).total_seconds()
    
    if time_diff <= 0:
        return 0.0
    
    # Calculate speed in m/s, then convert to km/h
    speed_ms = distance_meters / time_diff
    speed_kph = speed_ms * 3.6  # Convert m/s to km/h
    
    return speed_kph


def match_rider_to_track(box, frame_idx):
    """
    Match a detected rider box to an existing track or create new track.
    
    Args:
        box: (x1, y1, x2, y2) bounding box
        frame_idx: current frame index
    
    Returns:
        rider_id: ID of matched or new track
    """
    global next_rider_id
    
    x1, y1, x2, y2 = box
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    current_time = timezone.now()
    
    with track_lock:
        # Try to match with existing tracks
        best_match_id = None
        best_distance = float('inf')
        max_distance = 100  # Maximum pixel distance to consider same rider
        
        for rider_id, track in list(rider_tracks.items()):
            if len(track) == 0:
                continue
            
            # Get last known position
            last_frame, last_x, last_y, last_time = track[-1]
            
            # Remove old tracks (not seen in last 30 frames)
            if frame_idx - last_frame > 30:
                del rider_tracks[rider_id]
                continue
            
            # Calculate distance
            distance = math.sqrt((center_x - last_x)**2 + (center_y - last_y)**2)
            
            if distance < max_distance and distance < best_distance:
                best_distance = distance
                best_match_id = rider_id
        
        # If matched, update existing track
        if best_match_id is not None:
            rider_tracks[best_match_id].append((frame_idx, center_x, center_y, current_time))
            return best_match_id
        
        # Create new track
        new_id = next_rider_id
        next_rider_id += 1
        rider_tracks[new_id] = deque(maxlen=SPEED_SMOOTHING_FRAMES)
        rider_tracks[new_id].append((frame_idx, center_x, center_y, current_time))
        return new_id


def inference_worker():
    global annotated_frame
    local_frame_count = 0
    last_cleanup = time.time()

    while not stop_inference:
        try:
            frame = frame_queue.get(timeout=0.1)
            local_frame_count += 1

            if time.time() - last_cleanup > 300:
                cleanup_old_hashes()
                last_cleanup = time.time()

            if local_frame_count % SKIP_INFERENCE != 0:
                with inference_lock:
                    if annotated_frame is not None:
                        annotated_frame = annotated_frame.copy()
                continue

            det_frame = cv2.resize(frame, DETECTION_RESIZE)
            scale_x = frame.shape[1] / DETECTION_RESIZE[0]
            scale_y = frame.shape[0] / DETECTION_RESIZE[1]

            results = pretrained_model(det_frame, conf=0.4)[0]
            persons, motorcycles = [], []
            for box in results.boxes:
                label = pretrained_model.names[int(box.cls[0])]
                if label == "person":
                    persons.append(box)
                elif label == "motorcycle":
                    motorcycles.append(box)

            riders = []
            for person in persons:
                px1, py1, px2, py2 = map(int, person.xyxy[0])
                for moto in motorcycles:
                    mx1, my1, mx2, my2 = map(int, moto.xyxy[0])
                    ix1 = max(px1, mx1)
                    iy1 = max(py1, my1)
                    ix2 = min(px2, mx2)
                    iy2 = min(py2, my2)
                    iw = max(0, ix2 - ix1)
                    ih = max(0, iy2 - iy1)
                    inter = iw * ih
                    person_area = (px2 - px1) * (py2 - py1)
                    moto_area = (mx2 - mx1) * (my2 - my1)
                    union = person_area + moto_area - inter
                    iou_val = inter / union if union > 0 else 0
                    if iou_val > 0.1:
                        rx1 = min(px1, mx1)
                        ry1 = min(py1, my1)
                        rx2 = max(px2, mx2)
                        ry2 = max(py2, my2)
                        # upscale to original frame coords
                        rx1, ry1, rx2, ry2 = [
                            int(round(v * scale_x if i % 2 == 0 else v * scale_y))
                            for i, v in enumerate([rx1, ry1, rx2, ry2])
                        ]
                        riders.append(((rx1, ry1, rx2, ry2), person, moto))
                        break

            annotated = frame.copy()

            for (rx1, ry1, rx2, ry2), person, moto in riders:
                # Track rider and calculate speed
                rider_id = match_rider_to_track((rx1, ry1, rx2, ry2), local_frame_count)
                
                with track_lock:
                    track_history = rider_tracks.get(rider_id, deque())
                    speed_kph = calculate_speed_kph(track_history) if len(track_history) >= 2 else 0.0
                
                # Draw rider box with speed
                box_color = (255, 0, 0) if speed_kph >= MIN_SPEED_KPH else (128, 128, 128)
                cv2.rectangle(annotated, (rx1, ry1), (rx2, ry2), box_color, 2)
                
                # Display speed on frame
                speed_text = f"Rider {rider_id}: {speed_kph:.1f} km/h"
                cv2.putText(annotated, speed_text, (rx1, ry1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

                rider_crop = frame[ry1:ry2, rx1:rx2]
                if rider_crop.size == 0:
                    continue

                custom_results = custom_model(rider_crop, conf=0.4)[0]

                found_no_helmet = False
                plate_number = None

                # NEW: keep the best (largest) plate crop
                best_plate_crop = None
                best_area = 0

                for cbox in custom_results.boxes:
                    cx1, cy1, cx2, cy2 = map(int, cbox.xyxy[0])
                    clabel = custom_model.names[int(cbox.cls[0])]

                    color = (0, 255, 0)
                    if "no helmet" in clabel.lower():
                        color = (0, 0, 255)
                        found_no_helmet = True
                    elif "helmet" in clabel.lower():
                        color = (0, 255, 0)
                    elif "plate" in clabel.lower():
                        color = (255, 255, 0)
                        plate_number = clabel.replace("plate_", "").replace("_", "")

                        # guard bounds and crop
                        h, w = rider_crop.shape[:2]
                        px1 = max(0, min(w, cx1))
                        py1 = max(0, min(h, cy1))
                        px2 = max(0, min(w, cx2))
                        py2 = max(0, min(h, cy2))
                        crop = rider_crop[py1:py2, px1:px2]
                        area = max(0, (px2 - px1) * (py2 - py1))
                        if crop.size > 0 and area > best_area and (px2 - px1) >= 12 and (py2 - py1) >= 8:
                            best_area = area
                            best_plate_crop = crop

                    # draw sub-boxes on full frame
                    cv2.rectangle(annotated, (rx1 + cx1, ry1 + cy1), (rx1 + cx2, ry1 + cy2), color, 2)
                    cv2.putText(annotated, clabel, (rx1 + cx1, ry1 + cy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # Only capture violation if rider is moving AND has no helmet
                if found_no_helmet and speed_kph >= MIN_SPEED_KPH:
                    rider_hash = create_rider_hash(rider_crop, plate_number)

                    # spatial duplicate check
                    is_spatial_dup = False
                    for prev_idx, prev_box in recent_no_helmet:
                        if abs(local_frame_count - prev_idx) < SPATIAL_WINDOW and iou((rx1, ry1, rx2, ry2), prev_box) > NO_HELMET_IOU_THRESH:
                            is_spatial_dup = True
                            break

                    if not is_spatial_dup:
                        # Add speed info to the annotated frame
                        speed_info_text = f"Speed: {speed_kph:.1f} km/h"
                        cv2.putText(annotated, speed_info_text, (rx1, ry2 + 25), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        
                        ok_ann, ann_jpg = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                        plate_bytes = None
                        if best_plate_crop is not None:
                            ok_pl, pl_jpg = cv2.imencode('.jpg', best_plate_crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
                            if ok_pl:
                                plate_bytes = pl_jpg.tobytes()

                        if ok_ann:
                            if save_violation_to_db(
                                ann_jpg.tobytes(),
                                plate_number=plate_number,
                                rider_hash=rider_hash,
                                plate_image_data=plate_bytes  # NEW
                            ):
                                recent_no_helmet.append((local_frame_count, (rx1, ry1, rx2, ry2)))
                                print(f"✅ Violation captured: Speed {speed_kph:.1f} km/h, Plate: {plate_number or 'N/A'}")
                        else:
                            print("❌ Failed to encode annotated frame")
                    # else: skip due to spatial duplicate
                elif found_no_helmet and speed_kph < MIN_SPEED_KPH:
                    # Log that violation was skipped due to low speed
                    print(f"⏸️  Stationary rider ignored: Speed {speed_kph:.1f} km/h (min: {MIN_SPEED_KPH} km/h)")

            with inference_lock:
                annotated_frame = annotated

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Inference error: {e}")
            continue


# Start workers
frame_capture_thread = threading.Thread(target=frame_capture_worker, daemon=True)
frame_capture_thread.start()
inference_thread = threading.Thread(target=inference_worker, daemon=True)
inference_thread.start()


class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global annotated_frame

        if self.path != '/video':
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()

        last_frame_time = time.time()

        while True:
            try:
                with inference_lock:
                    output_frame = annotated_frame.copy() if annotated_frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)

                ret, jpeg = cv2.imencode('.jpg', output_frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                if not ret:
                    continue

                self.wfile.write(b"--frame\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.end_headers()
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b"\r\n")

                elapsed = time.time() - last_frame_time
                if elapsed < FRAME_INTERVAL:
                    time.sleep(FRAME_INTERVAL - elapsed)
                last_frame_time = time.time()

            except Exception as e:
                print(f"Stream error: {e}")
                break

    def log_message(self, format, *args):
        pass  # silence


def cleanup():
    global stop_inference
    stop_inference = True
    if inference_thread.is_alive():
        inference_thread.join(timeout=1)
    if frame_capture_thread.is_alive():
        frame_capture_thread.join(timeout=1)
    cap.release()


import atexit
atexit.register(cleanup)

server = HTTPServer(('0.0.0.0', 8081), MJPEGHandler)
print("✅ Smooth MJPEG stream running at http://localhost:8081/video")
print(f"📊 Target FPS: {TARGET_FPS}, Inference every {SKIP_INFERENCE} frames")
print("🗄️  Violations saved as BLOB (annotated + plate crop when available)")
print("🔄 Duplicate detection window: 5 minutes")
print(f"🏍️  Speed detection enabled: Minimum {MIN_SPEED_KPH} km/h to capture")
print(f"📏 Calibration: {PIXELS_PER_METER} pixels/meter (adjust if needed)")
print("⚠️  Stationary riders will be ignored")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Stopping server...")
    cleanup()
    server.shutdown()
