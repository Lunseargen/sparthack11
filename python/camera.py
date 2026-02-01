import cv2
import numpy as np
from flask import Flask, request
from PIL import Image
import io
import os
from datetime import datetime

app = Flask(__name__)

# Create frames directory if it doesn't exist
FRAMES_DIR = 'frames'
if not os.path.exists(FRAMES_DIR):
    os.makedirs(FRAMES_DIR)

frame_count = 0

@app.route('/send-frame', methods=['POST'])
def receive_frame():
    global frame_count
    try:
        frame_data = request.files['frame'].read()
        
        # Convert bytes to image
        image = Image.open(io.BytesIO(frame_data))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Save frame to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        frame_path = os.path.join(FRAMES_DIR, f'frame_{frame_count:05d}_{timestamp}.jpg')
        cv2.imwrite(frame_path, frame)
        frame_count += 1
        
        if frame_count % 30 == 0:  # Log every 30 frames
            print(f"Received {frame_count} frames...")
        
        return {'status': 'success', 'frame_count': frame_count}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 400

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print(f"Saving frames to: {os.path.abspath(FRAMES_DIR)}")
    print("Waiting for frames from web browser...")
    print("Press Ctrl+C to stop")
    app.run(host='localhost', port=5000, debug=False, use_reloader=False)

