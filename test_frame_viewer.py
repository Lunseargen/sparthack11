#!/usr/bin/env python3
"""
Quick Start Guide for Frame Viewer Demo
Shows how to test the video frame capture from JavaScript
"""

import subprocess
import sys
from pathlib import Path


def main():
    print("\n" + "="*70)
    print("SparthHack11 Frame Viewer - Quick Start Guide")
    print("="*70)
    
    print("""
Step 1: Record Video on the Website
-----------------------------------
1. Open index.html in your browser (or run: python -m http.server 8000)
2. Click "Page 1: Video Stream"
3. Click "Start Recording"
4. Allow camera access
5. Speak or perform actions in front of the camera
6. Click "Stop Recording" after a few seconds

Step 2: Run Frame Viewer
------------------------
Your frames will be saved to the 'frames/' directory.
You can now view them with this script.

""")
    
    print("Available Commands:")
    print("-" * 70)
    
    commands = [
        ("Browse Frames", "python python/frame_viewer_demo.py"),
        ("Real-time Monitor", "python python/frame_viewer_demo.py --monitor"),
        ("Slow Motion (15 FPS)", "python python/frame_viewer_demo.py --fps 15"),
        ("No Metadata Info", "python python/frame_viewer_demo.py --no-metadata"),
    ]
    
    for desc, cmd in commands:
        print(f"\n{desc}:")
        print(f"  $ {cmd}")
    
    print("\n" + "-" * 70)
    print("\nControls in Frame Viewer:")
    print("  → (Right)  : Next frame")
    print("  ← (Left)   : Previous frame")
    print("  SPACE      : Play/Pause")
    print("  0          : Jump to start")
    print("  9          : Jump to end")
    print("  I          : Toggle metadata info")
    print("  S          : Save current frame")
    print("  Q or ESC   : Quit")
    
    print("\n" + "="*70)
    
    # Check if frames directory exists
    frames_dir = Path("frames")
    if frames_dir.exists():
        frame_count = len(list(frames_dir.glob("frame_*.jpg")))
        quiz_count = len(list(frames_dir.glob("quiz_frame_*.jpg")))
        
        print(f"\nCurrent Status:")
        print(f"  Regular frames: {frame_count}")
        print(f"  Quiz frames: {quiz_count}")
        print(f"  Total: {frame_count + quiz_count}")
        
        if frame_count + quiz_count > 0:
            print("\n✓ Frames found! You can now run the viewer.")
            
            # Ask to run viewer
            response = input("\nWould you like to launch the frame viewer? (y/n): ").strip().lower()
            if response == 'y':
                try:
                    subprocess.run([sys.executable, "python/frame_viewer_demo.py"])
                except KeyboardInterrupt:
                    print("\nViewer closed.")
        else:
            print("\n✗ No frames found. Please record video first on page 1.")
    else:
        print(f"\n✗ Frames directory not found at '{frames_dir}'")
        print("  Please record video on page 1 first.")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
