#!/usr/bin/env python3
"""
Frame Viewer Demo - SparthHack11
Reads frames saved by JavaScript video stream and displays them in real-time
Useful for testing and debugging the video capture system
"""

import cv2
import json
import os
from pathlib import Path
from datetime import datetime
import time
import threading
import argparse


class FrameViewerDemo:
    def __init__(self, frames_dir="frames", delay=33, show_metadata=True):
        """
        Initialize the frame viewer
        
        Args:
            frames_dir: Directory containing frames
            delay: Delay between frames in milliseconds (33 = ~30fps)
            show_metadata: Whether to display metadata overlays
        """
        self.frames_dir = Path(frames_dir)
        self.delay = delay
        self.show_metadata = show_metadata
        self.running = False
        self.current_frame_idx = 0
        self.frame_list = []
        self.metadata_cache = {}
        
        if not self.frames_dir.exists():
            print(f"Error: Frames directory '{frames_dir}' not found!")
            print("Make sure to record video on page 1 first.")
            exit(1)
    
    def load_frames(self):
        """Load list of available frames from directory"""
        frames = sorted(self.frames_dir.glob("frame_*.jpg"))
        quiz_frames = sorted(self.frames_dir.glob("quiz_frame_*.jpg"))
        
        self.frame_list = frames + quiz_frames
        
        if not self.frame_list:
            print("No frames found! Record video on page 1 or page 2 first.")
            return False
        
        print(f"Found {len(frames)} regular frames and {len(quiz_frames)} quiz frames")
        return True
    
    def load_metadata(self, frame_path):
        """Load metadata for a frame"""
        metadata_path = frame_path.with_stem(frame_path.stem + "_meta")
        metadata_path = metadata_path.with_suffix(".json")
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def display_frame_with_info(self, frame_path):
        """Display a frame with metadata overlay"""
        frame = cv2.imread(str(frame_path))
        
        if frame is None:
            print(f"Error reading frame: {frame_path}")
            return False
        
        h, w = frame.shape[:2]
        
        # Load and display metadata if available
        metadata = self.load_metadata(frame_path)
        
        if self.show_metadata and metadata:
            # Add semi-transparent overlay for text
            overlay = frame.copy()
            cv2.rectangle(overlay, (10, 10), (w - 10, 150), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            # Draw metadata text
            y_offset = 40
            line_height = 30
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            color = (0, 255, 0)
            thickness = 1
            
            # Frame number
            cv2.putText(
                frame, 
                f"Frame: {metadata.get('frameNumber', 'N/A')}",
                (20, y_offset),
                font, font_scale, color, thickness
            )
            
            # Textbox 1
            textbox1 = metadata.get('textbox1', '')[:40]
            cv2.putText(
                frame,
                f"Text1: {textbox1}",
                (20, y_offset + line_height),
                font, font_scale, color, thickness
            )
            
            # Textbox 2
            textbox2 = metadata.get('textbox2', '')[:40]
            cv2.putText(
                frame,
                f"Text2: {textbox2}",
                (20, y_offset + line_height * 2),
                font, font_scale, color, thickness
            )
            
            # Timestamp
            timestamp = metadata.get('timestamp', 'N/A')
            if isinstance(timestamp, str):
                timestamp = timestamp.split('T')[-1][:8]
            cv2.putText(
                frame,
                f"Time: {timestamp}",
                (20, y_offset + line_height * 3),
                font, font_scale, color, thickness
            )
        
        # Display frame info at bottom
        info_text = f"{frame_path.name} | {self.current_frame_idx + 1}/{len(self.frame_list)}"
        cv2.putText(
            frame,
            info_text,
            (10, h - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        # Display the frame
        cv2.imshow("SparthHack11 - Frame Viewer", frame)
        
        return True
    
    def run_viewer(self):
        """Run the interactive frame viewer"""
        if not self.load_frames():
            return
        
        self.running = True
        self.current_frame_idx = 0
        
        print("\n" + "="*60)
        print("SparthHack11 Frame Viewer Demo")
        print("="*60)
        print(f"Total frames: {len(self.frame_list)}")
        print("\nControls:")
        print("  → (Right Arrow): Next frame")
        print("  ← (Left Arrow): Previous frame")
        print("  SPACE: Play/Pause automatic playback")
        print("  0: Jump to start")
        print("  9: Jump to end")
        print("  I: Toggle metadata info")
        print("  Q or ESC: Quit")
        print("="*60 + "\n")
        
        auto_play = False
        
        while self.running:
            if self.current_frame_idx < len(self.frame_list):
                frame_path = self.frame_list[self.current_frame_idx]
                
                # Display the frame
                self.display_frame_with_info(frame_path)
                
                # Handle keyboard input
                key = cv2.waitKey(self.delay) & 0xFF
                
                if key == ord('q') or key == 27:  # Q or ESC
                    print("Exiting...")
                    self.running = False
                
                elif key == 83 or key == ord('d'):  # Right arrow or D
                    if self.current_frame_idx < len(self.frame_list) - 1:
                        self.current_frame_idx += 1
                        print(f"Frame {self.current_frame_idx + 1}/{len(self.frame_list)}")
                
                elif key == 81 or key == ord('a'):  # Left arrow or A
                    if self.current_frame_idx > 0:
                        self.current_frame_idx -= 1
                        print(f"Frame {self.current_frame_idx + 1}/{len(self.frame_list)}")
                
                elif key == ord(' '):  # Space
                    auto_play = not auto_play
                    print(f"Playback: {'Playing' if auto_play else 'Paused'}")
                
                elif key == ord('0'):  # Jump to start
                    self.current_frame_idx = 0
                    print("Jumped to start")
                
                elif key == ord('9'):  # Jump to end
                    self.current_frame_idx = len(self.frame_list) - 1
                    print("Jumped to end")
                
                elif key == ord('i'):  # Toggle info
                    self.show_metadata = not self.show_metadata
                    print(f"Metadata info: {'ON' if self.show_metadata else 'OFF'}")
                
                elif key == ord('s'):  # Save current frame
                    output_path = f"frame_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    frame = cv2.imread(str(self.frame_list[self.current_frame_idx]))
                    cv2.imwrite(output_path, frame)
                    print(f"Frame saved to {output_path}")
                
                # Auto-play
                if auto_play:
                    self.current_frame_idx += 1
                    if self.current_frame_idx >= len(self.frame_list):
                        self.current_frame_idx = len(self.frame_list) - 1
                        auto_play = False
                        print("End of frames reached. Auto-play stopped.")
            else:
                break
        
        cv2.destroyAllWindows()
        print("Frame viewer closed.")
    
    def run_realtime_monitor(self):
        """Monitor frames directory and display new frames as they arrive"""
        print("\n" + "="*60)
        print("SparthHack11 Real-time Frame Monitor")
        print("="*60)
        print(f"Monitoring: {self.frames_dir}")
        print("Waiting for new frames... (Start recording on page 1 or 2)")
        print("Press Q or ESC to quit")
        print("="*60 + "\n")
        
        seen_frames = set()
        self.running = True
        
        while self.running:
            # Get current frames
            current_frames = set(f.name for f in self.frames_dir.glob("*.jpg"))
            
            # Find new frames
            new_frames = current_frames - seen_frames
            
            if new_frames:
                # Display the latest new frame
                latest = max(
                    [self.frames_dir / f for f in new_frames],
                    key=lambda x: x.stat().st_mtime
                )
                
                frame = cv2.imread(str(latest))
                if frame is not None:
                    h, w = frame.shape[:2]
                    cv2.putText(
                        frame,
                        f"New: {latest.name}",
                        (10, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )
                    cv2.imshow("SparthHack11 - Real-time Monitor", frame)
                    print(f"New frame: {latest.name}")
                
                seen_frames.update(new_frames)
            
            # Check for quit
            key = cv2.waitKey(100) & 0xFF
            if key == ord('q') or key == 27:
                self.running = False
                print("Exiting real-time monitor...")
        
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Frame Viewer Demo for SparthHack11",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python frame_viewer_demo.py                    # Browse recorded frames
  python frame_viewer_demo.py --monitor          # Monitor new frames in real-time
  python frame_viewer_demo.py --fps 15           # Slower playback (15 fps)
  python frame_viewer_demo.py --no-metadata      # Hide metadata overlay
        """
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
    
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Monitor directory for new frames in real-time'
    )
    
    parser.add_argument(
        '--no-metadata',
        action='store_true',
        help='Hide metadata overlay'
    )
    
    args = parser.parse_args()
    
    # Calculate delay from FPS
    delay = max(1, int(1000 / args.fps))
    
    viewer = FrameViewerDemo(
        frames_dir=args.frames_dir,
        delay=delay,
        show_metadata=not args.no_metadata
    )
    
    if args.monitor:
        viewer.run_realtime_monitor()
    else:
        viewer.run_viewer()


if __name__ == "__main__":
    main()
