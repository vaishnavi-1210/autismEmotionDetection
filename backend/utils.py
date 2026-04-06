import json
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
import cv2
from config import SESSION_DIR, UPLOADS_DIR, MAX_FILE_SIZE, MAX_DURATION, ALLOWED_FORMATS


def validate_video(video_path: Path) -> tuple[bool, str]:
    """Validate video file format and properties"""
    try:
        if not video_path.exists():
            return False, "Video file not found"

        if os.path.getsize(video_path) > MAX_FILE_SIZE:
            return False, f"File size exceeds {MAX_FILE_SIZE / (1024**2):.0f}MB limit"

        if video_path.suffix.lower() not in ALLOWED_FORMATS:
            return False, f"Invalid format. Allowed: {', '.join(ALLOWED_FORMATS)}"

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return False, "Cannot open video file"

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        if duration > MAX_DURATION:
            return False, f"Video exceeds {MAX_DURATION/60:.0f} minutes limit"

        if duration < 10:
            return False, "Video too short (minimum 10 seconds)"

        return True, "Valid"

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def get_session_info(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session metadata"""
    try:
        sessions_file = SESSION_DIR / "metadata.json"

        if not sessions_file.exists():
            return None

        with open(sessions_file, 'r') as f:
            sessions = json.load(f)

        for session in sessions:
            if session.get("session_id") == session_id:
                return session

        return None

    except Exception as e:
        print(f"Error getting session info: {e}")
        return None


def save_session_metadata(session_id: str, metadata: Dict[str, Any]) -> bool:
    """Save or update session metadata"""
    try:
        sessions_file = SESSION_DIR / "metadata.json"

        sessions = []
        if sessions_file.exists():
            with open(sessions_file, 'r') as f:
                sessions = json.load(f)

        sessions = [s for s in sessions if s.get("session_id") != session_id]
        sessions.append(metadata)

        with open(sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)

        return True

    except Exception as e:
        print(f"Error saving session metadata: {e}")
        return False


def load_sessions() -> List[Dict[str, Any]]:
    """Load all sessions"""
    try:
        sessions_file = SESSION_DIR / "metadata.json"

        if not sessions_file.exists():
            return []

        with open(sessions_file, 'r') as f:
            sessions = json.load(f)

        return sessions

    except Exception as e:
        print(f"Error loading sessions: {e}")
        return []


def get_video_info(video_path: Path) -> Optional[Dict[str, Any]]:
    """Get video information"""
    try:
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
            "resolution": f"{width}x{height}"
        }

    except Exception as e:
        print(f"Error getting video info: {e}")
        return None
