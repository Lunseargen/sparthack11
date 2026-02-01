#!/usr/bin/env python3
"""
Video Stream Handler for SparthHack11
Simple utility for handling video stream frames
No vision processing - just video stream management
"""

from pathlib import Path
from datetime import datetime
import json


class VideoStreamHandler:
    """Handles video stream frames without any processing"""
    
    def __init__(self, frames_directory="frames"):
        self.frames_dir = Path(frames_directory)
        self.frames_dir.mkdir(exist_ok=True)
    
    def get_frame_count(self):
        """Get total number of frames captured"""
        frames = sorted(self.frames_dir.glob("frame_*.jpg"))
        return len(frames)
    
    def get_latest_frame_info(self):
        """Get info about the latest frame"""
        frames = sorted(self.frames_dir.glob("frame_*.jpg"))
        if not frames:
            return None
        
        latest = frames[-1]
        return {
            "filename": latest.name,
            "size": latest.stat().st_size,
            "timestamp": datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
        }
    
    def get_all_frames(self):
        """List all captured frames"""
        frames = sorted(self.frames_dir.glob("frame_*.jpg"))
        return [f.name for f in frames]


def main():
    """Main entry point"""
    handler = VideoStreamHandler()
    print(json.dumps({
        "status": "Video stream handler ready",
        "frames_directory": str(handler.frames_dir),
        "frame_count": handler.get_frame_count()
    }))


if __name__ == "__main__":
    main()

