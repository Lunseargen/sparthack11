#!/usr/bin/env python3
"""
Vision Detection Script for SparthHack11
Detects characters from video frames using computer vision
"""

import os
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import sys

class VisionDetector:
    def __init__(self, frames_directory="frames"):
        self.frames_dir = Path(frames_directory)
        self.frames_dir.mkdir(exist_ok=True)
        
    def detect_character_from_frame(self, frame_path):
        """
        Detect character from a single frame image
        Uses edge detection and contour analysis
        """
        try:
            # Read the frame
            img = cv2.imread(str(frame_path))
            if img is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if len(contours) == 0:
                return "No character detected"
            
            # Sort contours by area
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # Get the largest contour
            largest_contour = contours[0]
            
            # Get contour properties
            area = cv2.contourArea(largest_contour)
            
            # Basic character classification based on contour properties
            detected_char = self._classify_character(largest_contour, area)
            
            return detected_char
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _classify_character(self, contour, area):
        """
        Classify character based on contour shape
        This is a simplified version - a real implementation would use
        machine learning or more sophisticated shape analysis
        """
        # Calculate moments for shape analysis
        moments = cv2.moments(contour)
        
        if moments['m00'] == 0:
            return "Unknown"
        
        # Calculate centroid
        cx = int(moments['m10'] / moments['m00'])
        cy = int(moments['m01'] / moments['m00'])
        
        # Get convex hull
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        
        # Calculate solidity
        solidity = float(area) / hull_area if hull_area > 0 else 0
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h if h > 0 else 0
        
        # Simple classification rules
        if aspect_ratio > 2:
            return "I or L"
        elif aspect_ratio < 0.5:
            return "T or I"
        elif solidity > 0.9:
            return "O or C"
        elif solidity > 0.7:
            return "S or Z"
        else:
            return "A to Z"
    
    def detect_from_latest_frame(self):
        """Detect character from the latest frame in the frames directory"""
        frames = sorted(self.frames_dir.glob("*.jpg"))
        
        if not frames:
            return "No frames found"
        
        latest_frame = frames[-1]
        return self.detect_character_from_frame(latest_frame)
    
    def batch_detect(self):
        """Detect characters from all frames and save results"""
        results = []
        frames = sorted(self.frames_dir.glob("*.jpg"))
        
        for frame_path in frames:
            detection = self.detect_character_from_frame(frame_path)
            results.append({
                "frame": str(frame_path.name),
                "detection": detection,
                "timestamp": datetime.now().isoformat()
            })
        
        return results
    
    def save_results(self, results, output_file="detections.json"):
        """Save detection results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {output_file}")


def main():
    """Main entry point"""
    detector = VisionDetector()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "detect_latest":
            result = detector.detect_from_latest_frame()
            print(json.dumps({"detection": result}))
            
        elif command == "batch":
            results = detector.batch_detect()
            detector.save_results(results)
            
        else:
            print("Unknown command")
    else:
        # Default: detect from latest frame
        result = detector.detect_from_latest_frame()
        print(json.dumps({"detection": result}))


if __name__ == "__main__":
    main()
