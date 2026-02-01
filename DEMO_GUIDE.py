#!/usr/bin/env python3
"""
DEMO SCRIPTS GUIDE - SparthHack11
Quick reference for testing and debugging
"""

import sys
from pathlib import Path


DEMOS = {
    "test_frame_viewer.py": {
        "description": "Quick start guide and interactive frame browser",
        "usage": "python test_frame_viewer.py",
        "features": [
            "Browse recorded frames",
            "View metadata (annotations, timestamps)",
            "Play/pause functionality",
            "Jump to start/end",
            "Save individual frames"
        ]
    },
    "frame_viewer_demo.py": {
        "description": "Advanced frame viewer with real-time monitoring",
        "usage": [
            "python python/frame_viewer_demo.py              # Browse frames",
            "python python/frame_viewer_demo.py --monitor    # Real-time monitor",
            "python python/frame_viewer_demo.py --fps 15     # 15 FPS playback"
        ],
        "features": [
            "Frame navigation with arrow keys",
            "Automatic playback with pause/resume",
            "Real-time monitoring of new frames",
            "Metadata overlay (textboxes, timestamps)",
            "Speed adjustment (FPS control)"
        ]
    },
    "frame_analyzer_demo.py": {
        "description": "Analyze frames for motion, brightness, objects, edges",
        "usage": [
            "python python/frame_analyzer_demo.py              # Full analysis",
            "python python/frame_analyzer_demo.py --show-edges # Show edge detection",
            "python python/frame_analyzer_demo.py --show-motion # Show motion detection"
        ],
        "features": [
            "Brightness analysis",
            "Contrast calculation",
            "Motion detection between frames",
            "Edge detection (Canny)",
            "Object counting via contours",
            "Generate JSON report"
        ]
    },
    "vision_detector.py": {
        "description": "Character detection using OpenCV shape analysis",
        "usage": [
            "python python/vision_detector.py detect_latest   # Detect latest frame",
            "python python/vision_detector.py batch           # Batch process all frames"
        ],
        "features": [
            "Character classification from images",
            "Edge detection and contour analysis",
            "Shape properties (solidity, aspect ratio)",
            "Batch processing support",
            "JSON output format"
        ]
    },
    "app.py": {
        "description": "Flask backend server for file uploads and detection",
        "usage": "python python/app.py",
        "features": [
            "HTTP API for file uploads/downloads",
            "Frame storage and retrieval",
            "Vision detection endpoint",
            "Metadata management",
            "Audio file serving"
        ]
    }
}

WORKFLOW = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    SPARTHACK11 WORKFLOW GUIDE                             ║
╚════════════════════════════════════════════════════════════════════════════╝

1. START THE WEBSITE
   ────────────────────
   cd sparthack11
   python -m http.server 8000
   
   Open browser: http://localhost:8000

2. RECORD VIDEO (Page 1)
   ──────────────────────
   - Click "Page 1: Video Stream"
   - Click "Start Recording"
   - Allow camera access
   - Perform actions in front of camera
   - Click "Stop Recording"
   ✓ Frames saved to 'frames/' directory

3. VIEW FRAMES (Interactive)
   ─────────────────────────
   Option A - Quick Start:
   $ python test_frame_viewer.py
   
   Option B - Advanced Viewer:
   $ python python/frame_viewer_demo.py
   
   Option C - Real-time Monitor:
   $ python python/frame_viewer_demo.py --monitor

4. ANALYZE FRAMES (Statistics)
   ────────────────────────────
   $ python python/frame_analyzer_demo.py
   
   With visualization:
   $ python python/frame_analyzer_demo.py --show-edges
   $ python python/frame_analyzer_demo.py --show-motion

5. RUN VISION DETECTION
   ─────────────────────
   $ python python/vision_detector.py detect_latest
   
   Batch process:
   $ python python/vision_detector.py batch

6. START BACKEND SERVER (Optional)
   ────────────────────────────────
   $ python python/app.py
   
   API available at: http://localhost:5000

════════════════════════════════════════════════════════════════════════════════

KEYBOARD SHORTCUTS (Frame Viewer)
─────────────────────────────────
→ (Right Arrow)  : Next frame
← (Left Arrow)   : Previous frame
SPACE            : Play/Pause
0                : Jump to start
9                : Jump to end
I                : Toggle metadata info
S                : Save current frame
Q or ESC         : Quit

════════════════════════════════════════════════════════════════════════════════

QUICK COMMANDS
──────────────
# Record 30 seconds of video and browse frames
python test_frame_viewer.py

# View frames with slow motion (15 FPS)
python python/frame_viewer_demo.py --fps 15

# Monitor incoming frames in real-time
python python/frame_analyzer_demo.py --show-edges

# Generate analysis report
python python/frame_analyzer_demo.py > analysis_report.txt

════════════════════════════════════════════════════════════════════════════════
"""


def print_header():
    print("\n" + "="*80)
    print("SPARTHACK11 - DEMO SCRIPTS GUIDE".center(80))
    print("="*80 + "\n")


def print_demo_info(name, info):
    print(f"\n📄 {name}")
    print("─" * 80)
    print(f"   Description: {info['description']}")
    print(f"\n   Usage:")
    
    usage = info.get('usage', [])
    if isinstance(usage, str):
        usage = [usage]
    
    for cmd in usage:
        print(f"   $ {cmd}")
    
    print(f"\n   Features:")
    for feature in info.get('features', []):
        print(f"   ✓ {feature}")


def main():
    print_header()
    
    # Check if in correct directory
    if not Path("index.html").exists():
        print("⚠️  Not in sparthack11 directory!")
        print("   Please run from the project root directory.\n")
        sys.exit(1)
    
    print(WORKFLOW)
    
    print("\n" + "="*80)
    print("DETAILED SCRIPT INFORMATION".center(80))
    print("="*80)
    
    for script_name, info in DEMOS.items():
        print_demo_info(script_name, info)
    
    print("\n" + "="*80)
    print("\nTROUBLESHOOTING")
    print("─" * 80)
    
    issues = [
        ("No frames found", "Record video on Page 1 first using 'Start Recording'"),
        ("Camera permission denied", "Check browser settings and allow camera access"),
        ("OpenCV not installed", "Run: pip install opencv-python numpy"),
        ("Flask import error", "Run: pip install flask werkzeug"),
        ("Port 8000 already in use", "Use different port: python -m http.server 8001"),
    ]
    
    for issue, solution in issues:
        print(f"\n   ❌ {issue}")
        print(f"      → {solution}")
    
    print("\n" + "="*80)
    print("\n💡 TIPS")
    print("─" * 80)
    print("""
   • Always start with test_frame_viewer.py to verify frames are saving
   • Use --fps 15 for slow-motion playback of fast movements
   • Run frame_analyzer_demo.py with --show-edges to debug detection issues
   • Check frame_analysis_report.json for detailed statistics
   • Frames are stored as JPEG files in the 'frames/' directory
   • Metadata is stored as JSON files next to each frame
   • Maximum 1000 frames per recording session (configurable)
""")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
