#!/usr/bin/env python3
"""
Advanced Frame Analysis Demo - SparthHack11
Performs real-time analysis on video frames from JavaScript
Includes motion detection, edge detection, and statistics
"""

import cv2
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import argparse


class FrameAnalyzer:
    def __init__(self, frames_dir="frames"):
        """Initialize frame analyzer"""
        self.frames_dir = Path(frames_dir)
        self.frame_list = []
        self.prev_frame = None
        
        if not self.frames_dir.exists():
            print(f"Error: Frames directory '{frames_dir}' not found!")
            exit(1)
    
    def load_frames(self):
        """Load frames from directory"""
        self.frame_list = sorted(self.frames_dir.glob("frame_*.jpg"))
        quiz_frames = sorted(self.frames_dir.glob("quiz_frame_*.jpg"))
        self.frame_list.extend(quiz_frames)
        
        if not self.frame_list:
            print("No frames found!")
            return False
        
        print(f"Loaded {len(self.frame_list)} frames")
        return True
    
    def analyze_motion(self, frame, prev_frame):
        """Detect motion between frames"""
        if prev_frame is None:
            return 0
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Threshold the difference
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # Count motion pixels
        motion_pixels = cv2.countNonZero(thresh)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        motion_percentage = (motion_pixels / total_pixels) * 100
        
        return motion_percentage
    
    def detect_edges(self, frame):
        """Detect edges in frame using Canny"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_count = cv2.countNonZero(edges)
        return edges, edge_count
    
    def analyze_brightness(self, frame):
        """Analyze frame brightness"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        return brightness
    
    def analyze_contrast(self, frame):
        """Analyze frame contrast"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        return contrast
    
    def count_objects(self, frame):
        """Estimate number of objects using contour detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter small contours
        significant_contours = [c for c in contours if cv2.contourArea(c) > 100]
        
        return len(significant_contours)
    
    def run_analysis(self, show_edges=False, show_motion=False):
        """Run analysis on all frames"""
        if not self.load_frames():
            return
        
        print("\n" + "="*70)
        print("SparthHack11 Frame Analysis Demo")
        print("="*70)
        print("\nAnalyzing frames...\n")
        
        stats = {
            'total_frames': len(self.frame_list),
            'avg_brightness': 0,
            'avg_contrast': 0,
            'avg_motion': 0,
            'avg_edges': 0,
            'avg_objects': 0,
            'frames': []
        }
        
        brightness_values = []
        contrast_values = []
        motion_values = []
        edge_values = []
        object_counts = []
        
        for idx, frame_path in enumerate(self.frame_list):
            frame = cv2.imread(str(frame_path))
            
            if frame is None:
                continue
            
            # Perform analysis
            brightness = self.analyze_brightness(frame)
            contrast = self.analyze_contrast(frame)
            motion = self.analyze_motion(frame, self.prev_frame)
            edges, edge_count = self.detect_edges(frame)
            objects = self.count_objects(frame)
            
            brightness_values.append(brightness)
            contrast_values.append(contrast)
            motion_values.append(motion)
            edge_values.append(edge_count)
            object_counts.append(objects)
            
            frame_info = {
                'frame_number': idx + 1,
                'filename': frame_path.name,
                'brightness': round(brightness, 2),
                'contrast': round(contrast, 2),
                'motion': round(motion, 2),
                'edges': edge_count,
                'objects': objects
            }
            
            stats['frames'].append(frame_info)
            self.prev_frame = frame.copy()
            
            # Print progress
            if (idx + 1) % max(1, len(self.frame_list) // 10) == 0:
                print(f"  Analyzed {idx + 1}/{len(self.frame_list)} frames...")
            
            # Display if requested
            if show_edges or show_motion:
                display_frame = frame.copy()
                h, w = display_frame.shape[:2]
                
                # Add text overlay
                text = f"Frame {idx + 1}/{len(self.frame_list)}"
                cv2.putText(display_frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                if show_edges:
                    text = f"Edges: {edge_count}"
                    cv2.putText(display_frame, text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)
                
                if show_motion:
                    text = f"Motion: {motion:.1f}%"
                    cv2.putText(display_frame, text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)
                
                cv2.imshow("Frame Analysis", display_frame)
                
                key = cv2.waitKey(10) & 0xFF
                if key == ord('q') or key == 27:
                    break
        
        # Calculate statistics
        if brightness_values:
            stats['avg_brightness'] = round(np.mean(brightness_values), 2)
            stats['avg_contrast'] = round(np.mean(contrast_values), 2)
            stats['avg_motion'] = round(np.mean(motion_values), 2)
            stats['avg_edges'] = int(np.mean(edge_values))
            stats['avg_objects'] = round(np.mean(object_counts), 2)
        
        cv2.destroyAllWindows()
        
        # Print results
        print("\n" + "-"*70)
        print("ANALYSIS RESULTS")
        print("-"*70)
        print(f"Total frames analyzed: {stats['total_frames']}")
        print(f"\nAverage Statistics:")
        print(f"  Brightness:  {stats['avg_brightness']:.2f} (0-255)")
        print(f"  Contrast:    {stats['avg_contrast']:.2f}")
        print(f"  Motion:      {stats['avg_motion']:.2f}%")
        print(f"  Edge pixels: {stats['avg_edges']}")
        print(f"  Objects:     {stats['avg_objects']:.1f}")
        
        # Find interesting frames
        print(f"\nMost Important Frames:")
        if stats['frames']:
            sorted_by_motion = sorted(stats['frames'], key=lambda x: x['motion'], reverse=True)
            sorted_by_objects = sorted(stats['frames'], key=lambda x: x['objects'], reverse=True)
            sorted_by_edges = sorted(stats['frames'], key=lambda x: x['edges'], reverse=True)
            
            print(f"  Most motion: {sorted_by_motion[0]['filename']} ({sorted_by_motion[0]['motion']:.1f}%)")
            print(f"  Most objects: {sorted_by_objects[0]['filename']} ({sorted_by_objects[0]['objects']} objects)")
            print(f"  Most edges: {sorted_by_edges[0]['filename']} ({sorted_by_edges[0]['edges']} edges)")
        
        # Save report
        report_path = "frame_analysis_report.json"
        with open(report_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_path}")
        print("-"*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Frame Analysis for SparthHack11",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python python/frame_analyzer_demo.py                    # Analyze frames
  python python/frame_analyzer_demo.py --show-edges       # Show edge detection
  python python/frame_analyzer_demo.py --show-motion      # Show motion between frames
        """
    )
    
    parser.add_argument(
        '--frames-dir',
        default='frames',
        help='Directory containing frames'
    )
    
    parser.add_argument(
        '--show-edges',
        action='store_true',
        help='Display edge detection visualization'
    )
    
    parser.add_argument(
        '--show-motion',
        action='store_true',
        help='Display motion detection visualization'
    )
    
    args = parser.parse_args()
    
    analyzer = FrameAnalyzer(frames_dir=args.frames_dir)
    analyzer.run_analysis(
        show_edges=args.show_edges,
        show_motion=args.show_motion
    )


if __name__ == "__main__":
    main()
