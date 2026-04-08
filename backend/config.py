import os
from pathlib import Path

# Project Metadata
PROJECT_NAME = "AutismIQ"
VERSION = "1.0.0"

# Directory structure
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKEND_DIR = BASE_DIR / "backend"
SEH_DIR = BASE_DIR / "SEH backend code"

# Data directories
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
RESULTS_DIR = DATA_DIR / "results"
ANIMATIONS_DIR = DATA_DIR / "animations"
SESSION_DIR = DATA_DIR / "sessions"
MODELS_DIR = SEH_DIR  # Using provided weights folder

# Video constraints
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_DURATION = 600  # 10 minutes in seconds
ALLOWED_FORMATS = {".mp4", ".avi", ".mov", ".mkv"}

# Model paths (Updated to Maam's files)
HGNN_MODEL_PATH = MODELS_DIR / "triple_fusion_hgnn_final.pth"
# BiLSTM models paths - will use fallback if not found
SK_MODEL_PATH = MODELS_DIR / "bilstm_skeleton_model.pth"
EYE_MODEL_PATH = MODELS_DIR / "bilstm_eye_model.pth"
HEAD_MODEL_PATH = MODELS_DIR / "bilstm_head_model.pth"

# Processing settings
SEQ_LEN = 30
BATCH_SIZE = 1

# Emotion classes from Maam's seh_hgnn.py
EMOTION_CLASSES = ["IM", "TT", "JA"]

# Create necessary directories
for directory in [DATA_DIR, UPLOADS_DIR, PROCESSED_DIR, FEATURES_DIR, RESULTS_DIR, SESSION_DIR]:
    os.makedirs(directory, exist_ok=True)
