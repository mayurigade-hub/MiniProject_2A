from typing import Dict, Any
from backend.services.storage_service import StorageService
from ai_pipeline.process_lecture import LecturePipeline
from ai_pipeline.explanation.llm_service import LLMExplanationService
from ai_pipeline.tts.tts_service import TTSService
from ai_pipeline.languages import LANGUAGES

# Status tracking in memory
PROCESSING_STATUS: Dict[str, Dict[str, Any]] = {}

def trigger_background_pipeline(
    video_path: str,
    lecture_id: str,
    title: str,
    subject: str,
    description: str
):
    """
    Triggers the AI processing pipeline for a lecture with real-time status & percentage updates.
    """
    PROCESSING_STATUS[lecture_id] = {
        "status": "processing",
        "progress_pct": 5,
        "progress_message": "Initializing video upload and frame extractor",
        "lecture_id": lecture_id
    }

    def update_progress(pct: int, msg: str):
        PROCESSING_STATUS[lecture_id] = {
            "status": "processing",
            "progress_pct": min(80, int(pct * 0.8)),
            "progress_message": msg,
            "lecture_id": lecture_id
        }

    try:
        pipeline = LecturePipeline()
        pipeline.process_video(
            video_path=video_path,
            lecture_id=lecture_id,
            title=title,
            subject=subject,
            description=description,
            progress_callback=update_progress
        )
        # The main pipeline requests every configured language, but external
        # translation/TTS providers can fail for an individual track. Run the
        # same missing-track pass used by the repair endpoint before marking
        # a newly uploaded lecture complete.
        trigger_language_generation(lecture_id, progress_start=80, progress_end=99)
        language_status = PROCESSING_STATUS.get(lecture_id, {})
        if language_status.get("status") == "failed":
            raise RuntimeError(language_status.get("error", "Regional language generation failed"))
        PROCESSING_STATUS[lecture_id] = {
            "status": "completed",
            "progress_pct": 100,
            "progress_message": "Pipeline finished successfully",
            "lecture_id": lecture_id
        }
    except Exception as e:
        print(f"Pipeline error for lecture {lecture_id}: {e}")
        metadata = StorageService.get_lecture_metadata(lecture_id)
        if metadata and metadata.get("status") == "processing":
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            StorageService.save_lecture_metadata(lecture_id, metadata)
        PROCESSING_STATUS[lecture_id] = {
            "status": "failed",
            "progress_pct": 0,
            "error": str(e),
            "lecture_id": lecture_id
        }

def get_lecture_status(lecture_id: str) -> Dict[str, Any]:
    if lecture_id in PROCESSING_STATUS:
        return PROCESSING_STATUS[lecture_id]
    
    # Check if metadata exists on disk
    meta = StorageService.get_lecture_metadata(lecture_id)
    if meta:
        if meta.get("status") == "processing":
            return {
                "status": "failed",
                "progress_pct": 0,
                "progress_message": "Processing stopped before completion",
                "error": "The processing job is no longer active. Please upload the lecture again.",
                "lecture_id": lecture_id,
            }
        if meta.get("status") == "failed":
            return {
                "status": "failed",
                "progress_pct": 0,
                "error": meta.get("error", "Lecture processing failed"),
                "lecture_id": lecture_id,
            }
        return {
            "status": "completed",
            "progress_pct": 100,
            "progress_message": "Completed",
            "lecture_id": lecture_id,
            "events_count": meta.get("events_count", 0)
        }
    
    return {"status": "not_found", "progress_pct": 0, "lecture_id": lecture_id}


def trigger_language_generation(lecture_id: str, progress_start: int = 0, progress_end: int = 99):
    """Add missing language explanations and audio to an already processed lecture."""
    metadata = StorageService.get_lecture_metadata(lecture_id)
    if not metadata:
        PROCESSING_STATUS[lecture_id] = {
            "status": "failed", "progress_pct": 0,
            "error": "Lecture metadata was not found", "lecture_id": lecture_id,
        }
        return

    events = metadata.get("events", [])
    PROCESSING_STATUS[lecture_id] = {
        "status": "processing", "progress_pct": progress_start,
        "progress_message": "Preparing regional audio-description tracks",
        "lecture_id": lecture_id,
    }
    llm_service = LLMExplanationService()
    tts_service = TTSService()

    try:
        for index, event in enumerate(events):
            # Refresh legacy English/Hindi tracks with the selected neural voices,
            # and synthesize any regional tracks this event is still missing.
            missing_codes = [
                code for code in LANGUAGES
                if not event.get(f"audio_{code}") or not event.get(f"explanation_{code}")
            ]
            if missing_codes:
                new_explanations = llm_service.generate_explanations(
                    event.get("vlm_analysis", ""),
                    subject=metadata.get("subject", "General Science"),
                    language_codes=[
                        code for code in missing_codes
                        if not event.get(f"explanation_{code}")
                    ],
                )
                narration = {
                    code: event.get(f"explanation_{code}") or new_explanations.get(code)
                    for code in missing_codes
                }
                narration = {code: text for code, text in narration.items() if text}
                event.update({f"explanation_{code}": text for code, text in new_explanations.items()})
                event.update(tts_service.synthesize_translations(narration, event["event_id"]))

            progress = progress_start + int(
                ((index + 1) / max(1, len(events))) * (progress_end - progress_start)
            )
            PROCESSING_STATUS[lecture_id] = {
                "status": "processing", "progress_pct": progress,
                "progress_message": f"Adding language tracks for diagram {index + 1} of {len(events)}",
                "lecture_id": lecture_id,
            }

        StorageService.save_lecture_metadata(lecture_id, metadata)
        PROCESSING_STATUS[lecture_id] = {
            "status": "completed", "progress_pct": 100,
            "progress_message": "Regional language tracks are ready",
            "lecture_id": lecture_id,
        }
    except Exception as error:
        PROCESSING_STATUS[lecture_id] = {
            "status": "failed", "progress_pct": 0,
            "error": str(error), "lecture_id": lecture_id,
        }
