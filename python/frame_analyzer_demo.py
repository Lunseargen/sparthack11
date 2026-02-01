#!/usr/bin/env python3
"""
Simple Video Stream Viewer for SparthHack11
Displays video frames captured from the web interface
"""

import cv2
from pathlib import Path
import argparse


class VideoStreamViewer:
    """Simple viewer for video stream frames"""
    
    def __init__(self, frames_dir="frames", delay=33):
        """
        Initialize the viewer
        
        Args:
            frames_dir: Directory containing frames
            delay: Delay between frames in milliseconds (33 = ~30fps)
        """
        self.frames_dir = Path(frames_dir)
        self.delay = delay
        self.frame_list = []
        
        if not self.frames_dir.exists():
            print(f"Error: Frames directory '{frames_dir}' not found!")
            exit(1)
    
    def load_frames(self):
        """Load available frames from directory"""
        frames = sorted(self.frames_dir.glob("frame_*.jpg"))
        quiz_frames = sorted(self.frames_dir.glob("quiz_frame_*.jpg"))
        
        self.frame_list = frames + quiz_frames
        
        if not self.frame_list:
            print("No frames found! Record video on the website first.")
            return False
        
        print(f"Found {len(frames)} regular frames and {len(quiz_frames)} quiz frames")
        return True
    
    def run_viewer(self):
        """Run the interactive frame viewer"""
        if not self.load_frames():
            return
        
        print("\n" + "="*60)
        print("SparthHack11 Video Stream Viewer")
        print("="*60)
        print(f"Total frames: {len(self.frame_list)}")
        print("\nControls:")
        print("  → (Right Arrow): Next frame")
        print("  ← (Left Arrow): Previous frame")
        print("  SPACE: Play/Pause automatic playback")
        print("  Q or ESC: Quit")
        print("="*60 + "\n")
        
        current_frame_idx = 0
        auto_play = False
        
        while current_frame_idx < len(self.frame_list):
            frame_path = self.frame_list[current_frame_idx]
            
            # Read and display frame
            frame = cv2.imread(str(frame_path))
            if frame is not None:
                h, w = frame.shape[:2]
                
                # Display frame info at bottom
                info_text = f"{frame_path.name} | {current_frame_idx + 1}/{len(self.frame_list)}"
                cv2.putText(
                    frame,
                    info_text,
                    (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
                
                cv2.imshow("SparthHack11 - Video Stream", frame)
            
            # Handle keyboard input
            key = cv2.waitKey(self.delay) & 0xFF
            
            if key == ord('q') or key == 27:  # Q or ESC
                print("Exiting...")
                break
            
            elif key == 83 or key == ord('d'):  # Right arrow or D
                if current_frame_idx < len(self.frame_list) - 1:
                    current_frame_idx += 1
                    print(f"Frame {current_frame_idx + 1}/{len(self.frame_list)}")
            
            elif key == 81 or key == ord('a'):  # Left arrow or A
                if current_frame_idx > 0:
                    current_frame_idx -= 1
                    print(f"Frame {current_frame_idx + 1}/{len(self.frame_list)}")
            
            elif key == ord(' '):  # Space
                auto_play = not auto_play
                print(f"Playback: {'Playing' if auto_play else 'Paused'}")
            
            # Auto-play
            if auto_play:
                current_frame_idx += 1
                if current_frame_idx >= len(self.frame_list):
                    current_frame_idx = len(self.frame_list) - 1
                    auto_play = False
                    print("End of frames reached. Auto-play stopped.")
        
        cv2.destroyAllWindows()
        print("Viewer closed.")


def main():
    parser = argparse.ArgumentParser(
        description="Video Stream Viewer for SparthHack11"
    )
    
    parser.add_argument(
        '--frames-dir',
        default='frames',
        help='Directory containing frames (default: frames)'
    )
    
    parser.add_argument(
        '--fps',
        type=int,
        default=30,
        help='Playback speed in FPS (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Calculate delay from FPS
    delay = max(1, int(1000 / args.fps))
    
    viewer = VideoStreamViewer(
        frames_dir=args.frames_dir,
        delay=delay
    )
    
    viewer.run_viewer()


if __name__ == "__main__":
    main()

