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

from SRAS_App.models import Violation, Camera
from django.utils import timezone

# Load both models
custom_model = YOLO("customyolov8n.pt")  # your custom model with "no helmet", "plate_*", etc
pretrained_model = YOLO("yolov8n.pt")    # base model for person/motorcycle
cap = cv2.VideoCapture("rtsp://SRAS_Admin:Admin123@192.168.1.6:554/stream1")  # Your IP camera

# Configuration for smoother streaming
TARGET_FPS = 30
FRAME_INTERVAL = 1.0 / TARGET_FPS
SKIP_INFERENCE = 1  # Run YOLO every N frames
BUFFER_SIZE = 10     # Number of frames to buffer
JPEG_QUALITY = 80   # JPEG encode quality
DETECTION_RESIZE = (640, 360)  # Resize for detection (w, h)

# Duplicate detection settings
NO_HELMET_IOU_THRESH = 0.7
TIME_WINDOW = 300   # seconds (5 minutes)
SPATIAL_WINDOW = 60 # frames


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


def get_default_camera():
    try:
        camera, _ = Camera.objects.get_or_create(
            name="Default Camera",
            defaults={'stream_url': "rtsp://SRAS_Admin:Admin123@192.168.1.6:554/stream1"}
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
                cv2.rectangle(annotated, (rx1, ry1), (rx2, ry2), (255, 0, 0), 2)
                cv2.putText(annotated, "Rider", (rx1, ry1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

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

                if found_no_helmet:
                    rider_hash = create_rider_hash(rider_crop, plate_number)

                    # spatial duplicate check
                    is_spatial_dup = False
                    for prev_idx, prev_box in recent_no_helmet:
                        if abs(local_frame_count - prev_idx) < SPATIAL_WINDOW and iou((rx1, ry1, rx2, ry2), prev_box) > NO_HELMET_IOU_THRESH:
                            is_spatial_dup = True
                            break

                    if not is_spatial_dup:
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
                        else:
                            print("❌ Failed to encode annotated frame")
                    # else: skip due to spatial duplicate

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

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Stopping server...")
    cleanup()
    server.shutdown()
