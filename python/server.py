import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials

# Create frames directory if it doesn't exist
FRAMES_DIR = 'frames'
if not os.path.exists(FRAMES_DIR):
    os.makedirs(FRAMES_DIR)

frame_count = 0

@app.before_request
def log_request():
    """Log all incoming requests"""
    try:
        if request.method == 'POST':
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {request.method} {request.path} - Files: {list(request.files.keys())}")
    except Exception as e:
        print(f"Error logging request: {e}")

@app.route('/send-frame', methods=['POST', 'OPTIONS'])
def receive_frame():
    global frame_count
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Check if frame file exists
        if 'frame' not in request.files:
            error_msg = 'No frame in request'
            print(f"ERROR: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), 400
        
        frame_file = request.files['frame']
        
        # Read frame data (don't check for empty filename - blobs may not have one)
        frame_data = frame_file.read()
        
        if not frame_data or len(frame_data) == 0:
            error_msg = 'Empty frame data'
            print(f"ERROR: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), 400
        
        # Convert bytes to image
        try:
            image = Image.open(io.BytesIO(frame_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            error_msg = f'Invalid image data: {str(e)}'
            print(f"ERROR: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), 400
        
        # Save frame to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        frame_path = os.path.join(FRAMES_DIR, f'frame_{frame_count:05d}_{timestamp}.jpg')
        cv2.imwrite(frame_path, frame)
        frame_count += 1
        
        if frame_count % 30 == 0:  # Log every 30 frames
            print(f"✓ Received {frame_count} frames...")
        
        return jsonify({'status': 'success', 'frame_count': frame_count}), 200
    except Exception as e:
        error_msg = f'Server error: {str(e)}'
        print(f"ERROR: {error_msg}")
        return jsonify({'status': 'error', 'message': error_msg}), 400

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'frames': frame_count}), 200

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Flask server on http://localhost:5000")
    print(f"Saving frames to: {os.path.abspath(FRAMES_DIR)}")
    print("Waiting for frames from web browser...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"Server error: {e}")
        print("Server will continue running if possible...")
        import traceback
        traceback.print_exc()
