from __future__ import annotations

import io
import json
import os
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

app = Flask(__name__)
CORS(app)

ROOT = Path(__file__).resolve().parent
DETECTIONS_LOG = ROOT / 'detections.json'
WEIGHTS_PATH = Path(r'C:\Users\32876\Downloads\newyolo\lastest.pt')
MAX_ENTRIES = int(os.environ.get('MAX_ENTRIES', '100'))
CONF = float(os.environ.get('YOLO_CONF', '0.6'))
IOU = float(os.environ.get('YOLO_IOU', '0.5'))
MAX_DET = int(os.environ.get('YOLO_MAX_DET', '1'))
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')

buffer = deque(maxlen=MAX_ENTRIES)
model = None
if YOLO is not None and WEIGHTS_PATH.exists():
    model = YOLO(str(WEIGHTS_PATH))


def write_detections():
    with open(DETECTIONS_LOG, 'w', encoding='utf-8') as f:
        json.dump(list(buffer), f, ensure_ascii=False, indent=2)
        f.write('\n')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model_loaded': model is not None}), 200


@app.route('/detect-frame', methods=['POST'])
def detect_frame():
    if model is None:
        return jsonify({'error': 'model not loaded'}), 500

    if 'frame' not in request.files:
        return jsonify({'error': 'frame missing'}), 400

    frame_file = request.files['frame']
    data = frame_file.read()
    if not data:
        return jsonify({'error': 'empty frame'}), 400

    try:
        image = Image.open(io.BytesIO(data))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    except Exception:
        return jsonify({'error': 'invalid image'}), 400

    results = model.predict(
        source=frame,
        conf=CONF,
        iou=IOU,
        max_det=MAX_DET,
        verbose=False,
    )

    label = 'none'
    conf = 0.0
    if results:
        r = results[0]
        if r.boxes is not None and len(r.boxes) > 0:
            confs = r.boxes.conf
            best_idx = int(confs.argmax().item())
            conf = float(confs[best_idx].item())
            best_cls = int(r.boxes.cls[best_idx].item())
            label = r.names.get(best_cls, str(best_cls))
            if str(label).lower() == 'sp':
                label = 'G'

    entry = {
        'frame_count': (buffer[-1]['frame_count'] + 1) if buffer else 1,
        'timestamp': datetime.now().isoformat(),
        'label': label,
        'confidence': conf,
    }
    buffer.append(entry)
    write_detections()

    return jsonify({'status': 'ok', 'label': label, 'confidence': conf}), 200


@app.route('/detections', methods=['GET'])
def detections():
    try:
        limit = int(request.args.get('limit', '4'))
    except Exception:
        limit = 4
    rows = list(buffer)[-limit:]
    return jsonify(rows), 200


@app.route('/reset', methods=['POST'])
def reset():
    buffer.clear()
    write_detections()
    return jsonify({'status': 'ok'}), 200


@app.route('/analyze', methods=['POST'])
def analyze():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get('text', '')).strip()
    if not text:
        return jsonify({'error': 'text missing'}), 400

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'GEMINI_API_KEY not set'}), 500

    try:
        from google import genai
    except Exception as exc:
        return jsonify({'error': 'Gemini SDK not installed', 'detail': str(exc)}), 500

    try:
        print('[analyze] prompt letters:', text)
        client = genai.Client(api_key=api_key)
        prompt = (
            'Guess the actual word or sentence from these letters. '
            'Letters may be missing or noisy. Return only the best guess.\n'
            f'Letters: {text}'
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        result_text = getattr(response, 'text', '') or ''
        print('[analyze] result:', result_text.strip())
        return jsonify({'result': result_text.strip()}), 200
    except Exception as exc:
        print('[analyze] error:', exc)
        return jsonify({'error': 'Gemini request failed', 'detail': str(exc)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('BACKEND_PORT', '5000'))
    print(f"Starting detection server on http://localhost:{port}")
    print(f"Weights: {WEIGHTS_PATH}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
