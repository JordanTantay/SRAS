# SRAS - Safety Helmet Detection System

A real-time safety helmet detection system using YOLO and optimized MJPEG streaming.

## 🚀 Quick Start

### Option 1: Automatic Startup (Recommended)
```bash
cd SRAS_Project
python start_servers.py
```

### Option 2: Manual Startup
1. **Start MJPEG Stream Server:**
   ```bash
   cd SRAS_Project
   python stream_mjpeg.py
   ```

2. **Start Django Server (in new terminal):**
   ```bash
   cd SRAS_Project
   python manage.py runserver
   ```

## 📱 Access Points

- **Main Interface**: http://localhost:8000/monitor/
- **High Performance Mode**: http://localhost:8000/monitor-smooth/
- **Direct Stream**: http://localhost:8081/video

## 🏗️ Architecture

### Simplified Design
- **`stream_mjpeg.py`**: Handles all video streaming and YOLO detection
- **Django**: Provides web interface only (no duplicate streaming)
- **No code repetition**: Single source of truth for video processing

### Key Features
- ✅ **30 FPS smooth streaming**
- ✅ **Threaded YOLO inference** (non-blocking)
- ✅ **Optimized frame processing**
- ✅ **Modern responsive UI**
- ✅ **High-performance viewing mode**

## 🎮 Controls

### High Performance Mode Keyboard Shortcuts:
- **I** - Toggle info overlay
- **S** - Toggle stats header
- **R** - Refresh stream
- **F** - Toggle fullscreen

## ⚙️ Configuration

Edit `stream_mjpeg.py` to customize:
- `TARGET_FPS = 30` - Target frame rate
- `SKIP_INFERENCE = 3` - YOLO inference frequency
- `JPEG_QUALITY = 85` - Image quality vs speed
- Camera URL: `cv2.VideoCapture("http://192.168.1.4:8080/video")`

## 🔧 Troubleshooting

### Stream Not Working?
1. Check if `stream_mjpeg.py` is running on port 8081
2. Verify camera URL in `stream_mjpeg.py`
3. Ensure YOLO model file exists: `customyolov8n.pt`

### Performance Issues?
- Reduce `TARGET_FPS` for lower CPU usage
- Increase `SKIP_INFERENCE` for faster detection
- Lower `JPEG_QUALITY` for faster streaming

## 📁 File Structure

```
SRAS_Project/
├── stream_mjpeg.py          # Main streaming server
├── start_servers.py         # Auto-startup script
├── manage.py               # Django management
├── customyolov8n.pt        # YOLO model
├── SRAS_App/
│   ├── views.py            # Simple Django views
│   ├── urls.py             # URL routing
│   └── templates/core/
│       ├── monitor.html    # Main interface
│       └── monitor_smooth.html  # High-performance mode
└── README.md               # This file
```

## 🎯 Benefits of This Setup

1. **No Code Duplication**: Single streaming implementation
2. **Better Performance**: Optimized MJPEG server
3. **Simpler Maintenance**: One place to update streaming logic
4. **Cleaner Architecture**: Separation of concerns
5. **Easier Debugging**: Clear server responsibilities

## 🛑 Stopping Servers

- **Automatic mode**: Press `Ctrl+C` in the startup script
- **Manual mode**: Press `Ctrl+C` in each terminal window 