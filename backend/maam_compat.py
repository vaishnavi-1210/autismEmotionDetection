import os
import sys
import importlib.util
from pathlib import Path
import torch
import torch.nn as nn
import numpy as np
import re
import traceback
import subprocess

# Add SEH directory to path to allow imports
BASE_DIR = Path(__file__).resolve().parent.parent
SEH_DIR = BASE_DIR / "SEH backend code"
ROOT_DIR = BASE_DIR

def get_maam_module(name):
    """Dynamically load Maam's script as a module."""
    script_path = SEH_DIR / f"{name}.py"
    if not script_path.exists():
        # Check backend dir for coordinate_extractor
        script_path = BASE_DIR / "backend" / f"{name}.py"
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

    spec = importlib.util.spec_from_file_location(name, str(script_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# --- STANDALONE HGNN ARCHITECTURE (Ref: seh_hgnn.py) ---
class TripleFusionHGNN(nn.Module):
    def __init__(self, in_dim=768, h_dim=256, out_dim=3):
        super().__init__()
        self.hconv1 = nn.Linear(in_dim, h_dim)
        self.hconv2 = nn.Linear(h_dim, h_dim)
        self.classifier = nn.Linear(h_dim, out_dim)

    def forward(self, x, G):
        # x shape: [batch, in_dim]
        # G shape: [batch, batch] 
        x = torch.relu(torch.matmul(G, self.hconv1(x)))
        x = torch.relu(torch.matmul(G, self.hconv2(x)))
        return self.classifier(x)

import subprocess

def run_real_extraction(video_path, output_json):
    """Bridge to run the friend's coordinate extraction logic in an isolated process."""
    try:
        extractor_path = BASE_DIR / "backend" / "coordinate_extractor.py"
        with open(extractor_path, "r") as f:
            code = f.read()
        
        # Robust replacement for video_path
        v_path_str = str(video_path).replace("\\", "\\\\")
        o_json_str = str(output_json).replace("\\", "\\\\")

        modified_code = []
        for line in code.splitlines():
            if line.strip().startswith("video_path="):
                modified_code.append(f'video_path = r"{v_path_str}"')
            elif 'open("output_data2.json", "w")' in line:
                modified_code.append(line.replace('open("output_data2.json", "w")', f'open(r"{o_json_str}", "w")'))
            else:
                modified_code.append(line)
        
        patched_script_path = Path(output_json).parent / "temp_extractor.py"
        with open(patched_script_path, "w") as f:
            f.write("\n".join(modified_code))

        # Run as a SUBPROCESS for isolation
        # This prevents mediapipe from crashing the main FastAPI server
        # and lets us capture stderr directly.
        python_exe = sys.executable or str(BASE_DIR / "backend" / "venv" / "Scripts" / "python.exe")
        
        result = subprocess.run(
            [python_exe, str(patched_script_path)],
            capture_output=True,
            text=True,
            timeout=300 # 5 minute limit
        )
        
        if result.returncode == 0:
            return True
        else:
            # Save the error output for the UI to see
            err_file = Path(output_json).parent / "extraction_error.txt"
            with open(err_file, "w") as ef:
                ef.write(result.stderr or result.stdout or "Subprocess failed with no output")
            print(f"DEBUG: Extraction subprocess failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"DEBUG: Extraction bridge error: {e}")
        return False

def classify_triple_fusion(skel_feat, eye_feat, head_feat):
    """Final Triple Fusion stage using the standalone HGNN definition."""
    from config import HGNN_MODEL_PATH
    
    # 1. Concatenate into 768-D vector
    combined = np.concatenate([skel_feat, eye_feat, head_feat], axis=0) # [768]
    combined_tensor = torch.FloatTensor(combined).unsqueeze(0) # [1, 768]
    
    # 2. Setup Topology (G) - Single node identity
    G = torch.eye(1)
    
    # 3. Load Model Standalone
    model = TripleFusionHGNN().to(torch.device("cpu"))
    if HGNN_MODEL_PATH.exists():
        state_dict = torch.load(HGNN_MODEL_PATH, map_location="cpu")
        model.load_state_dict(state_dict)
    model.eval()
    
    # 4. Inference
    with torch.no_grad():
        output = model(combined_tensor, G)
        probs = torch.softmax(output, dim=1).numpy()[0]
        prediction = int(np.argmax(probs))
        
    return prediction, probs

def run_modality_pipeline(modality, session_id):
    """Executes the strict sequence: Preprocess -> LSTM -> FE."""
    from config import PROCESSED_DIR, MODELS_DIR

    try:
        # 1. PREPROCESS (preprocess.py)
        prep_mod = get_maam_module(f"{modality}_preprocess")
        coord_file = PROCESSED_DIR / session_id / "coordinates.json"

        # Map modality to her exact function names in the scripts
        if modality == 'sk':
            X_clean, _, _ = prep_mod.extract_data_and_label(str(coord_file))
        elif modality == 'eye':
            X_clean, _, _ = prep_mod.extract_gaze_and_label(str(coord_file))
        elif modality == 'head':
            # Head only returns 2 values: series, label
            X_clean, _ = prep_mod.extract_head_gaze(str(coord_file))

        if X_clean is None:
            X_clean = np.zeros((30, 40 if modality=='sk' else 3))

        # Normalization (Matches her script's mean/std logic)
        X_norm = (X_clean - np.mean(X_clean)) / (np.std(X_clean) + 1e-8)
        X_tensor = torch.FloatTensor(X_norm).unsqueeze(0) # [1, 30, dim]

        # 2. LSTM & FE (lstm.py Class + fe.py Logic)
        fe_mod = get_maam_module(f"{modality}_fe")

        name_map = {'sk': 'skeleton', 'eye': 'gaze', 'head': 'head'}
        weights_path = MODELS_DIR / f"bilstm_{name_map[modality]}_model.pth"

        input_dim = 40 if modality == 'sk' else 3

        # Initialize her specific model class name
        if modality == 'head':
            model = fe_mod.HeadGazeBiLSTM(input_size=input_dim).to(torch.device("cpu"))
        else:
            model = fe_mod.BiLSTMClassifier(input_size=input_dim).to(torch.device("cpu"))

        if weights_path.exists():
            try:
                checkpoint = torch.load(weights_path, map_location="cpu")
                state_dict = checkpoint.get("model_state_dict", checkpoint)
                model.load_state_dict(state_dict)
            except Exception as e:
                print(f"[WARN] Could not load model {weights_path}: {e}. Using untrained model.")
        else:
            print(f"[WARN] Model not found at {weights_path}. Using untrained model.")

        model.eval()
        with torch.no_grad():
            # Forward pass in her FE modules
            features = model(X_tensor)
            return features.cpu().numpy()[0]
    except Exception as e:
        print(f"[ERROR] Feature extraction failed for {modality}: {e}")
        # Return zero feature vector as fallback
        return np.zeros(256)


def extract_coordinates_and_animate(video_path, session_id):
    """Extract coordinates from video and generate 2D animation

    Args:
        video_path: Path to input video
        session_id: Session ID for organizing output

    Returns:
        tuple: (coordinates_json_path, animation_video_path) or (None, None) on failure
    """
    from config import PROCESSED_DIR, ANIMATIONS_DIR

    try:
        # Step 1: Extract coordinates using root-level video_to_coordinates.py
        coord_module = __import__('video_to_coordinates', fromlist=['extract_coordinates_from_video'])

        processed_dir = PROCESSED_DIR / session_id
        processed_dir.mkdir(parents=True, exist_ok=True)
        coord_json_path = processed_dir / "coordinates.json"

        print(f"[{session_id}] 📹 Extracting coordinates from video...")
        success = coord_module.extract_coordinates_from_video(str(video_path), str(coord_json_path))

        if not success or not coord_json_path.exists():
            raise Exception("Coordinate extraction failed")

        # Step 2: Generate 2D animation using root-level 2d_animation.py
        anim_module = __import__('2d_animation', fromlist=['generate_2d_animation'])

        anim_dir = ANIMATIONS_DIR / session_id
        anim_dir.mkdir(parents=True, exist_ok=True)
        animation_path = anim_dir / "behavior_animation.mp4"

        print(f"[{session_id}] 🎬 Generating 2D behavior animation...")
        success = anim_module.generate_2d_animation(str(processed_dir), str(animation_path))

        if not success or not animation_path.exists():
            raise Exception("Animation generation failed")

        print(f"[{session_id}] ✅ Animation ready at: {animation_path}")
        return str(coord_json_path), str(animation_path)

    except Exception as e:
        print(f"[{session_id}] ❌ Coordinate extraction/animation error: {e}")
        traceback.print_exc()
        return None, None
