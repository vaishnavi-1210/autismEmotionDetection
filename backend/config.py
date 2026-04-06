import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
BACKEND_DIR = BASE_DIR / "backend"
SEH_DIR = BASE_DIR / "SEH backend code"

# Data directories
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
RESULTS_DIR = DATA_DIR / "results"
SESSION_DIR = DATA_DIR / "sessions"
MODELS_DIR = DATA_DIR / "models"

# Video constraints
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_DURATION = 600  # 10 minutes in seconds
ALLOWED_FORMATS = {".mp4", ".avi", ".mov", ".mkv"}

# Model paths
BILSTM_MODEL_PATH = MODELS_DIR / "bilstm_model.pth"
HGNN_MODEL_PATH = SEH_DIR / "triple_fusion_hgnn_final.pth"

# Processing settings
SEQ_LEN = 30
BATCH_SIZE = 1

# Emotion classes (to be confirmed)
EMOTION_CLASSES = ["Class_A", "Class_B", "Class_C"]

# Create necessary directories
for directory in [DATA_DIR, UPLOADS_DIR, PROCESSED_DIR, FEATURES_DIR, RESULTS_DIR, SESSION_DIR, MODELS_DIR]:
    os.makedirs(directory, exist_ok=True)
