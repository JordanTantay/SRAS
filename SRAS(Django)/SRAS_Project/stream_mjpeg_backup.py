import cv2
from ultralytics import YOLO
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import threading
from collections import deque
import queue
import numpy as np
import os
import sys
import django
import hashlib
import io
from PIL import Image
from datetime import timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SRAS_Project.settings')
django.setup()

# Import Django models after setup
from SRAS_App.models import Violation, Camera
from django.utils import timezone

# Load both models
custom_model = YOLO("customyolov8n.pt")
pretrained_model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture("http://192.168.1.4:8080/video")  # Your IP camera

# Configuration for smoother streaming
TARGET_FPS = 30
FRAME_INTERVAL = 1.0 / TARGET_FPS
SKIP_INFERENCE = 3  # Run YOLO every N frames
BUFFER_SIZE = 5  # Number of frames to buffer
JPEG_QUALITY = 85  # JPEG quality (0-100, lower = faster encoding)
DETECTION_RESIZE = (640, 360)  # Resize for detection (width, height)

# Loosened duplicate detection for testing
NO_HELMET_IOU_THRESH = 0.5  # Lowered threshold for less strict duplicate detection
TIME_WINDOW = 60  # Time window in seconds (1 minute) to check for duplicates
SPATIAL_WINDOW = 10  # Frames to check for spatial duplicates

# Check camera feed at startup
if not cap.isOpened():
    print("❌ Error: Camera feed could not be opened. Check your camera URL and network connection.")
else:
    print("✅ Camera feed opened successfully.")

# Global variables for frame management
frame_buffer = deque(maxlen=BUFFER_SIZE)
annotated_frame = None
frame_count = 0
inference_lock = threading.Lock()
inference_queue = queue.Queue(maxsize=2)
stop_inference = False

# New: Frame capture thread and queue
frame_queue = queue.Queue(maxsize=5)

# Improved duplicate detection
recent_no_helmet = deque(maxlen=100)  # Increased buffer for better duplicate detection
NO_HELMET_IOU_THRESH = 0.7  # Increased threshold for stricter duplicate detection
TIME_WINDOW = 300  # Time window in seconds (5 minutes) to check for duplicates
SPATIAL_WINDOW = 60  # Frames to check for spatial duplicates

# In-memory hash tracking for faster duplicate detection
recent_hashes = set()  # Store recent hashes in memory
hash_lock = threading.Lock()

def get_default_camera():
    try:
        camera, created = Camera.objects.get_or_create(
            name="Default Camera",
            defaults={'stream_url': "http://192.168.1.4:8080/video"}
        )
        return camera
    except Exception as e:
        print(f"Error getting camera: {e}")
        return None

def create_rider_hash(rider_crop, plate_number=None):
    """Create a unique hash for the rider to prevent duplicate counting"""
    try:
        # Resize for consistent hashing (smaller size for better performance)
        resized = cv2.resize(rider_crop, (32, 32))
        # Convert to grayscale for better hashing
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Create hash from image data
        image_hash = hashlib.md5(blurred.tobytes()).hexdigest()
        
        # Combine with plate number if available
        if plate_number and plate_number.strip():
            combined = f"{image_hash}_{plate_number.strip()}"
            return hashlib.md5(combined.encode()).hexdigest()
        
        return image_hash
    except Exception as e:
        print(f"Error creating rider hash: {e}")
        return None

def is_duplicate_violation(rider_hash, time_window_seconds=300):
    """Check if this rider has been counted recently"""
    if not rider_hash:
        return False
    
    try:
        # First check in-memory hashes for faster response
        with hash_lock:
            if rider_hash in recent_hashes:
                print(f"⚠️ Duplicate violation detected (memory): {rider_hash[:8]}...")
                return True
        
        # Check database for recent violations with same hash
        recent_time = timezone.now() - timedelta(seconds=time_window_seconds)
        recent_violations = Violation.objects.filter(
            rider_hash=rider_hash,
            timestamp__gte=recent_time
        ).exists()
        
        if recent_violations:
            print(f"⚠️ Duplicate violation detected (database): {rider_hash[:8]}...")
            # Add to memory cache
            with hash_lock:
                recent_hashes.add(rider_hash)
            return True
        
        return False
    except Exception as e:
        print(f"Error checking duplicate violation: {e}")
        return False

def cleanup_old_hashes():
    """Clean up old hashes from memory"""
    try:
        # Remove hashes older than 10 minutes from memory
        cutoff_time = timezone.now() - timedelta(minutes=10)
        old_violations = Violation.objects.filter(
            timestamp__lt=cutoff_time
        ).values_list('rider_hash', flat=True)
        
        with hash_lock:
            for old_hash in old_violations:
                if old_hash in recent_hashes:
                    recent_hashes.remove(old_hash)
    except Exception as e:
        print(f"Error cleaning up old hashes: {e}")

def save_violation_to_db(image_data, plate_number=None, rider_hash=None, plate_image_data=None):
    """Save violation to database with image and plate image as BLOB"""
    try:
        camera = get_default_camera()
        if camera is None:
            print("No camera available for violation recording")
            return False
        # Check for duplicate violation
        if rider_hash and is_duplicate_violation(rider_hash):
            print(f"[LOG] Duplicate violation detected for hash: {rider_hash}")
            return False
        # Create violation record with image as BLOB
        violation = Violation.objects.create(
            camera=camera,
            plate_number=plate_number,
            image=image_data,  # Store rider image as BLOB
            plate_image=plate_image_data,  # Store plate image as BLOB
            rider_hash=rider_hash,
            timestamp=timezone.now()
        )
        # Add hash to memory cache
        if rider_hash:
            with hash_lock:
                recent_hashes.add(rider_hash)
        print(f"✅ Violation saved to database: {violation.id} at {violation.timestamp}")
        return True
    except Exception as e:
        print(f"❌ Error saving violation to database: {e}")
        return False


def frame_capture_worker():
    """Continuously capture frames from the camera and put them in a queue."""
    while not stop_inference:
        success, frame = cap.read()
        if not success:
            time.sleep(0.01)
            continue
        # Always keep only the latest frame
        while not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                break
        frame_queue.put(frame)
        time.sleep(0.001)

def iou(boxA, boxB):
    # box: (x1, y1, x2, y2)
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
    return interArea / unionArea if unionArea > 0 else 0

def inference_worker():
    """Worker thread for YOLO inference"""
    global annotated_frame, frame_count
    local_frame_count = 0
    last_cleanup = time.time()
    
    while not stop_inference:
        try:
            # Get latest frame from queue
            frame = frame_queue.get(timeout=0.1)
            local_frame_count += 1
            
            # Periodic cleanup of old hashes
            if time.time() - last_cleanup > 300:  # Every 5 minutes
                cleanup_old_hashes()
                last_cleanup = time.time()
            
            # Only run detection every SKIP_INFERENCE frames
            if local_frame_count % SKIP_INFERENCE != 0:
                with inference_lock:
                    if annotated_frame is not None:
                        annotated_frame = annotated_frame.copy()
                        frame_count = local_frame_count
                continue
                
            det_frame = cv2.resize(frame, DETECTION_RESIZE)
            scale_x = frame.shape[1] / DETECTION_RESIZE[0]
            scale_y = frame.shape[0] / DETECTION_RESIZE[1]
            results = pretrained_model(det_frame, conf=0.4)[0]
            persons = []
            motorcycles = []
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
                    intersection = iw * ih
                    person_area = (px2 - px1) * (py2 - py1)
                    moto_area = (mx2 - mx1) * (my2 - my1)
                    union = person_area + moto_area - intersection
                    iou_val = intersection / union if union > 0 else 0
                    if iou_val > 0.1:
                        rx1 = min(px1, mx1)
                        ry1 = min(py1, my1)
                        rx2 = max(px2, mx2)
                        ry2 = max(py2, my2)
                        rx1, ry1, rx2, ry2 = [int(round(v * scale_x if i % 2 == 0 else v * scale_y)) for i, v in enumerate([rx1, ry1, rx2, ry2])]
                        riders.append(((rx1, ry1, rx2, ry2), person, moto))
                        break
            annotated = frame.copy()
            for (rx1, ry1, rx2, ry2), person, moto in riders:
                cv2.rectangle(annotated, (rx1, ry1), (rx2, ry2), (255, 0, 0), 2)
                cv2.putText(annotated, "Rider", (rx1, ry1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                rider_crop = frame[ry1:ry2, rx1:rx2]
                if rider_crop.size == 0:
                    print("[LOG] Skipping empty rider crop.")
                    continue
                custom_results = custom_model(rider_crop, conf=0.4)[0]
                found_no_helmet = False
                plate_number = None
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
                    cv2.rectangle(annotated, (rx1+cx1, ry1+cy1), (rx1+cx2, ry1+cy2), color, 2)
                    cv2.putText(annotated, clabel, (rx1+cx1, ry1+cy1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                if found_no_helmet:
                    print(f"[LOG] No helmet detected for rider at frame {local_frame_count}.")
                    rider_hash = create_rider_hash(rider_crop, plate_number)
                    is_spatial_duplicate = False
                    for prev_frame_idx, prev_box in recent_no_helmet:
                        if abs(local_frame_count - prev_frame_idx) < SPATIAL_WINDOW and iou((rx1, ry1, rx2, ry2), prev_box) > NO_HELMET_IOU_THRESH:
                            is_spatial_duplicate = True
                            print(f"⚠️ Spatial duplicate detected at frame {local_frame_count}")
                            break
                    if not is_spatial_duplicate:
                        success, jpeg_bytes = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if success:
                            if save_violation_to_db(jpeg_bytes.tobytes(), plate_number, rider_hash):
                                print(f"📸 Violation captured and saved to database at frame {local_frame_count}")
                                recent_no_helmet.append((local_frame_count, (rx1, ry1, rx2, ry2)))
                            else:
                                print(f"⚠️ Violation not saved (duplicate detected or DB error)")
                        else:
                            print(f"❌ Failed to encode violation image")
                    else:
                        print(f"[LOG] Skipped saving due to spatial duplicate at frame {local_frame_count}.")
            with inference_lock:
                annotated_frame = annotated
                frame_count = local_frame_count
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Inference error: {e}")
            continue

# Start frame capture and inference worker threads
frame_capture_thread = threading.Thread(target=frame_capture_worker, daemon=True)
frame_capture_thread.start()
inference_thread = threading.Thread(target=inference_worker, daemon=True)
inference_thread.start()

class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global frame_count, annotated_frame

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
        local_frame_count = 0

        while True:
            try:
                # Use the latest annotated frame
                with inference_lock:
                    output_frame = annotated_frame.copy() if annotated_frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)
                # Encode frame to JPEG with optimized settings
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
                ret, jpeg = cv2.imencode('.jpg', output_frame, encode_params)
                if not ret:
                    continue
                # Send frame
                self.wfile.write(b"--frame\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.end_headers()
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b"\r\n")
                # Frame rate control
                elapsed = time.time() - last_frame_time
                if elapsed < FRAME_INTERVAL:
                    time.sleep(FRAME_INTERVAL - elapsed)
                last_frame_time = time.time()
            except Exception as e:
                print(f"Stream error: {e}")
                break
    def log_message(self, format, *args):
        # Suppress logging for cleaner output
        pass

# Cleanup function

def cleanup():
    global stop_inference
    stop_inference = True
    if inference_thread.is_alive():
        inference_thread.join(timeout=1)
    if frame_capture_thread.is_alive():
        frame_capture_thread.join(timeout=1)
    cap.release()

# Register cleanup on exit
import atexit
atexit.register(cleanup)

server = HTTPServer(('0.0.0.0', 8081), MJPEGHandler)
print("✅ Smooth MJPEG stream running at http://localhost:8081/video")
print(f"📊 Target FPS: {TARGET_FPS}, Inference every {SKIP_INFERENCE} frames")
print("🗄️  Violations will be saved to MySQL database as BLOB")
print("🔄 Enhanced duplicate detection enabled - 5-minute window")
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Stopping server...")
    cleanup()
    server.shutdown()
