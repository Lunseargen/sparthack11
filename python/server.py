import cv2
import numpy as np
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from PIL import Image
import io
import os
from datetime import datetime
import threading
import queue

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Create frames directory if it doesn't exist
FRAMES_DIR = 'frames'
if not os.path.exists(FRAMES_DIR):
    os.makedirs(FRAMES_DIR)

# MJPEG stream queue
frame_queue = queue.Queue(maxsize=30)
frame_count = 0
frame_lock = threading.Lock()

@app.route('/send-mjpeg', methods=['POST', 'OPTIONS'])
def receive_mjpeg_frame():
    """Receive individual frames that get added to MJPEG stream"""
    global frame_count
    
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        if 'frame' not in request.files:
            return jsonify({'status': 'error', 'message': 'No frame in request'}), 400
        
        frame_file = request.files['frame']
        frame_data = frame_file.read()
        
        if not frame_data or len(frame_data) == 0:
            return jsonify({'status': 'error', 'message': 'Empty frame data'}), 400
        
        # Convert JPEG to OpenCV format
        try:
            image = Image.open(io.BytesIO(frame_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Invalid image data: {str(e)}'}), 400
        
        # Add to queue for MJPEG stream
        try:
            frame_queue.put_nowait((frame, frame_data))
        except queue.Full:
            pass  # Drop frame if queue is full
        
        # Save to disk
        with frame_lock:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            frame_path = os.path.join(FRAMES_DIR, f'frame_{frame_count:05d}_{timestamp}.jpg')
            cv2.imwrite(frame_path, frame)
            frame_count += 1
            
            if frame_count % 30 == 0:
                print(f"✓ Received {frame_count} frames...")
        
        return jsonify({'status': 'success', 'frame_count': frame_count}), 200
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 400

@app.route('/stream-mjpeg')
def stream_mjpeg():
    """MJPEG video stream endpoint"""
    def generate():
        while True:
            try:
                frame, frame_data = frame_queue.get(timeout=1)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_data)).encode() + b'\r\n\r\n' +
                       frame_data + b'\r\n')
            except queue.Empty:
                continue
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    with frame_lock:
        count = frame_count
    return jsonify({'status': 'ok', 'frames': count}), 200

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Flask MJPEG server on http://localhost:5000")
    print(f"Saving frames to: {os.path.abspath(FRAMES_DIR)}")
    print("Frame upload endpoint: POST /send-mjpeg")
    print("Stream endpoint: GET /stream-mjpeg")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
