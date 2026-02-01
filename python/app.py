#!/usr/bin/env python3
"""
Flask Backend Server for SparthHack11
Handles file uploads and video stream frame storage
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Path(__file__).parent.parent / 'uploads'
FRAMES_FOLDER = Path(__file__).parent.parent / 'frames'
AUDIO_FOLDER = Path(__file__).parent.parent / 'audio'
ALLOWED_EXTENSIONS = {'mp4', 'jpg', 'jpeg', 'png', 'mp3'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Create folders if they don't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
FRAMES_FOLDER.mkdir(exist_ok=True)
AUDIO_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return jsonify({"message": "SparthHack11 Backend API"})


# ==================== FILE MANAGEMENT ====================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + filename
        
        file_path = UPLOAD_FOLDER / filename
        file.save(str(file_path))
        
        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename,
            "size": os.path.getsize(file_path)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/list-files', methods=['GET'])
def list_files():
    """List all uploaded files"""
    try:
        files = []
        for file_path in UPLOAD_FOLDER.glob('*'):
            if file_path.is_file() and allowed_file(file_path.name):
                files.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "uploadDate": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                })
        
        return jsonify(files), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file"""
    try:
        filename = secure_filename(filename)
        file_path = UPLOAD_FOLDER / filename
        
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file"""
    try:
        filename = secure_filename(filename)
        file_path = UPLOAD_FOLDER / filename
        
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        file_path.unlink()
        
        return jsonify({"message": "File deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== FRAME STORAGE ====================

@app.route('/api/save-frame', methods=['POST'])
def save_frame():
    """Save a single frame from video stream"""
    try:
        if 'frame' not in request.files:
            return jsonify({"error": "No frame provided"}), 400
        
        frame = request.files['frame']
        frame_number = request.form.get('frameNumber', 0)
        textbox1 = request.form.get('textbox1', '')
        textbox2 = request.form.get('textbox2', '')
        timestamp = request.form.get('timestamp', datetime.now().isoformat())
        
        # Save frame image
        filename = f"frame_{frame_number:04d}.jpg"
        frame_path = FRAMES_FOLDER / filename
        frame.save(str(frame_path))
        
        # Save metadata
        metadata = {
            "frameNumber": int(frame_number),
            "textbox1": textbox1,
            "textbox2": textbox2,
            "timestamp": timestamp
        }
        
        metadata_path = FRAMES_FOLDER / f"frame_{frame_number:04d}_meta.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        return jsonify({"message": "Frame saved"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/save-quiz-frame', methods=['POST'])
def save_quiz_frame():
    """Save a frame from quiz video stream"""
    try:
        if 'frame' not in request.files:
            return jsonify({"error": "No frame provided"}), 400
        
        frame = request.files['frame']
        frame_number = request.form.get('frameNumber', 0)
        question_index = request.form.get('questionIndex', 0)
        timestamp = request.form.get('timestamp', datetime.now().isoformat())
        
        # Save frame with quiz-specific naming
        filename = f"quiz_frame_{frame_number:04d}.jpg"
        frame_path = FRAMES_FOLDER / filename
        frame.save(str(frame_path))
        
        # Save metadata
        metadata = {
            "frameNumber": int(frame_number),
            "questionIndex": int(question_index),
            "timestamp": timestamp
        }
        
        metadata_path = FRAMES_FOLDER / f"quiz_frame_{frame_number:04d}_meta.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        return jsonify({"message": "Quiz frame saved"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== STATIC FILES ====================

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    try:
        filename = secure_filename(filename)
        return send_from_directory(str(AUDIO_FOLDER), filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("SparthHack11 Backend Server Starting...")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Frames folder: {FRAMES_FOLDER}")
    print(f"Audio folder: {AUDIO_FOLDER}")
    
    # Run with debug mode for development
    app.run(debug=True, host='localhost', port=5000)
