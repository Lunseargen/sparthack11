import argparse
import json
from collections import deque
from pathlib import Path

from ultralytics import YOLO



import cv2


def find_working_camera(max_index=3):
    for idx in range(max_index + 1):
        cap = cv2.VideoCapture(idx)
        ok = cap.isOpened()
        cap.release()
        if ok:
            return idx
    return None

def find_latest_weights():
    runs_dir = Path("runs/detect")
    if not runs_dir.exists():
        return None
    candidates = sorted(runs_dir.glob("train*/weights/best.pt"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def main():
    ap = argparse.ArgumentParser(description="Realtime ASL detector using webcam")
    ap.add_argument("--weights", default=None, help="path to trained weights")
    ap.add_argument("--device", default=0, help="device id or cpu")
    ap.add_argument("--imgsz", type=int, default=640, help="inference image size")
    ap.add_argument("--conf", type=float, default=0.4, help="confidence threshold")
    ap.add_argument("--iou", type=float, default=0.5, help="NMS IoU threshold")
    ap.add_argument("--max-det", type=int, default=1, help="max detections per frame")
    ap.add_argument("--camera", default=0, help="camera index")
    ap.add_argument("--auto-camera", action="store_true", help="auto-pick first working camera")
    ap.add_argument("--out", default="detections.json", help="output JSON file")
    ap.add_argument("--max-entries", type=int, default=100, help="max rows to keep in JSON")
    ap.add_argument(
        "--log-empty",
        action="store_true",
        help="log frames with no detection as [frame, 0.0, 'none']",
    )
    ap.add_argument("--write-every", type=int, default=1, help="write JSON every N frames")
    args = ap.parse_args()

    weights = args.weights
    if not weights:
        latest = find_latest_weights()
        if latest:
            weights = str(latest)
        else:
            raise FileNotFoundError("No weights found. Train first or pass --weights path.")

    model = YOLO(weights)
    if args.auto_camera:
        cam = find_working_camera()
        if cam is None:
            raise RuntimeError('No working camera found')
        args.camera = cam

    buffer = deque(maxlen=args.max_entries)
    frame_idx = 0

    # stream=True yields results frame-by-frame
    for result in model.predict(
        source=args.camera,
        stream=True,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        max_det=args.max_det,
        device=args.device,
        show=True,
    ):
        frame_idx += 1
        entry = None
        if result.boxes is not None and len(result.boxes) > 0:
            confs = result.boxes.conf
            best_idx = int(confs.argmax().item())
            best_conf = float(confs[best_idx].item())
            best_cls = int(result.boxes.cls[best_idx].item())
            label = model.names.get(best_cls, str(best_cls))
            entry = [frame_idx, best_conf, label]
        elif args.log_empty:
            entry = [frame_idx, 0.0, "none"]

        if entry is not None:
            buffer.append(entry)

        if frame_idx % args.write_every == 0:
            rows = list(buffer)
            with open(args.out, "w", encoding="utf-8") as f:
                if not rows:
                    f.write("[]\n")
                else:
                    f.write("[\n")
                    for i, row in enumerate(rows):
                        line = json.dumps(row, ensure_ascii=False)
                        if i < len(rows) - 1:
                            f.write(f"  {line},\n")
                        else:
                            f.write(f"  {line}\n")
                    f.write("]\n")


if __name__ == "__main__":
    main()
