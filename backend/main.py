import os
import sys
import uuid
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import tempfile

from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import cv2

from config import (
    DATA_DIR, UPLOADS_DIR, PROCESSED_DIR, FEATURES_DIR, RESULTS_DIR, ANIMATIONS_DIR,
    SESSION_DIR, MAX_FILE_SIZE, MAX_DURATION, ALLOWED_FORMATS
)
from models import VideoUploadResponse, SessionStatus, ProcessingStatus, ExportData
from processing import process_video_async
from utils import validate_video, get_session_info, save_session_metadata, load_sessions

app = FastAPI(title="Autism Emotion Detection System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for directory in [UPLOADS_DIR, PROCESSED_DIR, FEATURES_DIR, RESULTS_DIR, ANIMATIONS_DIR, SESSION_DIR]:
    os.makedirs(directory, exist_ok=True)


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "data_dir": str(DATA_DIR)
    }


@app.post("/api/v1/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload video file and create session"""
    try:
        print(f"[UPLOAD] Starting upload for file: {file.filename}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Allowed: {', '.join(ALLOWED_FORMATS)}"
            )

        session_id = str(uuid.uuid4())
        session_dir = UPLOADS_DIR / session_id
        os.makedirs(session_dir, exist_ok=True)
        print(f"[UPLOAD] Created session directory: {session_dir}")

        video_path = session_dir / "video.mp4"

        file_size = 0
        async with aiofiles.open(video_path, 'wb') as f:
            for chunk in iter(lambda: file.file.read(1024 * 1024), b''):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    os.remove(video_path)
                    raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE / (1024**2):.0f}MB limit")
                await f.write(chunk)

        print(f"[UPLOAD] File saved: {video_path} ({file_size} bytes)")

        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0

            if duration > MAX_DURATION:
                cap.release()
                os.remove(video_path)
                raise HTTPException(status_code=400, detail=f"Video exceeds {MAX_DURATION/60:.0f} minutes limit")

            cap.release()
        except Exception as e:
            if os.path.exists(video_path):
                os.remove(video_path)
            raise HTTPException(status_code=400, detail=f"Invalid video file: {str(e)}")

        print(f"[UPLOAD] Video validated: {duration:.2f}s, {fps} fps, {frame_count} frames")

        session_metadata = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "uploaded",
            "video_metadata": {
                "original_filename": file.filename,
                "file_size": file_size,
                "duration": float(duration),
                "format": file_ext
            }
        }

        save_session_metadata(session_id, session_metadata)

        # Automatically start processing in background
        session_metadata["status"] = "processing"
        session_metadata["start_time"] = datetime.utcnow().isoformat()
        save_session_metadata(session_id, session_metadata)
        
        print(f"[UPLOAD] Starting background processing for session: {session_id}")
        background_tasks.add_task(process_video_async, session_id)

        return VideoUploadResponse(
            session_id=session_id,
            filename=file.filename,
            size=file_size,
            duration=float(duration),
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/v1/process/{session_id}")
async def process_video(session_id: str, background_tasks: BackgroundTasks):
    """Start processing pipeline for uploaded video"""
    try:
        session_metadata = get_session_info(session_id)
        if not session_metadata:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_metadata.get("status") == "processing":
            raise HTTPException(status_code=400, detail="Already processing")

        if session_metadata.get("status") == "completed":
            raise HTTPException(status_code=400, detail="Already completed")

        session_metadata["status"] = "processing"
        session_metadata["start_time"] = datetime.utcnow().isoformat()
        save_session_metadata(session_id, session_metadata)

        background_tasks.add_task(process_video_async, session_id)

        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Processing started"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process request failed: {str(e)}")


@app.get("/api/v1/status/{session_id}")
async def get_status(session_id: str):
    """Get processing status for session"""
    try:
        session_metadata = get_session_info(session_id)
        if not session_metadata:
            raise HTTPException(status_code=404, detail="Session not found")

        payload = {
            "session_id": session_id,
            "status": session_metadata.get("status"),
            "created_at": session_metadata.get("created_at"),
            "start_time": session_metadata.get("start_time"),
            "end_time": session_metadata.get("end_time"),
            "error": session_metadata.get("error"),
            "progress": session_metadata.get("progress", 0),
            "current_stage": session_metadata.get("current_stage", "")
        }

        return JSONResponse(
            content=payload,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@app.get("/api/v1/results/{session_id}")
async def get_results(session_id: str):
    """Get emotion classification results"""
    try:
        results_dir = RESULTS_DIR / session_id
        if not results_dir.exists():
            raise HTTPException(status_code=404, detail="Results not found")

        prediction_file = results_dir / "prediction.json"
        if not prediction_file.exists():
            raise HTTPException(status_code=404, detail="Prediction file not found")

        with open(prediction_file, 'r') as f:
            results = json.load(f)

        return JSONResponse(
            content=results,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")


@app.get("/api/v1/sessions")
async def list_sessions():
    """List all sessions"""
    try:
        sessions = load_sessions()
        return {
            "total": len(sessions),
            "sessions": sessions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@app.get("/api/v1/session/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    try:
        session_metadata = get_session_info(session_id)
        if not session_metadata:
            raise HTTPException(status_code=404, detail="Session not found")

        return session_metadata

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@app.get("/api/v1/export/{session_id}")
async def export_results(session_id: str, format: str = "json"):
    """Export results in JSON or CSV format"""
    try:
        results_dir = RESULTS_DIR / session_id
        if not results_dir.exists():
            raise HTTPException(status_code=404, detail="Results not found")

        prediction_file = results_dir / "prediction.json"
        if not prediction_file.exists():
            raise HTTPException(status_code=404, detail="Prediction file not found")

        with open(prediction_file, 'r') as f:
            results = json.load(f)

        if format == "json":
            return FileResponse(
                prediction_file,
                media_type="application/json",
                filename=f"results_{session_id}.json"
            )

        elif format == "csv":
            import csv
            import io

            csv_file = results_dir / "prediction.csv"
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Session ID", results.get("session_id")])
                writer.writerow(["Timestamp", results.get("timestamp")])
                writer.writerow(["Emotion Class", results.get("emotion_class")])

                confidence = results.get("confidence_scores", {})
                for class_name, score in confidence.items():
                    writer.writerow([f"Confidence - {class_name}", f"{score:.4f}"])

                metadata = results.get("processing_metadata", {})
                writer.writerow(["Total Duration (s)", metadata.get("total_duration")])

            return FileResponse(
                csv_file,
                media_type="text/csv",
                filename=f"results_{session_id}.csv"
            )

        else:
            raise HTTPException(status_code=400, detail="Unsupported format")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/api/v1/coordinates/{session_id}")
async def get_coordinates(session_id: str):
    """Download the raw coordinates (landmarks) JSON created by extraction"""
    try:
        coord_file = PROCESSED_DIR / session_id / "coordinates.json"
        if not coord_file.exists():
            raise HTTPException(status_code=404, detail="Coordinates not found")

        return FileResponse(
            coord_file,
            media_type="application/json",
            filename=f"coordinates_{session_id}.json"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve coordinates: {str(e)}")


@app.get("/api/v1/animation/{session_id}")
async def get_animation(session_id: str):
    """Download the 2D behavior animation video"""
    try:
        anim_file = ANIMATIONS_DIR / session_id / "behavior_animation.mp4"
        if not anim_file.exists():
            raise HTTPException(status_code=404, detail="Animation not found")

        return FileResponse(
            anim_file,
            media_type="video/mp4",
            filename=f"behavior_animation_{session_id}.mp4",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve animation: {str(e)}")


@app.get("/api/v1/features/{session_id}")
async def get_features(session_id: str):
    """Download the intermediate features extracted for research purposes"""
    try:
        import shutil
        import zipfile
        
        features_dir = FEATURES_DIR / session_id
        if not features_dir.exists():
            raise HTTPException(status_code=404, detail="Features not found")
            
        # Create a temporary zip of the features folder
        temp_zip = Path(tempfile.gettempdir()) / f"features_{session_id}.zip"
        with zipfile.ZipFile(temp_zip, 'w') as z:
            for f in features_dir.glob("*.npy"):
                z.write(f, f.name)
                
        return FileResponse(
            temp_zip,
            media_type="application/zip",
            filename=f"features_{session_id}.zip"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve features: {str(e)}")


@app.delete("/api/v1/session/{session_id}")
async def delete_session(session_id: str):
    """Delete session and all associated data"""
    try:
        import shutil

        for directory in [UPLOADS_DIR, PROCESSED_DIR, FEATURES_DIR, RESULTS_DIR]:
            session_path = directory / session_id
            if session_path.exists():
                shutil.rmtree(session_path)

        sessions = load_sessions()
        sessions = [s for s in sessions if s.get("session_id") != session_id]

        sessions_file = SESSION_DIR / "metadata.json"
        with open(sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)

        return {
            "session_id": session_id,
            "status": "deleted"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint - redirect to frontend"""
    return {
        "message": "Autism Emotion Detection System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
