import math
from pathlib import Path
from typing import List, Dict, Any

class FrameExtractor:
    def __init__(self, target_fps: float = 1.0):
        if target_fps <= 0:
            raise ValueError("target_fps must be greater than zero")
        self.target_fps = target_fps

    def extract_frames(self, video_path: str, output_dir: str) -> List[Dict[str, Any]]:
        """
        Extracts frames at `target_fps` rate from video file.
        Returns List of dicts following Contract 1:
        [ { "frame_path": "frames/frame_001.jpg", "timestamp": 1.0 }, ... ]
        """
        v_path = Path(video_path)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        frames_data = []
        cap = None

        try:
            import cv2
            cap = cv2.VideoCapture(str(v_path))
            if not cap.isOpened():
                raise ValueError(f"Unable to open video file: {video_path}")

            native_fps = cap.get(cv2.CAP_PROP_FPS)
            if not math.isfinite(native_fps) or native_fps <= 0:
                native_fps = 30.0
            frame_interval = int(max(1, native_fps / self.target_fps))

            frame_count = 0
            saved_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_interval == 0:
                    timestamp = round(frame_count / native_fps, 2)
                    frame_filename = f"frame_{saved_count:04d}_{int(timestamp)}s.jpg"
                    frame_filepath = out_dir / frame_filename
                    if not cv2.imwrite(str(frame_filepath), frame):
                        raise OSError(f"Could not write extracted frame: {frame_filepath}")

                    frames_data.append({
                        "frame_path": str(frame_filepath),
                        "relative_path": f"frames/{v_path.stem}/{frame_filename}",
                        "timestamp": timestamp
                    })
                    saved_count += 1

                frame_count += 1

            print(f"Extracted {saved_count} frames from {video_path}")
            if not frames_data:
                raise ValueError(f"No frames could be decoded from video: {video_path}")
        except ImportError as error:
            raise RuntimeError("OpenCV is required to process lecture videos") from error
        except Exception as e:
            raise RuntimeError(f"Frame extraction failed: {e}") from e
        finally:
            if cap is not None:
                cap.release()

        return frames_data
