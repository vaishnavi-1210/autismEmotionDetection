import sys
import os
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
import traceback

from config import (
    UPLOADS_DIR, PROCESSED_DIR, FEATURES_DIR, RESULTS_DIR,
    HGNN_MODEL_PATH, SEH_DIR, BASE_DIR, EMOTION_CLASSES
)
from utils import save_session_metadata, get_session_info, get_video_info

# Helper for progress tracking
def update_progress(session_id, progress_val, current_stage=""):
    """Update the progress of the current session."""
    try:
        session_metadata = get_session_info(session_id)
        if session_metadata:
            session_metadata["progress"] = progress_val
            if current_stage:
                session_metadata["current_stage"] = current_stage
            save_session_metadata(session_id, session_metadata)
    except Exception as e:
        print(f"DEBUG: Error updating progress: {e}")

def extract_coordinates_from_video(session_id: str) -> bool:
    """Extract coordinates and generate 2D animation."""
    try:
        from maam_compat import extract_coordinates_and_animate

        print(f"[{session_id}] 🎥 AutismIQ: Starting coordinate extraction & animation...")
        update_progress(session_id, 10, "Extracting Landmarks & Generating Animation")
        stage_start = time.time()

        video_path = UPLOADS_DIR / session_id / "video.mp4"
        if not video_path.exists():
            raise Exception(f"Video not found: {video_path}")

        # Extract coordinates AND generate animation
        coord_json, anim_video = extract_coordinates_and_animate(str(video_path), session_id)

        if not coord_json or not anim_video:
            raise Exception("Coordinate extraction or animation generation failed")

        update_progress(session_id, 40, "Landmarks Extracted & Animation Ready")
        print(f"[{session_id}] ✅ Extraction + Animation finished in {time.time() - stage_start:.2f}s")
        return True
    except Exception as e:
        print(f"[{session_id}] ❌ Extraction Stage Failed: {str(e)}")
        traceback.print_exc()
        return False

def extract_bilstm_features(session_id: str) -> bool:
    """Extract 256-D features using the sequence: Preprocess -> LSTM -> FE."""
    try:
        from maam_compat import run_modality_pipeline
        
        print(f"[{session_id}] AutismIQ: Starting modular feature extraction chain...")
        stage_start = time.time()
        features_dir = FEATURES_DIR / session_id
        os.makedirs(features_dir, exist_ok=True)

        # 1. Sequential calls to modality scripts
        update_progress(session_id, 50, "Processing Skeleton")
        skel_feat = run_modality_pipeline('sk', session_id)
        
        update_progress(session_id, 65, "Processing Eye Gaze")
        eye_feat = run_modality_pipeline('eye', session_id)
        
        update_progress(session_id, 80, "Processing Head Gaze")
        head_feat = run_modality_pipeline('head', session_id)

        # 2. Save intermediate features
        np.save(features_dir / "skel_feat.npy", skel_feat)
        np.save(features_dir / "eye_feat.npy", eye_feat)
        np.save(features_dir / "head_feat.npy", head_feat)

        print(f"[{session_id}] Feature chain completed in {time.time() - stage_start:.2f}s")
        return True
    except Exception as e:
        print(f"[{session_id}] Feature Extraction Stage Failed: {str(e)}")
        traceback.print_exc()
        return False

def classify_emotion(session_id: str) -> bool:
    """Final classification using the standalone HGNN model."""
    try:
        from maam_compat import classify_triple_fusion
        
        print(f"[{session_id}] AutismIQ: Starting standalone HGNN classification...")
        update_progress(session_id, 90, "Final Classification")
        stage_start = time.time()

        features_dir = FEATURES_DIR / session_id
        skel_feat = np.load(features_dir / "skel_feat.npy")
        eye_feat = np.load(features_dir / "eye_feat.npy")
        head_feat = np.load(features_dir / "head_feat.npy")

        # 1. Run HGNN Inference (Concat 768-D)
        prediction_idx, probabilities = classify_triple_fusion(skel_feat, eye_feat, head_feat)
        
        # 2. Map to Maam's labels
        class_names = ["IM", "TT", "JA"]
        emotion_class = class_names[prediction_idx]

        confidence_scores = {
            "IM": float(probabilities[0]),
            "TT": float(probabilities[1]),
            "JA": float(probabilities[2])
        }

        # 3. Store Results
        results_dir = RESULTS_DIR / session_id
        os.makedirs(results_dir, exist_ok=True)

        prediction_result = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "emotion_class": emotion_class,
            "confidence_scores": confidence_scores,
            "processing_metadata": {
                "system": "AutismIQ 1.0.0",
                "stages": {
                    "extraction": "Friend's MediaPipe",
                    "features": "Sequential Script Chain (Preprocess -> LSTM -> FE)",
                    "hgnn": "Standalone Reference Implementation"
                },
                "duration": time.time() - stage_start
            }
        }

        with open(results_dir / "prediction.json", 'w') as f:
            json.dump(prediction_result, f, indent=2)

        update_progress(session_id, 100, "Complete")
        print(f"[{session_id}] AutismIQ Analysis Successful: {emotion_class}")
        return True
    except Exception as e:
        print(f"[{session_id}] Classification Stage Failed: {str(e)}")
        traceback.print_exc()
        return False

async def process_video_async(session_id: str):
    """Complete AutismIQ Processing Pipeline"""
    start_time = time.time()
    try:
        # Step 1: Extraction
        if not extract_coordinates_from_video(session_id):
            raise Exception("Coordinate extraction failed")

        # Step 2: Features (Sequential Chain)
        if not extract_bilstm_features(session_id):
            raise Exception("Feature extraction failed")

        # Step 3: Classification
        if not classify_emotion(session_id):
            raise Exception("Classification failed")

        # Finalize Metadata
        session_metadata = get_session_info(session_id)
        if session_metadata:
            session_metadata["status"] = "completed"
            session_metadata["progress"] = 100
            session_metadata["end_time"] = datetime.utcnow().isoformat()
            session_metadata["total_duration"] = time.time() - start_time
            save_session_metadata(session_id, session_metadata)

        print(f"[{session_id}] ✅ Pipeline completed successfully in {time.time() - start_time:.2f}s")

    except Exception as e:
        traceback.print_exc()
        print(f"[{session_id}] ❌ Pipeline error: {str(e)}")
        session_metadata = get_session_info(session_id)
        if session_metadata:
            session_metadata["status"] = "failed"
            session_metadata["error"] = str(e)
            session_metadata["total_duration"] = time.time() - start_time
            save_session_metadata(session_id, session_metadata)
