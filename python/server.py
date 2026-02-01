from __future__ import annotations

import io
import json
import os
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock

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


if __name__ == '__main__':
    print('=' * 50)
    print('Starting Flask server on http://localhost:5000')
    print(f'Saving frames to: {os.path.abspath(FRAMES_DIR)}')
    if DETECTION_ENABLED:
        print(f'YOLO enabled: {model is not None}, weights: {WEIGHTS_PATH}')
        print(f'Detection log: {DETECTIONS_LOG}')
    print(f'Max frames on disk: {MAX_FRAMES_ON_DISK}')
    print('Waiting for frames from web browser...')
    print('Press Ctrl+C to stop')
    print('=' * 50)
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f'Server error: {e}')
        print('Server will continue running if possible...')
        import traceback
        traceback.print_exc()from __future__ import annotations

# import io
# import re
# import zipfile
# import json
# import os
# from collections import deque
# from datetime import datetime
# from pathlib import Path
# from threading import Lock
# from urllib import request as urlrequest

# import cv2
# import numpy as np
# from flask import Flask, jsonify, request, Response, send_file
# from flask_cors import CORS
# from PIL import Image

# try:
#     from ultralytics import YOLO
# except Exception:
#     YOLO = None

# app = Flask(__name__)
# CORS(app, supports_credentials=True)  # Enable CORS with credentials

# # Create frames directory if it doesn't exist
# FRAMES_DIR = 'frames'
# if not os.path.exists(FRAMES_DIR):
#     os.makedirs(FRAMES_DIR)

# frame_count = 0

# # ----- YOLO realtime detection (optional) -----
# ROOT_DIR = Path(__file__).resolve().parents[2]
# DEFAULT_WEIGHTS = ROOT_DIR / 'lastest.pt'
# WEIGHTS_PATH = Path(os.environ.get('YOLO_WEIGHTS', str(DEFAULT_WEIGHTS)))
# DETECTIONS_LOG = Path(os.environ.get('DETECTIONS_LOG', str(Path(__file__).parent / 'detections.json')))
# CONF_THRESH = float(os.environ.get('YOLO_CONF', '0.4'))
# IOU_THRESH = float(os.environ.get('YOLO_IOU', '0.5'))
# MAX_DET = int(os.environ.get('YOLO_MAX_DET', '1'))
# LOG_EMPTY = os.environ.get('YOLO_LOG_EMPTY', '0') == '1'
# WRITE_EVERY = int(os.environ.get('YOLO_WRITE_EVERY', '1'))
# MAX_ENTRIES = int(os.environ.get('YOLO_MAX_ENTRIES', '2000'))
# DETECTION_ENABLED = os.environ.get('YOLO_ENABLE', '1') == '1'
# MAX_FRAMES_ON_DISK = int(os.environ.get('MAX_FRAMES_ON_DISK', '300'))
# CORRECTED_LOG = Path(__file__).parent / 'CorrectedLog.json'
# ANNOTATED_FRAMES_DIR = Path(__file__).parent / 'frames_annotated'

# # Keep last N detections in memory
# _detections_buffer = deque(maxlen=MAX_ENTRIES)
# _buffer_lock = Lock()

# if DETECTION_ENABLED and YOLO is not None and WEIGHTS_PATH.exists():
#     try:
#         model = YOLO(str(WEIGHTS_PATH))
#         print(f"YOLO model loaded: {WEIGHTS_PATH}")
#     except Exception as e:
#         model = None
#         print(f"WARNING: Failed to load YOLO model: {e}")
# else:
#     model = None
#     if DETECTION_ENABLED and YOLO is None:
#         print('WARNING: ultralytics not installed, realtime detection disabled.')
#     elif DETECTION_ENABLED and not WEIGHTS_PATH.exists():
#         print(f"WARNING: weights not found at {WEIGHTS_PATH}, realtime detection disabled.")




# def _prune_old_frames():
#     try:
#         frames = sorted(Path(FRAMES_DIR).glob('*.jpg'), key=lambda p: p.stat().st_mtime)
#         if len(frames) <= MAX_FRAMES_ON_DISK:
#             return
#         to_delete = len(frames) - MAX_FRAMES_ON_DISK
#         for p in frames[:to_delete]:
#             try:
#                 p.unlink(missing_ok=True)
#             except Exception:
#                 pass
#     except Exception as e:
#         print(f"WARNING: Failed to prune frames: {e}")

# def _write_detections():
#     rows = list(_detections_buffer)
#     with open(DETECTIONS_LOG, 'w', encoding='utf-8') as f:
#         f.write('[\n')
#         for i, row in enumerate(rows):
#             line = json.dumps(row, ensure_ascii=False)
#             if i < len(rows) - 1:
#                 f.write(f"  {line},\n")
#             else:
#                 f.write(f"  {line}\n")
#         f.write(']\n')


# def compact_detection_ranges(
#     detections_path: Path = DETECTIONS_LOG,
#     output_path: Path | None = None,
# ):
#     """
#     Read detections.json and compact consecutive frames of the same label.

#     Returns a list of dicts like:
#       {"frameRange": "x1-x2", "label": "char"}
#     """
#     try:
#         with open(detections_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#     except Exception as e:
#         print(f"WARNING: Failed to read detections from {detections_path}: {e}")
#         return []

#     def _extract_frame_label(row):
#         if isinstance(row, dict):
#             frame = row.get('frame_count') or row.get('frame')
#             label = row.get('label')
#             return frame, label
#         if isinstance(row, list) and len(row) >= 3:
#             return row[0], row[2]
#         return None, None

#     compacted = []
#     current_label = None
#     range_start = None
#     range_end = None

#     for row in data or []:
#         frame, label = _extract_frame_label(row)
#         if frame is None or label is None:
#             continue

#         try:
#             frame = int(frame)
#         except Exception:
#             continue

#         if current_label is None:
#             current_label = label
#             range_start = frame
#             range_end = frame
#             continue

#         if label == current_label:
#             if frame > range_end:
#                 range_end = frame
#             continue

#         compacted.append({
#             'frameRange': f"{range_start}-{range_end}",
#             'label': current_label,
#         })
#         current_label = label
#         range_start = frame
#         range_end = frame

#     if current_label is not None:
#         compacted.append({
#             'frameRange': f"{range_start}-{range_end}",
#             'label': current_label,
#         })

#     if output_path is None:
#         output_path = detections_path.parent / 'compactedLog.json'

#     try:
#         with open(output_path, 'w', encoding='utf-8') as f:
#             json.dump(compacted, f, ensure_ascii=False, indent=2)
#             f.write('\n')
#     except Exception as e:
#         print(f"WARNING: Failed to write compacted log to {output_path}: {e}")

#     return compacted


# def _extract_words_from_compacted(compacted: list[dict]) -> list[dict]:
#     """
#     Extract word entries from compacted detection ranges.
    
#     Treats 'sp', 'space', '_', 'fn', 'none' as word separators.
#     Each word entry contains the frame range and the raw letter sequence.
#     """
#     words = []
#     current = []
#     word_start = None
#     word_end = None

#     # Labels that indicate word boundaries (space, no hand detected, etc.)
#     separator_labels = {'sp', 'space', '_', 'fn', 'none'}

#     for entry in compacted:
#         label = entry.get('label')
#         frame_range = entry.get('frameRange', '')
#         if not label or not frame_range:
#             continue

#         try:
#             start_str, end_str = frame_range.split('-', 1)
#             start_frame = int(start_str)
#             end_frame = int(end_str)
#         except Exception:
#             continue

#         if label in separator_labels:
#             # End current word if there is one
#             if current:
#                 words.append({
#                     'frameRange': f"{word_start}-{word_end}",
#                     'raw': ''.join(current),
#                 })
#                 current = []
#                 word_start = None
#                 word_end = None
#             continue

#         # It's an actual letter label
#         if word_start is None:
#             word_start = start_frame
#         word_end = end_frame
#         current.append(label)

#     if current:
#         words.append({
#             'frameRange': f"{word_start}-{word_end}",
#             'raw': ''.join(current),
#         })

#     return words


# # Common English words dictionary for matching ASL letter sequences
# COMMON_WORDS = {
#     # 1-letter
#     'a', 'i',
#     # 2-letter
#     'am', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 'hi', 'if', 'in',
#     'is', 'it', 'me', 'my', 'no', 'of', 'ok', 'on', 'or', 'so', 'to', 'up',
#     'us', 'we',
#     # 3-letter
#     'all', 'and', 'any', 'are', 'ask', 'bad', 'big', 'boy', 'but', 'buy',
#     'can', 'car', 'cat', 'dad', 'day', 'did', 'dog', 'eat', 'end', 'eye',
#     'far', 'few', 'for', 'fun', 'get', 'god', 'got', 'guy', 'had', 'has',
#     'her', 'him', 'his', 'hot', 'how', 'its', 'job', 'joy', 'just', 'keep',
#     'key', 'kid', 'let', 'lot', 'man', 'may', 'mom', 'mrs', 'new', 'not',
#     'now', 'off', 'old', 'one', 'our', 'out', 'own', 'pay', 'put', 'ran',
#     'run', 'sad', 'sat', 'saw', 'say', 'see', 'set', 'she', 'sit', 'six',
#     'son', 'ten', 'the', 'too', 'top', 'try', 'two', 'use', 'war', 'was',
#     'way', 'who', 'why', 'win', 'won', 'yes', 'yet', 'you',
#     # 4-letter
#     'able', 'also', 'back', 'ball', 'bank', 'been', 'best', 'bill', 'body',
#     'book', 'both', 'call', 'came', 'come', 'cool', 'city', 'dark', 'data',
#     'deal', 'does', 'done', 'door', 'down', 'each', 'east', 'easy', 'else',
#     'even', 'ever', 'face', 'fact', 'fall', 'feel', 'find', 'fire', 'food',
#     'four', 'free', 'from', 'full', 'game', 'gave', 'girl', 'give', 'glad',
#     'goes', 'gone', 'good', 'great', 'grow', 'hair', 'half', 'hand', 'hard',
#     'have', 'head', 'hear', 'help', 'here', 'high', 'hold', 'home', 'hope',
#     'hour', 'idea', 'into', 'just', 'keep', 'kind', 'knew', 'know', 'land',
#     'last', 'late', 'left', 'less', 'life', 'like', 'line', 'live', 'long',
#     'look', 'love', 'made', 'main', 'make', 'many', 'meet', 'mind', 'more',
#     'most', 'move', 'much', 'must', 'name', 'near', 'need', 'next', 'nice',
#     'none', 'once', 'only', 'open', 'over', 'paid', 'part', 'pass', 'past',
#     'pick', 'plan', 'play', 'read', 'real', 'rest', 'right', 'road', 'room',
#     'safe', 'said', 'same', 'save', 'seen', 'self', 'send', 'show', 'side',
#     'sign', 'size', 'some', 'soon', 'stay', 'stop', 'such', 'sure', 'take',
#     'talk', 'tell', 'text', 'than', 'that', 'them', 'then', 'they', 'this',
#     'thus', 'time', 'told', 'took', 'tree', 'true', 'turn', 'type', 'upon',
#     'used', 'user', 'very', 'view', 'wait', 'walk', 'wall', 'want', 'week',
#     'well', 'went', 'were', 'west', 'what', 'when', 'will', 'with', 'word',
#     'work', 'year', 'your',
#     # 5-letter
#     'about', 'above', 'after', 'again', 'being', 'below', 'black', 'bring',
#     'bring', 'cause', 'child', 'clear', 'close', 'could', 'doing', 'early',
#     'every', 'field', 'first', 'found', 'front', 'given', 'going', 'great',
#     'green', 'group', 'happy', 'heard', 'heart', 'hello', 'house', 'human',
#     'known', 'large', 'later', 'learn', 'leave', 'level', 'light', 'little',
#     'local', 'might', 'money', 'month', 'never', 'night', 'often', 'order',
#     'other', 'party', 'peace', 'place', 'plant', 'point', 'power', 'press',
#     'quite', 'ready', 'right', 'river', 'round', 'seems', 'shall', 'short',
#     'shown', 'since', 'small', 'sorry', 'sound', 'south', 'space', 'start',
#     'state', 'still', 'study', 'table', 'taken', 'thank', 'thanks', 'their',
#     'there', 'these', 'thing', 'think', 'third', 'those', 'three', 'today',
#     'under', 'until', 'using', 'value', 'voice', 'watch', 'water', 'white',
#     'whole', 'woman', 'women', 'world', 'would', 'write', 'wrong', 'young',
#     # 6+ letter common words
#     'always', 'around', 'become', 'before', 'better', 'called', 'change',
#     'coming', 'enough', 'family', 'friend', 'having', 'itself', 'little',
#     'making', 'matter', 'minute', 'moment', 'mother', 'number', 'people',
#     'person', 'please', 'rather', 'really', 'reason', 'school', 'should',
#     'simple', 'social', 'system', 'things', 'though', 'together', 'toward',
#     'wanted', 'without', 'working', 'because', 'between', 'brought', 'country',
#     'during', 'example', 'father', 'general', 'getting', 'government', 'however',
#     'looking', 'morning', 'nothing', 'problem', 'program', 'several', 'something',
#     'special', 'started', 'through', 'understand', 'whether', 'another',
# }

# # Build index by length and first letter for faster lookup
# _WORDS_BY_LEN: dict[int, set[str]] = {}
# for _w in COMMON_WORDS:
#     _WORDS_BY_LEN.setdefault(len(_w), set()).add(_w)


# def _levenshtein(s1: str, s2: str) -> int:
#     """Compute Levenshtein edit distance between two strings."""
#     if len(s1) < len(s2):
#         s1, s2 = s2, s1
#     if not s2:
#         return len(s1)
#     prev_row = list(range(len(s2) + 1))
#     for i, c1 in enumerate(s1):
#         curr_row = [i + 1]
#         for j, c2 in enumerate(s2):
#             insertions = prev_row[j + 1] + 1
#             deletions = curr_row[j] + 1
#             substitutions = prev_row[j] + (c1 != c2)
#             curr_row.append(min(insertions, deletions, substitutions))
#         prev_row = curr_row
#     return prev_row[-1]


# def _match_word(raw: str, max_distance: int = 2) -> str:
#     """
#     Find the best matching English word for a raw ASL letter sequence.
    
#     Uses Levenshtein distance to find close matches within the allowed distance.
#     Returns the original raw string if no good match is found.
#     """
#     raw_lower = raw.lower()
#     raw_len = len(raw_lower)
    
#     # If raw is already a word, return it
#     if raw_lower in COMMON_WORDS:
#         return raw_lower
    
#     best_match = None
#     best_dist = max_distance + 1
    
#     # Search words of similar length (±max_distance)
#     for length in range(max(1, raw_len - max_distance), raw_len + max_distance + 1):
#         candidates = _WORDS_BY_LEN.get(length, set())
#         for word in candidates:
#             dist = _levenshtein(raw_lower, word)
#             if dist < best_dist:
#                 best_dist = dist
#                 best_match = word
#             if dist == 0:
#                 return word
    
#     if best_match and best_dist <= max_distance:
#         return best_match
    
#     return raw


# def generate_corrected_log(
#     detections_path: Path = DETECTIONS_LOG,
#     compacted_path: Path | None = None,
#     output_path: Path = CORRECTED_LOG,
# ):
#     compacted = compact_detection_ranges(detections_path, compacted_path)
#     word_entries = _extract_words_from_compacted(compacted)
#     corrected = []

#     for word in word_entries:
#         raw = word.get('raw', '')
#         if not raw:
#             continue
        
#         # Match the raw letter sequence to the closest English word
#         matched = _match_word(raw)

#         corrected.append({
#             'frame': word['frameRange'],
#             'string': matched,
#         })

#     try:
#         with open(output_path, 'w', encoding='utf-8') as f:
#             json.dump(corrected, f, ensure_ascii=False, indent=2)
#             f.write('\n')
#     except Exception as e:
#         print(f"WARNING: Failed to write corrected log to {output_path}: {e}")

#     return corrected


# def _load_corrected_ranges(path: Path = CORRECTED_LOG) -> list[dict]:
#     try:
#         with open(path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#         return data if isinstance(data, list) else []
#     except Exception as e:
#         print(f"WARNING: Failed to read corrected log from {path}: {e}")
#         return []


# def _index_frames(frames_dir: Path) -> dict[int, Path]:
#     pattern = re.compile(r"frame_(\d+)_")
#     index = {}
#     for frame_path in frames_dir.glob('frame_*.jpg'):
#         match = pattern.search(frame_path.name)
#         if not match:
#             continue
#         try:
#             frame_num = int(match.group(1))
#         except ValueError:
#             continue
#         index[frame_num] = frame_path
#     return index


# def annotate_frames_from_corrected(
#     frames_dir: Path = Path(FRAMES_DIR),
#     corrected_path: Path = CORRECTED_LOG,
#     output_dir: Path = ANNOTATED_FRAMES_DIR,
# ):
#     output_dir.mkdir(parents=True, exist_ok=True)
#     corrected = _load_corrected_ranges(corrected_path)
#     frame_index = _index_frames(frames_dir)
#     annotated_count = 0

#     for entry in corrected:
#         frame_range = entry.get('frame') or entry.get('frameRange')
#         text = entry.get('string') or entry.get('label') or ''
#         if not frame_range or not text:
#             continue
#         try:
#             start_str, end_str = frame_range.split('-', 1)
#             start_frame = int(start_str)
#             end_frame = int(end_str)
#         except Exception:
#             continue

#         for frame_num in range(start_frame, end_frame + 1):
#             frame_path = frame_index.get(frame_num)
#             if not frame_path or not frame_path.exists():
#                 continue
#             img = cv2.imread(str(frame_path))
#             if img is None:
#                 continue

#             h, w = img.shape[:2]
#             font_scale = max(0.6, min(1.2, w / 800))
#             thickness = 2
#             margin = 20
#             text_pos = (margin, h - margin)

#             cv2.putText(
#                 img,
#                 text,
#                 text_pos,
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 font_scale,
#                 (0, 255, 0),
#                 thickness,
#                 cv2.LINE_AA,
#             )

#             out_path = output_dir / frame_path.name
#             cv2.imwrite(str(out_path), img)
#             annotated_count += 1

#     return annotated_count


# def _log_detection(entry: dict):
#     with _buffer_lock:
#         _detections_buffer.append(entry)
#         if entry['frame_count'] % WRITE_EVERY == 0:
#             _write_detections()


# def _run_detection(frame_bgr: np.ndarray, frame_path: str):
#     if model is None:
#         return
#     try:
#         results = model.predict(
#             source=frame_bgr,
#             conf=CONF_THRESH,
#             iou=IOU_THRESH,
#             max_det=MAX_DET,
#             verbose=False,
#         )
#         if not results:
#             if LOG_EMPTY:
#                 _log_detection({
#                     'frame_count': frame_count,
#                     'timestamp': datetime.now().isoformat(),
#                     'label': 'none',
#                     'confidence': 0.0,
#                     'frame_path': frame_path,
#                 })
#             return

#         result = results[0]
#         if result.boxes is not None and len(result.boxes) > 0:
#             confs = result.boxes.conf
#             best_idx = int(confs.argmax().item())
#             best_conf = float(confs[best_idx].item())
#             best_cls = int(result.boxes.cls[best_idx].item())
#             label = result.names.get(best_cls, str(best_cls))
#             _log_detection({
#                 'frame_count': frame_count,
#                 'timestamp': datetime.now().isoformat(),
#                 'label': label,
#                 'confidence': best_conf,
#                 'frame_path': frame_path,
#             })
#         elif LOG_EMPTY:
#             _log_detection({
#                 'frame_count': frame_count,
#                 'timestamp': datetime.now().isoformat(),
#                 'label': 'none',
#                 'confidence': 0.0,
#                 'frame_path': frame_path,
#             })
#     except Exception as e:
#         print(f"WARNING: YOLO detection failed: {e}")


# @app.before_request
# def log_request():
#     """Log all incoming requests"""
#     try:
#         if request.method == 'POST':
#             print(f"[{datetime.now().strftime('%H:%M:%S')}] {request.method} {request.path} - Files: {list(request.files.keys())}")
#     except Exception as e:
#         print(f"Error logging request: {e}")


# @app.route('/send-frame', methods=['POST', 'OPTIONS'])
# def receive_frame():
#     global frame_count

#     # Handle CORS preflight
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         # Check if frame file exists
#         if 'frame' not in request.files:
#             error_msg = 'No frame in request'
#             print(f"ERROR: {error_msg}")
#             return jsonify({'status': 'error', 'message': error_msg}), 400

#         frame_file = request.files['frame']

#         # Read frame data (don't check for empty filename - blobs may not have one)
#         frame_data = frame_file.read()

#         if not frame_data or len(frame_data) == 0:
#             error_msg = 'Empty frame data'
#             print(f"ERROR: {error_msg}")
#             return jsonify({'status': 'error', 'message': error_msg}), 400

#         # Convert bytes to image
#         try:
#             image = Image.open(io.BytesIO(frame_data))
#             frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
#         except Exception as e:
#             error_msg = f"Invalid image data: {str(e)}"
#             print(f"ERROR: {error_msg}")
#             return jsonify({'status': 'error', 'message': error_msg}), 400

#         # Save frame to disk
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
#         frame_path = os.path.join(FRAMES_DIR, f'frame_{frame_count:05d}_{timestamp}.jpg')
#         cv2.imwrite(frame_path, frame)
#         frame_count += 1
#         _prune_old_frames()

#         # Realtime detection (if enabled)
#         _run_detection(frame, frame_path)

#         if frame_count % 30 == 0:  # Log every 30 frames
#             print(f"Received {frame_count} frames...")

#         return jsonify({'status': 'success', 'frame_count': frame_count}), 200
#     except Exception as e:
#         error_msg = f"Server error: {str(e)}"
#         print(f"ERROR: {error_msg}")
#         return jsonify({'status': 'error', 'message': error_msg}), 400


# @app.route('/health', methods=['GET'])
# def health():
#     """Health check endpoint"""
#     return jsonify({'status': 'ok', 'frames': frame_count}), 200


# def _read_json_file(path: Path):
#     try:
#         with open(path, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except Exception:
#         return []


# @app.route('/logs/raw', methods=['GET'])
# def logs_raw():
#     data = _read_json_file(DETECTIONS_LOG)
#     labels = []
#     for row in data:
#         if isinstance(row, dict):
#             label = row.get('label')
#         elif isinstance(row, list) and len(row) >= 3:
#             label = row[2]
#         else:
#             label = None
#         if label:
#             labels.append(label)
#     return jsonify({'labels': ''.join(labels)}), 200


# @app.route('/logs/compacted', methods=['GET'])
# def logs_compacted():
#     compacted = compact_detection_ranges(DETECTIONS_LOG)
#     return jsonify(compacted), 200


# @app.route('/logs/corrected', methods=['GET'])
# def logs_corrected():
#     corrected = generate_corrected_log(DETECTIONS_LOG)
#     return jsonify(corrected), 200


# @app.route('/detections/load', methods=['POST'])
# def detections_load():
#     """Load detection data from JSON payload (for demo/testing)."""
#     try:
#         data = request.get_json(silent=True)
#         if not isinstance(data, list):
#             return jsonify({'error': 'Expected a JSON array'}), 400

#         # Clear the buffer and load new data
#         with _buffer_lock:
#             _detections_buffer.clear()
#             for entry in data:
#                 _detections_buffer.append(entry)
#             _write_detections()

#         return jsonify({'status': 'ok', 'loaded': len(data)}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# @app.route('/detections/clear', methods=['POST'])
# def detections_clear():
#     """Clear all detection data."""
#     try:
#         with _buffer_lock:
#             _detections_buffer.clear()
#             _write_detections()

#         # Also clear the compacted and corrected logs
#         try:
#             compacted_path = DETECTIONS_LOG.parent / 'compactedLog.json'
#             compacted_path.write_text('[]\n', encoding='utf-8')
#         except Exception:
#             pass

#         try:
#             CORRECTED_LOG.write_text('[]\n', encoding='utf-8')
#         except Exception:
#             pass

#         return jsonify({'status': 'ok'}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# @app.route('/video/process', methods=['POST'])
# def video_process():
#     """
#     Process an uploaded MP4 video file frame by frame using YOLO detection.
#     Generates detections.json, compactedLog.json, and CorrectedLog.json.
#     """
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file in request'}), 400

#     video_file = request.files['file']
#     if not video_file.filename:
#         return jsonify({'error': 'No file selected'}), 400

#     if model is None:
#         return jsonify({'error': 'YOLO model not loaded. Check weights path.'}), 500

#     # Save uploaded video to a temp file
#     import tempfile
#     temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
#     try:
#         video_file.save(temp_video.name)
#         temp_video.close()

#         # Open video with OpenCV
#         cap = cv2.VideoCapture(temp_video.name)
#         if not cap.isOpened():
#             return jsonify({'error': 'Failed to open video file'}), 400

#         # Clear existing detections
#         with _buffer_lock:
#             _detections_buffer.clear()

#         frame_idx = 0
#         total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         processed = 0

#         while True:
#             ret, frame_bgr = cap.read()
#             if not ret:
#                 break

#             frame_idx += 1

#             # Run YOLO detection
#             try:
#                 results = model.predict(
#                     source=frame_bgr,
#                     conf=CONF_THRESH,
#                     iou=IOU_THRESH,
#                     max_det=MAX_DET,
#                     verbose=False,
#                 )

#                 entry = None
#                 if results and results[0].boxes is not None and len(results[0].boxes) > 0:
#                     result = results[0]
#                     confs = result.boxes.conf
#                     best_idx = int(confs.argmax().item())
#                     best_conf = float(confs[best_idx].item())
#                     best_cls = int(result.boxes.cls[best_idx].item())
#                     label = result.names.get(best_cls, str(best_cls))
#                     entry = {
#                         'frame_count': frame_idx,
#                         'timestamp': None,
#                         'label': label,
#                         'confidence': best_conf,
#                         'frame_path': f'video_frame_{frame_idx:05d}',
#                     }
#                 elif LOG_EMPTY:
#                     entry = {
#                         'frame_count': frame_idx,
#                         'timestamp': None,
#                         'label': 'none',
#                         'confidence': 0.0,
#                         'frame_path': f'video_frame_{frame_idx:05d}',
#                     }

#                 if entry:
#                     with _buffer_lock:
#                         _detections_buffer.append(entry)
#                     processed += 1

#             except Exception as e:
#                 print(f'WARNING: Detection failed on frame {frame_idx}: {e}')
#                 continue

#         cap.release()

#         # Write detections to file
#         with _buffer_lock:
#             _write_detections()

#         # Generate compacted and corrected logs
#         compacted = compact_detection_ranges(DETECTIONS_LOG)
#         corrected = generate_corrected_log(DETECTIONS_LOG)

#         return jsonify({
#             'status': 'ok',
#             'total_frames': total_frames,
#             'processed': processed,
#             'detections': len(list(_detections_buffer)),
#             'words': len(corrected) if corrected else 0,
#         }), 200

#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': str(e)}), 500
#     finally:
#         # Clean up temp file
#         try:
#             Path(temp_video.name).unlink(missing_ok=True)
#         except Exception:
#             pass


# @app.route('/frames/annotate', methods=['POST'])
# def frames_annotate():
#     annotated = annotate_frames_from_corrected()
#     return jsonify({'annotated': annotated, 'output_dir': str(ANNOTATED_FRAMES_DIR)}), 200


# @app.route('/frames/annotated-zip', methods=['GET'])
# def frames_annotated_zip():
#     if not ANNOTATED_FRAMES_DIR.exists():
#         return jsonify({'error': 'No annotated frames found. Run /frames/annotate first.'}), 404

#     mem_file = io.BytesIO()
#     with zipfile.ZipFile(mem_file, 'w', zipfile.ZIP_DEFLATED) as zf:
#         for frame_path in sorted(ANNOTATED_FRAMES_DIR.glob('frame_*.jpg')):
#             zf.write(frame_path, arcname=frame_path.name)
#     mem_file.seek(0)

#     return send_file(
#         mem_file,
#         mimetype='application/zip',
#         as_attachment=True,
#         download_name='annotated_frames.zip',
#     )


# if __name__ == '__main__':
#     backend_port = int(os.environ.get('BACKEND_PORT', os.environ.get('PORT', '5000')))
#     print('=' * 50)
#     print(f'Starting Flask server on http://localhost:{backend_port}')
#     print(f'Saving frames to: {os.path.abspath(FRAMES_DIR)}')
#     if DETECTION_ENABLED:
#         print(f'YOLO enabled: {model is not None}, weights: {WEIGHTS_PATH}')
#         print(f'Detection log: {DETECTIONS_LOG}')
#     print(f'Max frames on disk: {MAX_FRAMES_ON_DISK}')
#     print('Waiting for frames from web browser...')
#     print('Press Ctrl+C to stop')
#     print('=' * 50)
#     try:
#         app.run(host='0.0.0.0', port=backend_port, debug=False, use_reloader=False, threaded=True)
#     except Exception as e:
#         print(f'Server error: {e}')
#         print('Server will continue running if possible...')
#         import traceback
#         traceback.print_exc()
