import uuid
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from backend.services.storage_service import StorageService
from backend.services.pipeline_orchestrator import (
    trigger_background_pipeline,
    trigger_language_generation,
    get_lecture_status,
    PROCESSING_STATUS,
)
from backend.config import UPLOAD_DIR, MAX_UPLOAD_BYTES

router = APIRouter(prefix="/api/lectures", tags=["lectures"])


class LectureUpdate(BaseModel):
    title: str
    subject: str
    description: str = ""

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


@router.patch("/{lecture_id}")
async def update_lecture(lecture_id: str, update: LectureUpdate):
    """Update the editable catalog details for a completed lecture."""
    metadata = StorageService.get_lecture_metadata(lecture_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Lecture '{lecture_id}' not found")
    if (metadata.get("status") != "completed"
            or get_lecture_status(lecture_id).get("status") == "processing"):
        raise HTTPException(status_code=409, detail="A lecture cannot be edited while it is processing")

    title = update.title.strip()
    subject = update.subject.strip()
    description = update.description.strip()
    if not title or len(title) > 200:
        raise HTTPException(status_code=422, detail="Title must contain 1 to 200 characters")
    if not subject or len(subject) > 100:
        raise HTTPException(status_code=422, detail="Subject must contain 1 to 100 characters")
    if len(description) > 2000:
        raise HTTPException(status_code=422, detail="Description must be 2000 characters or fewer")

    metadata.update({"title": title, "subject": subject, "description": description})
    StorageService.save_lecture_metadata(lecture_id, metadata)
    return {"success": True, "lecture": metadata}


@router.delete("/{lecture_id}")
async def delete_lecture(lecture_id: str):
    """Delete a lecture and its owned video, audio, frames, and metadata."""
    metadata = StorageService.get_lecture_metadata(lecture_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Lecture '{lecture_id}' not found")
    if get_lecture_status(lecture_id).get("status") == "processing":
        raise HTTPException(status_code=409, detail="A lecture cannot be deleted while it is processing")
    if not StorageService.delete_lecture(lecture_id):
        raise HTTPException(status_code=404, detail=f"Lecture '{lecture_id}' not found")
    PROCESSING_STATUS.pop(lecture_id, None)
    return {"success": True, "lecture_id": lecture_id}

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
    if metadata.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Regional language tracks can be added after lecture processing completes")

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
        await file.close()
        raise HTTPException(status_code=400, detail="Uploaded file missing filename")

    lecture_id = f"lec_{str(uuid.uuid4())[:8]}"
    ext = Path(file.filename).suffix.lower()
    if ext not in {".mp4", ".webm", ".mov", ".m4v", ".mkv"}:
        await file.close()
        raise HTTPException(status_code=400, detail="Unsupported video format. Use MP4, WebM, MOV, M4V, or MKV.")
    video_filename = f"{lecture_id}{ext}"
    saved_video_path = UPLOAD_DIR / video_filename

    try:
        with open(saved_video_path, "wb") as f:
            total_bytes = 0
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Video exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit.",
                    )
                f.write(chunk)
        if total_bytes == 0:
            raise HTTPException(status_code=400, detail="Uploaded video file is empty")
    except HTTPException:
        saved_video_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        saved_video_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")
    finally:
        await file.close()

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
