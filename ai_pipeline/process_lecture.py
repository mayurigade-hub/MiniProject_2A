import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.services.frame_extractor import FrameExtractor
from backend.services.storage_service import StorageService
from ai_pipeline.detection.detector import DiagramDetector
from ai_pipeline.detection.event_grouping import EventGrouper
from ai_pipeline.detection.annotator import DiagramAnnotator
from ai_pipeline.ocr.ocr_service import OCRService
from ai_pipeline.vlm.vlm_service import VLMService
from ai_pipeline.explanation.llm_service import LLMExplanationService
from ai_pipeline.tts.tts_service import TTSService
from ai_pipeline.languages import LANGUAGE_CODES

class LecturePipeline:
    def __init__(self):
        self.frame_extractor = FrameExtractor(target_fps=0.5)
        self.detector = DiagramDetector(confidence_threshold=0.35)
        self.grouper = EventGrouper(max_gap_seconds=4.0)
        self.annotator = DiagramAnnotator()
        self.ocr_service = OCRService()
        self.vlm_service = VLMService()
        self.llm_service = LLMExplanationService()
        self.tts_service = TTSService()

    def process_video(
        self,
        video_path: str,
        lecture_id: str,
        title: str = "Untitled Lecture",
        subject: str = "General Science",
        description: str = "",
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Runs full pipeline end to end for a lecture video file.
        Produces Contract 3 final metadata JSON structure.
        """
        print(f"=== Starting EduVision AI Pipeline for Lecture: {lecture_id} ===")
        v_path = Path(video_path)
        if not v_path.is_file():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        frames_dir = StorageService.get_lecture_frames_dir(lecture_id)

        # Step 1: Frame Extraction (Contract 1) - 25% Progress
        if progress_callback: progress_callback(10, "Extracting video frames and timestamps (Contract 1)")
        raw_frames = self.frame_extractor.extract_frames(str(v_path), str(frames_dir))
        
        if not raw_frames:
            mock_frame = frames_dir / "frame_0001_10s.jpg"
            with open(mock_frame, "wb") as f:
                f.write(b"MOCK_IMAGE_DATA")
            raw_frames = [{
                "frame_path": str(mock_frame),
                "timestamp": 10.0
            }]

        # Step 2: Diagram Detection & Region Extraction - 40% Progress
        if progress_callback: progress_callback(30, "Detecting diagram structures & extracting regions")
        detections = []
        for frame_info in raw_frames:
            det = self.detector.is_diagram_frame(frame_info["frame_path"])
            frame_info.update(det)
            detections.append(frame_info)

        # Step 3: Event Grouping (Contract 2) - 50% Progress
        if progress_callback: progress_callback(50, "Grouping consecutive detections into diagram events")
        events = self.grouper.group_detections(detections)
        print(f" -> Found {len(events)} distinct diagram events.")

        # Step 4, 5, 6: OCR, VLM, LLM, TTS per event (Contract 3) - 75% -> 100% Progress
        processed_events = []
        prior_events_context = []

        for idx, event in enumerate(events):
            event_start_pct = 50 + int((idx / max(1, len(events))) * 49)
            event_end_pct = 50 + int(((idx + 1) / max(1, len(events))) * 49)
            def stage_pct(stage):
                return event_start_pct + int((event_end_pct - event_start_pct) * stage / 6)
            event_label = f"Event {idx + 1}/{len(events)}"
            if progress_callback: progress_callback(stage_pct(0), f"{event_label}: preparing diagram")
            
            img_path = event["image"]
            event_key = f"{lecture_id}_evt_{idx + 1:03d}"

            # Bounding Box Annotation (M3.6)
            annotated_path = self.annotator.annotate_frame(
                img_path,
                event.get("bounding_boxes", []),
                label=f"{event.get('diagram_type', 'diagram').upper()}",
                output_path=str(frames_dir / f"annotated_{event_key}.jpg")
            )
            if progress_callback: progress_callback(stage_pct(1), f"{event_label}: extracting text")

            # OCR Text
            ocr_text = self.ocr_service.extract_text(img_path)
            if progress_callback: progress_callback(stage_pct(2), f"{event_label}: analyzing diagram")
            
            # VLM Visual Analysis
            vlm_analysis = self.vlm_service.analyze_diagram(img_path, ocr_text=ocr_text)
            if progress_callback: progress_callback(stage_pct(3), f"{event_label}: writing audio descriptions")

            # Generate audio-description text in the languages available in the player.
            explanations = self.llm_service.generate_explanations(
                vlm_analysis,
                subject=subject,
                prior_events_context=prior_events_context,
                language_codes=LANGUAGE_CODES,
            )
            if progress_callback: progress_callback(stage_pct(4), f"{event_label}: generating speech")
            
            # Track prior context for subsequent events
            prior_events_context.append(f"Event {idx + 1} ({event.get('diagram_type', 'diagram')}): {explanations.get('en', '')[:120]}")

            # Synthesize one track for each successfully generated translation.
            audio_paths = self.tts_service.synthesize_translations(explanations, event_key)
            if progress_callback: progress_callback(stage_pct(5), f"{event_label}: saving results")

            processed_event = {
                "event_id": event_key,
                "timestamp": event["timestamp"],
                "trigger_timestamp": event.get("trigger_timestamp", event["timestamp"]),
                "start_time": event["start_time"],
                "end_time": event["end_time"],
                "diagram_type": event["diagram_type"],
                "diagram_state": event.get("diagram_state", "NEW_DIAGRAM_ENTRY"),
                "entry_context": event.get("entry_context", f"Diagram entry detected at {event['timestamp']}s"),
                "image_url": f"/storage/frames/{lecture_id}/{Path(img_path).name}",
                "annotated_image_url": f"/storage/frames/{lecture_id}/{Path(annotated_path).name}",
                "ocr_text": ocr_text,
                "vlm_analysis": vlm_analysis,
                **{f"explanation_{code}": text for code, text in explanations.items()},
                **audio_paths,
            }
            processed_events.append(processed_event)
            # Brief rate-limit cooldown to prevent HTTP 429 errors during API inference
            time.sleep(0.3)

        final_metadata = {
            "lecture_id": lecture_id,
            "title": title,
            "subject": subject,
            "description": description,
            "video_url": f"/storage/uploads/{v_path.name}",
            "status": "completed",
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "events_count": len(processed_events),
            "events": processed_events
        }

        # Save metadata JSON
        StorageService.save_lecture_metadata(lecture_id, final_metadata)
        if progress_callback: progress_callback(100, "Processing complete")
        print(f"\n=== EduVision Pipeline Complete for {lecture_id}! Metadata saved. ===")

        return final_metadata
