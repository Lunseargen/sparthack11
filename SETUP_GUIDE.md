# SparthHack11 - Complete Setup & Usage Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Start the Website
```bash
cd sparthack11
python -m http.server 8000
```

Then open http://localhost:8000 in your browser

### Step 2: Record Video
1. Click "📹 Page 1: Video Stream"
2. Click "▶️ Start Recording"
3. Allow camera access
4. Perform actions for 10-30 seconds
5. Click "⏹️ Stop Recording"

### Step 3: View Frames with Python
```bash
python test_frame_viewer.py
```

That's it! You can now see your recorded frames.

---

## 📁 Project Structure

```
sparthack11/
│
├── HTML Pages (Web Interface)
│   ├── index.html              # Landing page with navigation
│   ├── page1.html              # Video stream & annotations
│   ├── page2.html              # Interactive quiz
│   └── page3.html              # MP4 file manager
│
├── JavaScript (Frontend Logic)
│   └── js/
│       ├── video-capture.js    # Video recording and frame saving
│       ├── quiz.js             # Quiz functionality and scoring
│       └── file-manager.js     # File upload/download management
│
├── Python (Backend & Analysis)
│   └── python/
│       ├── app.py              # Flask web server (optional)
│       ├── vision_detector.py  # Character detection with OpenCV
│       ├── frame_viewer_demo.py    # Browse & display frames
│       ├── frame_analyzer_demo.py  # Analyze frames (motion, edges, etc)
│       └── requirements.txt    # Python dependencies
│
├── Demo Scripts
│   ├── test_frame_viewer.py    # Quick start guide
│   └── DEMO_GUIDE.py           # This guide
│
├── Data Folders
│   ├── frames/                 # Recorded video frames (auto-created)
│   ├── uploads/                # Uploaded MP4 files
│   └── audio/                  # MP3 audio files
│
└── README.md                   # Project documentation
```

---

## 🎯 Features Overview

### Page 1: Video Stream & Annotations
- **Live webcam capture** from your browser
- **Automatic frame saving** (up to 1000 frames)
- **Text annotations** in two textboxes
- **Audio playback** for MP3 files
- **Manual frame capture** button
- All frames saved to `frames/` directory

### Page 2: Interactive Quiz
- **Character selection** (A-Z checkboxes)
- **Real-time detection** from video frames
- **Detection display** showing AI results
- **Score tracking** (correct/total)
- **Question progression** with Next button
- **Video recording** during quiz sessions

### Page 3: File Manager
- **Drag-and-drop MP4 upload**
- **File list** with sizes and dates
- **Download any file** with one click
- **Delete files** from storage
- **Progress bar** during upload
- Up to **500MB per file**

---

## 🐍 Python Demo Scripts

### 1. Frame Viewer (Browse Recorded Frames)

**Quick start:**
```bash
python test_frame_viewer.py
```

**Advanced viewer:**
```bash
python python/frame_viewer_demo.py
```

**Real-time monitor:**
```bash
python python/frame_viewer_demo.py --monitor
```

**Slow motion (15 FPS):**
```bash
python python/frame_viewer_demo.py --fps 15
```

**Controls:**
- `→` / `←` : Next/Previous frame
- `SPACE` : Play/Pause
- `0` / `9` : Jump to start/end
- `I` : Toggle metadata
- `S` : Save frame
- `Q` / `ESC` : Quit

---

### 2. Frame Analyzer (Statistics & Detection)

**Basic analysis:**
```bash
python python/frame_analyzer_demo.py
```

**With edge detection visualization:**
```bash
python python/frame_analyzer_demo.py --show-edges
```

**With motion detection visualization:**
```bash
python python/frame_analyzer_demo.py --show-motion
```

**Output:** Generates `frame_analysis_report.json` with:
- Average brightness (0-255)
- Average contrast
- Motion percentage between frames
- Edge pixel counts
- Object count estimates
- Per-frame detailed statistics

---

### 3. Vision Detector (Character Detection)

**Detect latest frame:**
```bash
python python/vision_detector.py detect_latest
```

**Batch process all frames:**
```bash
python python/vision_detector.py batch
```

**Output:** JSON format with detection results

---

### 4. Flask Backend Server (Optional)

```bash
python python/app.py
```

Starts server at `http://localhost:5000` with API endpoints:
- `POST /api/upload` - Upload MP4
- `GET /api/list-files` - List files
- `GET /api/download/<file>` - Download
- `POST /api/save-frame` - Save frames
- `POST /api/detect` - Run detection
- `GET /audio/<file>` - Serve audio

---

## 💻 Installation & Setup

### Prerequisites
- Python 3.8+ (for backend)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Webcam for video capture

### Step 1: Install Python Dependencies
```bash
cd python
pip install -r requirements.txt
```

Required packages:
- Flask 2.3.3
- OpenCV (opencv-python)
- NumPy
- Werkzeug

### Step 2: Start Website (No Backend)
```bash
cd sparthack11
python -m http.server 8000
```

Then open: http://localhost:8000

### Step 3: Start Backend (Optional)
```bash
cd sparthack11/python
python app.py
```

Backend runs at: http://localhost:5000

---

## 🎬 Usage Workflows

### Workflow 1: Record and View Video
```bash
# 1. Start website
python -m http.server 8000

# 2. Record on Page 1 (in browser)
# 3. View frames
python test_frame_viewer.py

# 4. Analyze frames
python python/frame_analyzer_demo.py
```

### Workflow 2: Test Vision Detection
```bash
# 1. Record video with character objects
# 2. Run detection
python python/vision_detector.py detect_latest

# 3. Analyze results
python python/frame_analyzer_demo.py --show-edges
```

### Workflow 3: Full Stack Testing
```bash
# Terminal 1: Start website
python -m http.server 8000

# Terminal 2: Start backend
cd python && python app.py

# Terminal 3: Monitor frames
python python/frame_viewer_demo.py --monitor

# Terminal 4: Analyze
python python/frame_analyzer_demo.py
```

---

## 🔧 Configuration

### Audio File
Edit `page1.html` to use your audio file:
```javascript
const audio = new Audio('audio/your-file.mp3');
```

### Frame Storage Limit
Edit `js/video-capture.js`:
```javascript
this.maxFrames = 1000;  // Change this number
```

### FPS (Frames Per Second)
Edit `js/video-capture.js`:
```javascript
setTimeout(captureLoop, 33); // 33ms = 30fps
                            // 50ms = 20fps
                            // 16ms = 60fps
```

### File Upload Limit
Edit `python/app.py`:
```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
```

---

## 📊 Data Output Formats

### Frame Metadata (JSON)
```json
{
  "frameNumber": 42,
  "textbox1": "User annotation 1",
  "textbox2": "User annotation 2",
  "timestamp": "2026-01-31T10:30:45.123Z"
}
```

### Analysis Report (JSON)
```json
{
  "total_frames": 150,
  "avg_brightness": 127.5,
  "avg_contrast": 45.3,
  "avg_motion": 8.2,
  "avg_edges": 15423,
  "avg_objects": 2.1,
  "frames": [...]
}
```

### Detection Output (JSON)
```json
{
  "detection": "A to Z"
}
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera not working | Check browser permissions, ensure camera hardware available |
| No frames saving | Verify `frames/` folder exists, check disk space |
| OpenCV errors | `pip install --upgrade opencv-python` |
| Port 8000 in use | Use different port: `python -m http.server 8001` |
| Flask import error | `pip install flask werkzeug` |
| No frames found | Record video on Page 1 first |
| Audio not playing | Add MP3 file to `audio/` folder, update path |
| Frame viewer won't open | Install numpy: `pip install numpy` |

---

## 🌐 Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Best performance |
| Firefox | ✅ Full | Works well |
| Safari | ✅ Full | iOS: limited camera access |
| Edge | ✅ Full | Chromium-based |
| IE 11 | ❌ No | Too old, not supported |

---

## 📱 Mobile Considerations

- **Page 1 & 2**: Work on mobile with camera access
- **Page 3**: File upload works on mobile
- **Frame viewers**: Work best on desktop
- **Backend**: Can run on mobile with Python installed

---

## 🔒 Security Notes

- Frames are stored locally on your machine
- No data is sent without explicit upload
- File uploads are validated on server
- Use HTTPS in production for camera access
- Clean up old frames periodically

---

## 📈 Performance Tips

1. **Lower resolution**: Reduces frame size and storage
2. **Reduce FPS**: Change delay from 33ms to 50ms or 100ms
3. **Limit frames**: Set maxFrames to 500 instead of 1000
4. **Use server storage**: More efficient than IndexedDB
5. **Batch detection**: Process multiple frames at once

---

## 🚀 Next Steps

1. ✅ Record a 30-second video on Page 1
2. ✅ View frames with: `python test_frame_viewer.py`
3. ✅ Analyze with: `python python/frame_analyzer_demo.py`
4. ✅ Try detection: `python python/vision_detector.py detect_latest`
5. ✅ Upload files on Page 3

---

## 📚 Additional Resources

- [OpenCV Documentation](https://docs.opencv.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)

---

## 📞 Support

For issues:
1. Check browser console (F12) for JavaScript errors
2. Check terminal output for Python errors
3. Verify all dependencies installed: `pip list`
4. Check folder permissions in `frames/` and `uploads/`

---

**Last Updated:** January 31, 2026
**Version:** 1.0.0
**Status:** ✅ Complete and ready to use!
