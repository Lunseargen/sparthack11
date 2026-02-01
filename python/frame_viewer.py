import cv2
import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FrameDisplayHandler(FileSystemEventHandler):
    def __init__(self, frames_dir):
        self.frames_dir = frames_dir
        self.last_displayed = None
        self.frame_count = 0
        self.gui_available = False
        
        # Try to detect if GUI is available
        try:
            import sys
            if 'DISPLAY' not in os.environ and sys.platform == 'darwin':
                print("⚠ Warning: GUI display may not be available on this system")
                self.gui_available = False
            else:
                self.gui_available = True
        except:
            self.gui_available = False
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        # Check if it's a jpg file
        if not event.src_path.endswith('.jpg'):
            return
        
        # Wait a moment for the file to be fully written
        time.sleep(0.05)
        
        # Read and validate the frame
        try:
            frame = cv2.imread(event.src_path)
            if frame is not None:
                filename = os.path.basename(event.src_path)
                self.frame_count += 1
                
                # Try to display if GUI available
                if self.gui_available:
                    try:
                        cv2.imshow('Frame Stream', frame)
                        cv2.waitKey(1)
                    except:
                        # GUI failed, just log
                        if self.frame_count == 1:
                            print("ℹ GUI display unavailable, logging frames instead")
                            self.gui_available = False
                
                # Log every 10 frames
                if self.frame_count % 10 == 0:
                    height, width = frame.shape[:2]
                    print(f"Frame #{self.frame_count}: {filename} ({width}x{height})")
                else:
                    print(f"✓ {filename}", end='\r')
            else:
                print(f"✗ Failed to read: {event.src_path}")
        except Exception as e:
            print(f"Error processing frame: {e}")

def main():
    FRAMES_DIR = 'frames'
    
    # Check if frames directory exists
    if not os.path.exists(FRAMES_DIR):
        print(f"Error: {FRAMES_DIR} directory not found")
        return
    
    print("=== Frame Stream Viewer ===")
    print(f"Watching: {os.path.abspath(FRAMES_DIR)}")
    print("Press Ctrl+C to stop")
    print("")
    
    # Create observer
    event_handler = FrameDisplayHandler(FRAMES_DIR)
    observer = Observer()
    observer.schedule(event_handler, FRAMES_DIR, recursive=False)
    observer.start()
    
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        observer.stop()
    
    observer.join()
    try:
        cv2.destroyAllWindows()
    except:
        pass
    print(f"✓ Stopped. Total frames received: {event_handler.frame_count}")

if __name__ == '__main__':
    main()
