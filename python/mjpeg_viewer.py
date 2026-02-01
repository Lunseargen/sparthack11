#!/usr/bin/env python3
"""
MJPEG Stream Viewer
Displays the live MJPEG stream from Flask server
"""

import cv2
import urllib.request
import numpy as np
from io import BytesIO
from PIL import Image

def view_mjpeg_stream(url='http://localhost:5000/stream-mjpeg'):
    """
    Connect to MJPEG stream and display frames
    """
    print(f"Connecting to MJPEG stream at {url}...")
    
    try:
        # Open the MJPEG stream
        stream = urllib.request.urlopen(url)
        bytes_data = b''
        frame_count = 0
        
        print("🎥 Stream connected! Press 'q' to quit")
        
        while True:
            # Read bytes until we get a complete JPEG frame
            bytes_data += stream.read(1024)
            
            # Find JPEG boundaries
            a = bytes_data.find(b'\xff\xd8')  # JPEG start
            b = bytes_data.find(b'\xff\xd9')  # JPEG end
            
            if a != -1 and b != -1:
                # Extract the JPEG frame
                jpg_data = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                
                try:
                    # Convert JPEG to OpenCV format
                    frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        frame_count += 1
                        
                        # Display frame info
                        cv2.putText(frame, f'Frame: {frame_count}', (10, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # Display the frame
                        cv2.imshow('MJPEG Stream', frame)
                        
                        # Check for quit key
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print(f"\n✓ Closing stream. Total frames displayed: {frame_count}")
                            break
                            
                except Exception as e:
                    print(f"Error processing frame: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Error connecting to stream: {e}")
    finally:
        cv2.destroyAllWindows()

if __name__ == '__main__':
    view_mjpeg_stream()
