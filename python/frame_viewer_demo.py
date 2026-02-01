#!/usr/bin/env python3
"""
Video Stream Viewer for SparthHack11
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
        self.current_frame_idx = 0
        
        if not self.frames_dir.exists():
            print(f"Error: Frames directory '{frames_dir}' not found!")
            print("Make sure to record video on the website first.")
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
    
    def display_frame(self, frame_path):
        """Display a frame"""
        frame = cv2.imread(str(frame_path))
        
        if frame is None:
            print(f"Error reading frame: {frame_path}")
            return False
        
        h, w = frame.shape[:2]
        
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
        cv2.imshow("SparthHack11 - Video Stream Viewer", frame)
        
        return True
    
    def run_viewer(self):
        """Run the interactive frame viewer"""
        if not self.load_frames():
            return
        
        self.current_frame_idx = 0
        
        print("\n" + "="*60)
        print("SparthHack11 Video Stream Viewer")
        print("="*60)
        print(f"Total frames: {len(self.frame_list)}")
        print("\nControls:")
        print("  → (Right Arrow): Next frame")
        print("  ← (Left Arrow): Previous frame")
        print("  SPACE: Play/Pause automatic playback")
        print("  0: Jump to start")
        print("  9: Jump to end")
        print("  Q or ESC: Quit")
        print("="*60 + "\n")
        
        auto_play = False
        running = True
        
        while running and self.current_frame_idx < len(self.frame_list):
            frame_path = self.frame_list[self.current_frame_idx]
            
            # Display the frame
            self.display_frame(frame_path)
            
            # Handle keyboard input
            key = cv2.waitKey(self.delay) & 0xFF
            
            if key == ord('q') or key == 27:  # Q or ESC
                print("Exiting...")
                running = False
            
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
            
            # Auto-play
            if auto_play:
                self.current_frame_idx += 1
                if self.current_frame_idx >= len(self.frame_list):
                    self.current_frame_idx = len(self.frame_list) - 1
                    auto_play = False
                    print("End of frames reached. Auto-play stopped.")
        
        cv2.destroyAllWindows()
        print("Viewer closed.")
    
    def run_realtime_monitor(self):
        """Monitor frames directory and display new frames as they arrive"""
        print("\n" + "="*60)
        print("SparthHack11 Real-time Frame Monitor")
        print("="*60)
        print(f"Monitoring: {self.frames_dir}")
        print("Waiting for new frames... (Start recording on the website)")
        print("Press Q or ESC to quit")
        print("="*60 + "\n")
        
        seen_frames = set()
        running = True
        
        while running:
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
                running = False
                print("Exiting real-time monitor...")
        
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Video Stream Viewer for SparthHack11",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python frame_viewer_demo.py                    # Browse recorded frames
  python frame_viewer_demo.py --monitor          # Monitor new frames in real-time
  python frame_viewer_demo.py --fps 15           # Slower playback (15 fps)
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
    
    args = parser.parse_args()
    
    # Calculate delay from FPS
    delay = max(1, int(1000 / args.fps))
    
    viewer = VideoStreamViewer(
        frames_dir=args.frames_dir,
        delay=delay
    )
    
    if args.monitor:
        viewer.run_realtime_monitor()
    else:
        viewer.run_viewer()


if __name__ == "__main__":
    main()

