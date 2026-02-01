import cv2
import numpy as np
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from PIL import Image
import io
import os
from datetime import datetime
import threading
from collections import deque

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Create frames directory if it doesn't exist
FRAMES_DIR = 'frames'
if not os.path.exists(FRAMES_DIR):
    os.makedirs(FRAMES_DIR)

# MJPEG stream deque - automatically drops oldest frames when new ones exceed max size
MAX_QUEUE_SIZE = 250
frame_queue = deque(maxlen=MAX_QUEUE_SIZE)
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
        # deque with maxlen automatically drops oldest frames when limit exceeded
        with frame_lock:
            frame_queue.append((frame, frame_data))
        
        # Return success (no disk saving)
        return jsonify({'status': 'success', 'queued': True}), 200
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 400

@app.route('/stream-mjpeg')
def stream_mjpeg():
    """MJPEG video stream endpoint"""
    def generate():
        while True:
            try:
                with frame_lock:
                    if frame_queue:
                        frame, frame_data = frame_queue[0]  # Get oldest frame
                        # Manually remove after reading to prevent rapid re-reading
                        frame_queue.popleft()
                    else:
                        continue
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_data)).encode() + b'\r\n\r\n' +
                       frame_data + b'\r\n')
            except Exception as e:
                print(f"Stream error: {e}")
                continue
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    with frame_lock:
        queue_size = len(frame_queue)
    return jsonify({'status': 'ok', 'queue_size': queue_size, 'max_size': MAX_QUEUE_SIZE}), 200

if __name__ == '__main__':
    max_queue_size = 250
    queue_memory_mb = (max_queue_size * 150) / 1024  # ~150KB per frame average
    
    print("=" * 50)
    print("Starting Flask MJPEG server on http://localhost:5000")
    print(f"Saving frames to: {os.path.abspath(FRAMES_DIR)}")
    print(f"MJPEG Queue: {max_queue_size} frames (~{queue_memory_mb:.1f}MB, ~8 seconds at 30fps)")
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
