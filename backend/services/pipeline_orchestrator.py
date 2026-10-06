import asyncio
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
            "progress_pct": pct,
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
        PROCESSING_STATUS[lecture_id] = {
            "status": "completed",
            "progress_pct": 100,
            "progress_message": "Pipeline finished successfully",
            "lecture_id": lecture_id
        }
    except Exception as e:
        print(f"Pipeline error for lecture {lecture_id}: {e}")
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
        return {
            "status": "completed",
            "progress_pct": 100,
            "progress_message": "Completed",
            "lecture_id": lecture_id,
            "events_count": meta.get("events_count", 0)
        }
    
    return {"status": "not_found", "progress_pct": 0, "lecture_id": lecture_id}


def trigger_language_generation(lecture_id: str):
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
        "status": "processing", "progress_pct": 0,
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
                if code in ("en", "hi") or not event.get(f"audio_{code}")
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

            progress = int(((index + 1) / max(1, len(events))) * 100)
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
