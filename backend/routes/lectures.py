import uuid
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from backend.services.storage_service import StorageService
from backend.services.pipeline_orchestrator import (
    trigger_background_pipeline,
    trigger_language_generation,
    get_lecture_status,
    PROCESSING_STATUS,
)
from backend.config import UPLOAD_DIR

router = APIRouter(prefix="/api/lectures", tags=["lectures"])

@router.get("")
async def list_lectures():
    """Returns catalog of all processed lectures."""
    lectures = StorageService.list_all_lectures()
    return {"success": True, "count": len(lectures), "lectures": lectures}

@router.get("/{lecture_id}")
async def get_lecture(lecture_id: str):
    """Returns details for a specific lecture."""
    metadata = StorageService.get_lecture_metadata(lecture_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Lecture '{lecture_id}' not found")
    return {"success": True, "lecture": metadata}

@router.get("/{lecture_id}/metadata")
async def get_lecture_event_metadata(lecture_id: str):
    """Returns Contract 3 per-event diagram audio metadata for intelligent player."""
    metadata = StorageService.get_lecture_metadata(lecture_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for lecture '{lecture_id}' not found")
    return {
        "lecture_id": lecture_id,
        "title": metadata.get("title", ""),
        "subject": metadata.get("subject", ""),
        "events": metadata.get("events", [])
    }

@router.get("/{lecture_id}/export-notes")
async def export_lecture_notes(lecture_id: str):
    """
    Generates and returns accessible Markdown study notes for BLV students.
    Includes timestamps, OCR labels, and bilingual diagram audio narratives.
    """
    from fastapi.responses import Response
    metadata = StorageService.get_lecture_metadata(lecture_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Lecture '{lecture_id}' not found")

    title = metadata.get("title", "Untitled Lecture")
    subject = metadata.get("subject", "General STEM")
    description = metadata.get("description", "")
    events = metadata.get("events", [])

    md_lines = [
        f"# EduVision Accessible Study Guide — {title}",
        f"**Subject:** {subject} | **Lecture ID:** `{lecture_id}`",
        f"**Description:** {description}\n",
        "## Summary of Visual Diagram Events",
        f"This lecture contains **{len(events)}** visual diagram descriptions tagged for screen reader navigation and Braille displays.\n",
        "---"
    ]

    for idx, evt in enumerate(events):
        ts = evt.get("timestamp", 0)
        diagram_type = evt.get("diagram_type", "diagram").upper()
        en_narrative = evt.get("explanation_en", "")
        hi_narrative = evt.get("explanation_hi", "")
        ocr_text = evt.get("ocr_text", "None")

        md_lines.extend([
            f"### Event #{idx + 1}: {diagram_type} (Timestamp: {ts}s)",
            f"- **Entry Context:** {evt.get('entry_context', 'Diagram entry detected')}",
            f"- **OCR Extracted Text:** `{ocr_text}`",
            f"- **English Spoken Narrative:** \"{en_narrative}\"",
            f"- **Hindi Spoken Narrative (हिंदी):** \"{hi_narrative}\"\n"
        ])

    md_content = "\n".join(md_lines)
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=accessible_notes_{lecture_id}.md"}
    )

@router.get("/{lecture_id}/status")
async def check_status(lecture_id: str):
    """Check processing status for a lecture."""
    status_info = get_lecture_status(lecture_id)
    return {"success": True, "status_info": status_info}

@router.post("/{lecture_id}/languages")
async def add_language_tracks(lecture_id: str, background_tasks: BackgroundTasks):
    """Generate missing narration tracks for a lecture already in the catalog."""
    metadata = StorageService.get_lecture_metadata(lecture_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Lecture '{lecture_id}' not found")

    current_status = get_lecture_status(lecture_id)
    if current_status.get("status") == "processing":
        raise HTTPException(status_code=409, detail="This lecture is already being processed")

    PROCESSING_STATUS[lecture_id] = {
        "status": "processing", "progress_pct": 0,
        "progress_message": "Queued additional audio-description languages",
        "lecture_id": lecture_id,
    }
    background_tasks.add_task(trigger_language_generation, lecture_id)
    return {
        "success": True,
        "message": "Generating missing audio-description languages.",
        "lecture_id": lecture_id,
        "status_url": f"/api/lectures/{lecture_id}/status",
    }

@router.post("/upload")
async def upload_lecture(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form("Untitled Lecture"),
    subject: str = Form("Physics"),
    description: str = Form("")
):
    """
    Accepts video upload, saves file, and triggers background processing pipeline.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file missing filename")

    lecture_id = f"lec_{str(uuid.uuid4())[:8]}"
    ext = Path(file.filename).suffix or ".mp4"
    video_filename = f"{lecture_id}{ext}"
    saved_video_path = UPLOAD_DIR / video_filename

    try:
        contents = await file.read()
        with open(saved_video_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

    # Seed initial metadata
    initial_metadata = {
        "lecture_id": lecture_id,
        "title": title,
        "subject": subject,
        "description": description,
        "video_url": f"/storage/uploads/{video_filename}",
        "status": "processing",
        "events_count": 0,
        "events": []
    }
    StorageService.save_lecture_metadata(lecture_id, initial_metadata)

    # Trigger async background pipeline execution
    background_tasks.add_task(
        trigger_background_pipeline,
        video_path=str(saved_video_path),
        lecture_id=lecture_id,
        title=title,
        subject=subject,
        description=description
    )

    return {
        "success": True,
        "message": "Lecture uploaded successfully. AI processing started.",
        "lecture_id": lecture_id,
        "status_url": f"/api/lectures/{lecture_id}/status"
    }
