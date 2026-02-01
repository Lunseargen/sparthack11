from __future__ import annotations

import io
import re
import zipfile
import json
import os
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock
from urllib import request as urlrequest

import cv2
import numpy as np
from flask import Flask, jsonify, request, Response, send_file
from flask_cors import CORS
from PIL import Image

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials

# Create frames directory if it doesn't exist
FRAMES_DIR = 'frames'
if not os.path.exists(FRAMES_DIR):
    os.makedirs(FRAMES_DIR)

frame_count = 0

# ----- YOLO realtime detection (optional) -----
ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS = ROOT_DIR / 'lastest.pt'
WEIGHTS_PATH = Path(os.environ.get('YOLO_WEIGHTS', str(DEFAULT_WEIGHTS)))
DETECTIONS_LOG = Path(os.environ.get('DETECTIONS_LOG', str(Path(__file__).parent / 'detections.json')))
CONF_THRESH = float(os.environ.get('YOLO_CONF', '0.4'))
IOU_THRESH = float(os.environ.get('YOLO_IOU', '0.5'))
MAX_DET = int(os.environ.get('YOLO_MAX_DET', '1'))
LOG_EMPTY = os.environ.get('YOLO_LOG_EMPTY', '0') == '1'
WRITE_EVERY = int(os.environ.get('YOLO_WRITE_EVERY', '1'))
MAX_ENTRIES = int(os.environ.get('YOLO_MAX_ENTRIES', '2000'))
DETECTION_ENABLED = os.environ.get('YOLO_ENABLE', '1') == '1'
MAX_FRAMES_ON_DISK = int(os.environ.get('MAX_FRAMES_ON_DISK', '300'))
ELEVEN_KEY_PATH = Path(__file__).parent / 'elevenKEY'
GEMINI_KEY_PATH = Path(__file__).parent / 'geminiKEY'
CORRECTED_LOG = Path(__file__).parent / 'CorrectedLog.json'
ELEVEN_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')
ANNOTATED_FRAMES_DIR = Path(__file__).parent / 'frames_annotated'

# Keep last N detections in memory
_detections_buffer = deque(maxlen=MAX_ENTRIES)
_buffer_lock = Lock()

if DETECTION_ENABLED and YOLO is not None and WEIGHTS_PATH.exists():
    try:
        model = YOLO(str(WEIGHTS_PATH))
        print(f"YOLO model loaded: {WEIGHTS_PATH}")
    except Exception as e:
        model = None
        print(f"WARNING: Failed to load YOLO model: {e}")
else:
    model = None
    if DETECTION_ENABLED and YOLO is None:
        print('WARNING: ultralytics not installed, realtime detection disabled.')
    elif DETECTION_ENABLED and not WEIGHTS_PATH.exists():
        print(f"WARNING: weights not found at {WEIGHTS_PATH}, realtime detection disabled.")




def _prune_old_frames():
    try:
        frames = sorted(Path(FRAMES_DIR).glob('*.jpg'), key=lambda p: p.stat().st_mtime)
        if len(frames) <= MAX_FRAMES_ON_DISK:
            return
        to_delete = len(frames) - MAX_FRAMES_ON_DISK
        for p in frames[:to_delete]:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception as e:
        print(f"WARNING: Failed to prune frames: {e}")

def _write_detections():
    rows = list(_detections_buffer)
    with open(DETECTIONS_LOG, 'w', encoding='utf-8') as f:
        f.write('[\n')
        for i, row in enumerate(rows):
            line = json.dumps(row, ensure_ascii=False)
            if i < len(rows) - 1:
                f.write(f"  {line},\n")
            else:
                f.write(f"  {line}\n")
        f.write(']\n')


def compact_detection_ranges(
    detections_path: Path = DETECTIONS_LOG,
    output_path: Path | None = None,
):
    """
    Read detections.json and compact consecutive frames of the same label.

    Returns a list of dicts like:
      {"frameRange": "x1-x2", "label": "char"}
    """
    try:
        with open(detections_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"WARNING: Failed to read detections from {detections_path}: {e}")
        return []

    def _extract_frame_label(row):
        if isinstance(row, dict):
            frame = row.get('frame_count') or row.get('frame')
            label = row.get('label')
            return frame, label
        if isinstance(row, list) and len(row) >= 3:
            return row[0], row[2]
        return None, None

    compacted = []
    current_label = None
    range_start = None
    range_end = None

    for row in data or []:
        frame, label = _extract_frame_label(row)
        if frame is None or label is None:
            continue

        try:
            frame = int(frame)
        except Exception:
            continue

        if current_label is None:
            current_label = label
            range_start = frame
            range_end = frame
            continue

        if label == current_label:
            if frame > range_end:
                range_end = frame
            continue

        compacted.append({
            'frameRange': f"{range_start}-{range_end}",
            'label': current_label,
        })
        current_label = label
        range_start = frame
        range_end = frame

    if current_label is not None:
        compacted.append({
            'frameRange': f"{range_start}-{range_end}",
            'label': current_label,
        })

    if output_path is None:
        output_path = detections_path.parent / 'compactedLog.json'

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(compacted, f, ensure_ascii=False, indent=2)
            f.write('\n')
    except Exception as e:
        print(f"WARNING: Failed to write compacted log to {output_path}: {e}")

    return compacted


def _read_api_key(path: Path) -> str | None:
    try:
        key = path.read_text(encoding='utf-8').strip()
        return key or None
    except Exception as e:
        print(f"WARNING: Failed to read API key from {path}: {e}")
        return None


def _gemini_correct_word(raw_word: str, context: str, api_key: str | None) -> str | None:
    if not api_key:
        return None
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent?key=" + api_key
    )
    prompt = (
        "You correct ASL letter sequences into likely English words. "
        "Return only the corrected word, no punctuation. "
        f"Letters: {raw_word}. Context: {context}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 16},
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urlrequest.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urlrequest.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
        text = (
            resp_data.get('candidates', [{}])[0]
            .get('content', {})
            .get('parts', [{}])[0]
            .get('text', '')
        )
        word = text.strip().split()[0] if text else None
        return word
    except Exception as e:
        print(f"WARNING: Gemini correction failed: {e}")
        return None


def _elevenlabs_correct_word(raw_word: str, context: str, api_key: str | None) -> str | None:
    if not api_key:
        return None
    url = os.environ.get('ELEVENLABS_LLM_URL', 'https://api.elevenlabs.io/v1/llm/completions')
    payload = {
        "prompt": (
            "You correct ASL letter sequences into likely English words. "
            "Return only the corrected word, no punctuation. "
            f"Letters: {raw_word}. Context: {context}"
        ),
        "max_tokens": 16,
        "temperature": 0.2,
    }
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urlrequest.Request(url, data=data, headers=headers)
        with urlrequest.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
        text = resp_data.get('text')
        if not text and 'choices' in resp_data:
            text = resp_data.get('choices', [{}])[0].get('text')
        word = text.strip().split()[0] if text else None
        return word
    except Exception as e:
        print(f"WARNING: ElevenLabs correction failed: {e}")
        return None


def _extract_words_from_compacted(compacted: list[dict]) -> list[dict]:
    words = []
    current = []
    word_start = None
    word_end = None

    for entry in compacted:
        label = entry.get('label')
        frame_range = entry.get('frameRange', '')
        if not label or not frame_range:
            continue

        try:
            start_str, end_str = frame_range.split('-', 1)
            start_frame = int(start_str)
            end_frame = int(end_str)
        except Exception:
            continue

        if label in {'sp', 'space', '_'}:
            if current:
                words.append({
                    'frameRange': f"{word_start}-{word_end}",
                    'raw': ''.join(current),
                })
                current = []
                word_start = None
                word_end = None
            continue

        if label in {'fn', 'none'}:
            continue

        if word_start is None:
            word_start = start_frame
        word_end = end_frame
        current.append(label)

    if current:
        words.append({
            'frameRange': f"{word_start}-{word_end}",
            'raw': ''.join(current),
        })

    return words


def generate_corrected_log(
    detections_path: Path = DETECTIONS_LOG,
    compacted_path: Path | None = None,
    output_path: Path = CORRECTED_LOG,
):
    compacted = compact_detection_ranges(detections_path, compacted_path)
    word_entries = _extract_words_from_compacted(compacted)
    eleven_key = _read_api_key(ELEVEN_KEY_PATH)
    gemini_key = _read_api_key(GEMINI_KEY_PATH)
    corrected = []

    for idx, word in enumerate(word_entries):
        raw = word.get('raw', '')
        if not raw:
            continue
        prev_word = word_entries[idx - 1]['raw'] if idx > 0 else ''
        next_word = word_entries[idx + 1]['raw'] if idx + 1 < len(word_entries) else ''
        context = f"prev={prev_word} next={next_word}".strip()

        gemini_word = _gemini_correct_word(raw, context, gemini_key)
        eleven_word = _elevenlabs_correct_word(raw, context, eleven_key)

        if gemini_word and eleven_word and gemini_word.lower() == eleven_word.lower():
            chosen = gemini_word
        else:
            chosen = gemini_word or eleven_word or raw

        corrected.append({
            'frame': word['frameRange'],
            'string': chosen,
        })

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(corrected, f, ensure_ascii=False, indent=2)
            f.write('\n')
    except Exception as e:
        print(f"WARNING: Failed to write corrected log to {output_path}: {e}")

    return corrected


def _load_corrected_ranges(path: Path = CORRECTED_LOG) -> list[dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"WARNING: Failed to read corrected log from {path}: {e}")
        return []


def _index_frames(frames_dir: Path) -> dict[int, Path]:
    pattern = re.compile(r"frame_(\d+)_")
    index = {}
    for frame_path in frames_dir.glob('frame_*.jpg'):
        match = pattern.search(frame_path.name)
        if not match:
            continue
        try:
            frame_num = int(match.group(1))
        except ValueError:
            continue
        index[frame_num] = frame_path
    return index


def annotate_frames_from_corrected(
    frames_dir: Path = Path(FRAMES_DIR),
    corrected_path: Path = CORRECTED_LOG,
    output_dir: Path = ANNOTATED_FRAMES_DIR,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    corrected = _load_corrected_ranges(corrected_path)
    frame_index = _index_frames(frames_dir)
    annotated_count = 0

    for entry in corrected:
        frame_range = entry.get('frame') or entry.get('frameRange')
        text = entry.get('string') or entry.get('label') or ''
        if not frame_range or not text:
            continue
        try:
            start_str, end_str = frame_range.split('-', 1)
            start_frame = int(start_str)
            end_frame = int(end_str)
        except Exception:
            continue

        for frame_num in range(start_frame, end_frame + 1):
            frame_path = frame_index.get(frame_num)
            if not frame_path or not frame_path.exists():
                continue
            img = cv2.imread(str(frame_path))
            if img is None:
                continue

            h, w = img.shape[:2]
            font_scale = max(0.6, min(1.2, w / 800))
            thickness = 2
            margin = 20
            text_pos = (margin, h - margin)

            cv2.putText(
                img,
                text,
                text_pos,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (0, 255, 0),
                thickness,
                cv2.LINE_AA,
            )

            out_path = output_dir / frame_path.name
            cv2.imwrite(str(out_path), img)
            annotated_count += 1

    return annotated_count


def _log_detection(entry: dict):
    with _buffer_lock:
        _detections_buffer.append(entry)
        if entry['frame_count'] % WRITE_EVERY == 0:
            _write_detections()


def _run_detection(frame_bgr: np.ndarray, frame_path: str):
    if model is None:
        return
    try:
        results = model.predict(
            source=frame_bgr,
            conf=CONF_THRESH,
            iou=IOU_THRESH,
            max_det=MAX_DET,
            verbose=False,
        )
        if not results:
            if LOG_EMPTY:
                _log_detection({
                    'frame_count': frame_count,
                    'timestamp': datetime.now().isoformat(),
                    'label': 'none',
                    'confidence': 0.0,
                    'frame_path': frame_path,
                })
            return

        result = results[0]
        if result.boxes is not None and len(result.boxes) > 0:
            confs = result.boxes.conf
            best_idx = int(confs.argmax().item())
            best_conf = float(confs[best_idx].item())
            best_cls = int(result.boxes.cls[best_idx].item())
            label = result.names.get(best_cls, str(best_cls))
            _log_detection({
                'frame_count': frame_count,
                'timestamp': datetime.now().isoformat(),
                'label': label,
                'confidence': best_conf,
                'frame_path': frame_path,
            })
        elif LOG_EMPTY:
            _log_detection({
                'frame_count': frame_count,
                'timestamp': datetime.now().isoformat(),
                'label': 'none',
                'confidence': 0.0,
                'frame_path': frame_path,
            })
    except Exception as e:
        print(f"WARNING: YOLO detection failed: {e}")


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
            error_msg = f"Invalid image data: {str(e)}"
            print(f"ERROR: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), 400

        # Save frame to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        frame_path = os.path.join(FRAMES_DIR, f'frame_{frame_count:05d}_{timestamp}.jpg')
        cv2.imwrite(frame_path, frame)
        frame_count += 1
        _prune_old_frames()

        # Realtime detection (if enabled)
        _run_detection(frame, frame_path)

        if frame_count % 30 == 0:  # Log every 30 frames
            print(f"Received {frame_count} frames...")

        return jsonify({'status': 'success', 'frame_count': frame_count}), 200
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"ERROR: {error_msg}")
        return jsonify({'status': 'error', 'message': error_msg}), 400


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'frames': frame_count}), 200


def _read_json_file(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


@app.route('/logs/raw', methods=['GET'])
def logs_raw():
    data = _read_json_file(DETECTIONS_LOG)
    labels = []
    for row in data:
        if isinstance(row, dict):
            label = row.get('label')
        elif isinstance(row, list) and len(row) >= 3:
            label = row[2]
        else:
            label = None
        if label:
            labels.append(label)
    return jsonify({'labels': ''.join(labels)}), 200


@app.route('/logs/compacted', methods=['GET'])
def logs_compacted():
    compacted = compact_detection_ranges(DETECTIONS_LOG)
    return jsonify(compacted), 200


@app.route('/logs/corrected', methods=['GET'])
def logs_corrected():
    corrected = generate_corrected_log(DETECTIONS_LOG)
    return jsonify(corrected), 200


@app.route('/tts', methods=['POST'])
def tts():
    payload = request.get_json(silent=True) or {}
    text = (payload.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'text is required'}), 400

    api_key = _read_api_key(ELEVEN_KEY_PATH)
    if not api_key:
        return jsonify({'error': 'API key not found'}), 500

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    body = {
        "text": text,
        "model_id": payload.get('model_id', 'eleven_monolingual_v1'),
        "voice_settings": payload.get('voice_settings', {
            "stability": 0.5,
            "similarity_boost": 0.8,
        }),
    }

    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
    }

    try:
        data = json.dumps(body).encode('utf-8')
        req = urlrequest.Request(url, data=data, headers=headers)
        with urlrequest.urlopen(req, timeout=20) as resp:
            audio_bytes = resp.read()
        return Response(audio_bytes, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'error': f'TTS failed: {e}'}), 502


@app.route('/frames/annotate', methods=['POST'])
def frames_annotate():
    annotated = annotate_frames_from_corrected()
    return jsonify({'annotated': annotated, 'output_dir': str(ANNOTATED_FRAMES_DIR)}), 200


@app.route('/frames/annotated-zip', methods=['GET'])
def frames_annotated_zip():
    if not ANNOTATED_FRAMES_DIR.exists():
        return jsonify({'error': 'No annotated frames found. Run /frames/annotate first.'}), 404

    mem_file = io.BytesIO()
    with zipfile.ZipFile(mem_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for frame_path in sorted(ANNOTATED_FRAMES_DIR.glob('frame_*.jpg')):
            zf.write(frame_path, arcname=frame_path.name)
    mem_file.seek(0)

    return send_file(
        mem_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='annotated_frames.zip',
    )


if __name__ == '__main__':
    backend_port = int(os.environ.get('BACKEND_PORT', os.environ.get('PORT', '5000')))
    print('=' * 50)
    print(f'Starting Flask server on http://localhost:{backend_port}')
    print(f'Saving frames to: {os.path.abspath(FRAMES_DIR)}')
    if DETECTION_ENABLED:
        print(f'YOLO enabled: {model is not None}, weights: {WEIGHTS_PATH}')
        print(f'Detection log: {DETECTIONS_LOG}')
    print(f'Max frames on disk: {MAX_FRAMES_ON_DISK}')
    print('Waiting for frames from web browser...')
    print('Press Ctrl+C to stop')
    print('=' * 50)
    try:
        app.run(host='0.0.0.0', port=backend_port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f'Server error: {e}')
        print('Server will continue running if possible...')
        import traceback
        traceback.print_exc()
