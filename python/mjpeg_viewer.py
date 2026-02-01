#!/usr/bin/env python3
"""
MJPEG Stream Viewer
Displays the live MJPEG stream from Flask server with queue info
"""

import cv2
import urllib.request
import numpy as np
import json
from io import BytesIO
from PIL import Image

def get_queue_info(server_url='http://localhost:5000'):
    """Get current MJPEG queue size from server health endpoint"""
    try:
        response = urllib.request.urlopen(f'{server_url}/health', timeout=2)
        data = json.loads(response.read().decode())
        return data.get('queue_size', 0), data.get('max_size', 250)
    except Exception as e:
        return 0, 250

def view_mjpeg_stream(url='http://localhost:5000/stream-mjpeg'):
    """
    Connect to MJPEG stream and display frames with queue info
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
                        
                        # Get queue info from server
                        queue_size, max_size = get_queue_info()
                        
                        # Display frame counter
                        cv2.putText(frame, f'Displayed: {frame_count}', (10, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        
                        # Display queue info
                        cv2.putText(frame, f'Queue: {queue_size}/{max_size} frames', (10, 70), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
                        
                        # Display percentage
                        percentage = (queue_size / max_size) * 100
                        color = (0, 255, 0) if percentage < 80 else (0, 165, 255) if percentage < 95 else (0, 0, 255)
                        cv2.putText(frame, f'{percentage:.1f}%', (10, 110), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        
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
