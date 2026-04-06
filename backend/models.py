from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class VideoUploadResponse(BaseModel):
    """Response for video upload"""
    session_id: str
    filename: str
    size: int
    duration: float
    status: str


class SessionStatus(BaseModel):
    """Session status information"""
    session_id: str
    status: str  # uploaded, processing, completed, failed
    created_at: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None


class ProcessingStatus(BaseModel):
    """Processing status details"""
    session_id: str
    status: str
    stage: Optional[str] = None
    progress: Optional[float] = None
    message: str


class ConfidenceScores(BaseModel):
    """Emotion confidence scores"""
    class_a: float
    class_b: float
    class_c: float


class ProcessingMetadata(BaseModel):
    """Processing metadata"""
    upload_time: str
    start_time: str
    end_time: str
    total_duration: float
    stages: Dict[str, float]


class PredictionResult(BaseModel):
    """Emotion prediction result"""
    session_id: str
    timestamp: str
    video_filename: str
    emotion_class: str
    confidence_scores: Dict[str, float]
    processing_metadata: Dict[str, Any]
    model_versions: Optional[Dict[str, str]] = None


class ExportData(BaseModel):
    """Data export request"""
    session_id: str
    format: str  # json or csv
