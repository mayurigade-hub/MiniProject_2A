import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from backend.config import UPLOAD_DIR, AUDIO_DIR, FRAMES_DIR, METADATA_DIR

class StorageService:
    _SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
    _SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_-]{1,100}\.[A-Za-z0-9]{1,10}$")

    @classmethod
    def _safe_id(cls, value: str) -> bool:
        return isinstance(value, str) and bool(cls._SAFE_ID.fullmatch(value))

    @staticmethod
    def save_lecture_metadata(lecture_id: str, data: Dict[str, Any]) -> Path:
        if not StorageService._safe_id(lecture_id):
            raise ValueError("Invalid lecture ID")
        filepath = METADATA_DIR / f"{lecture_id}.json"
        temporary_path = METADATA_DIR / f".{lecture_id}.{uuid.uuid4().hex}.tmp"
        try:
            with open(temporary_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            temporary_path.replace(filepath)
        finally:
            temporary_path.unlink(missing_ok=True)
        return filepath

    @staticmethod
    def get_lecture_metadata(lecture_id: str) -> Optional[Dict[str, Any]]:
        if not StorageService._safe_id(lecture_id):
            return None
        filepath = METADATA_DIR / f"{lecture_id}.json"
        if not filepath.is_file():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def list_all_lectures() -> List[Dict[str, Any]]:
        lectures = []
        for file in METADATA_DIR.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("status", "completed") == "completed":
                        lectures.append(data)
            except Exception:
                continue
        return lectures

    @staticmethod
    def get_lecture_video_path(filename: str) -> Path:
        if not isinstance(filename, str) or not StorageService._SAFE_FILENAME.fullmatch(filename):
            raise ValueError("Invalid video filename")
        return UPLOAD_DIR / filename

    @staticmethod
    def get_lecture_frames_dir(lecture_id: str) -> Path:
        if not StorageService._safe_id(lecture_id):
            raise ValueError("Invalid lecture ID")
        frames_path = FRAMES_DIR / lecture_id
        frames_path.mkdir(parents=True, exist_ok=True)
        return frames_path

    @staticmethod
    def delete_lecture(lecture_id: str) -> bool:
        """Delete a lecture and only the media files owned by its ID."""
        if not StorageService._safe_id(lecture_id):
            return False

        metadata_path = METADATA_DIR / f"{lecture_id}.json"
        if not metadata_path.is_file():
            return False

        metadata = StorageService.get_lecture_metadata(lecture_id) or {}
        video_url = metadata.get("video_url", "")
        video_name = Path(urlparse(video_url).path).name if isinstance(video_url, str) else ""
        if (StorageService._SAFE_FILENAME.fullmatch(video_name)
                and video_name.startswith(f"{lecture_id}.")):
            (UPLOAD_DIR / video_name).unlink(missing_ok=True)

        events = metadata.get("events", [])
        if not isinstance(events, list):
            events = []
        for event in events:
            if not isinstance(event, dict):
                continue
            event_id = event.get("event_id", "")
            if not isinstance(event_id, str) or not event_id.startswith(f"{lecture_id}_"):
                continue
            for key, audio_url in event.items():
                if not key.startswith("audio_") or not isinstance(audio_url, str):
                    continue
                audio_name = Path(urlparse(audio_url).path).name
                if (StorageService._SAFE_FILENAME.fullmatch(audio_name)
                        and audio_name.startswith(f"{event_id}_")):
                    (AUDIO_DIR / audio_name).unlink(missing_ok=True)

        frames_path = FRAMES_DIR / lecture_id
        if frames_path.is_dir():
            shutil.rmtree(frames_path)
        metadata_path.unlink(missing_ok=True)
        return True
