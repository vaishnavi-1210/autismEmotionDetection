import os
import json
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.utils import resample, shuffle

# ================= CONFIGURATION =================
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_JSON_DIR = str(DATA_DIR / "dream_dataset")
SAVE_FOLDER = str(DATA_DIR / "processed" / "dream_gaze")
DIAGNOSTIC_DIR = str(DATA_DIR / "processed" / "diagnostics")  # Added diagnostic folder
GAZE_FEATURES = ['rx', 'ry', 'rz'] 

SEQ_LEN = 30  
BATCH_SIZE = 64
LABEL_MAP = {"IM": 0, "TT": 1, "JA": 2} 
# =================================================

os.makedirs(SAVE_FOLDER, exist_ok=True)
os.makedirs(DIAGNOSTIC_DIR, exist_ok=True)

def extract_gaze_and_label(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        task_info = data.get('task', {})
        ability = task_info.get('ability') or data.get('condition')
        ability_str = str(ability).upper() if ability else "UNKNOWN"

        final_label = None
        for key in LABEL_MAP.keys():
            if key in ability_str:
                final_label = LABEL_MAP[key]
                break

        if final_label is None: return None, None, "Unknown Task"

        gaze_data = data.get('eye_gaze', {})
        if not gaze_data: return None, None, "No Gaze Data"

        all_series = []
        for feat in GAZE_FEATURES:
            vals = gaze_data.get(feat, [])
            if not vals: return None, None, f"Empty: {feat}"
            all_series.append([v if v is not None else np.nan for v in vals])

        series_np = np.array(all_series).T
        clean_series = series_np[~np.isnan(series_np).any(axis=1)]

        if clean_series.shape[0] < SEQ_LEN:
            return None, None, f"Too Short"

        return clean_series[:SEQ_LEN, :].astype(np.float32), final_label, "Success"

    except Exception as e:
        return None, None, f"Error: {str(e)}"

def extract_gaze_features(file_path):
    """Inference-only: Extract eye gaze features without label dependency."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        gaze_data = data.get('eye_gaze', {})
        if not gaze_data:
            raise Exception("No Gaze Data")

        all_series = []
        for feat in GAZE_FEATURES:
            vals = gaze_data.get(feat, [])
            # Truncate to SEQ_LEN or pad with zeros
            vals = (vals[:SEQ_LEN] if len(vals) >= SEQ_LEN else vals + [0] * (SEQ_LEN - len(vals)))
            all_series.append([v if v is not None else 0 for v in vals])

        series_np = np.array(all_series, dtype=np.float32).T

        if series_np.shape[1] != 3:
            raise Exception(f"Invalid feature size: expected 3, got {series_np.shape[1]}")

        if series_np.shape[0] != SEQ_LEN:
            raise Exception(f"Invalid sequence length: expected {SEQ_LEN}, got {series_np.shape[0]}")

        return series_np.astype(np.float32)
    except Exception as e:
        raise Exception(f"[EYE] Feature extraction failed: {str(e)}")

def generate_visualizations(y_raw, y_bal, x_bal):
    """Generates plots to verify data distribution and normalization."""
    plt.figure(figsize=(12, 5))

    # Plot 1: Class Balance (Before vs After)
    plt.subplot(1, 2, 1)
    orig_counts = Counter(y_raw)
    bal_counts = Counter(y_bal)
    
    classes = list(LABEL_MAP.keys())
    x = np.arange(len(classes))
    plt.bar(x - 0.2, [orig_counts.get(i, 0) for i in range(3)], 0.4, label='Original')
    plt.bar(x + 0.2, [bal_counts.get(i, 0) for i in range(3)], 0.4, label='Balanced')
    plt.xticks(x, classes)
    plt.title("Class Distribution Balancing")
    plt.legend()

    # Plot 2: Feature Distribution (Normalization Check)
    plt.subplot(1, 2, 2)
    for i, feat in enumerate(GAZE_FEATURES):
        sns.kdeplot(x_bal[:, :, i].flatten(), label=feat)
    plt.title("Normalized Feature Distributions (Z-score)")
    plt.xlabel("Standard Deviations")
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(DIAGNOSTIC_DIR, "gaze_data_health.png"))
    print(f"📊 Visualizations saved to {DIAGNOSTIC_DIR}")

def process_workflow():
    all_windows, all_labels = [], []
    print(f"🚀 Processing DREAM Gaze Data (Features: {GAZE_FEATURES})...")
    
    for root, _, files in os.walk(RAW_JSON_DIR):
        for fn in files:
            if fn.endswith('.json'):
                series, lab, status = extract_gaze_and_label(os.path.join(root, fn))
                if series is not None:
                    all_windows.append(series); all_labels.append(lab)

    if not all_windows:
        print("❌ No valid data found.")
        return

    X_raw = np.array(all_windows)
    y_raw = np.array(all_labels)

    # --- Step 1: Oversampling ---
    counts = Counter(y_raw)
    max_samples = max(counts.values())
    X_bal_list, y_bal_list = [], []
    for label_code in LABEL_MAP.values():
        idx = np.where(y_raw == label_code)[0]
        if len(idx) == 0: continue
        res_idx = resample(idx, replace=True, n_samples=max_samples, random_state=42)
        X_bal_list.append(X_raw[res_idx]); y_bal_list.append(y_raw[res_idx])

    X_bal = np.concatenate(X_bal_list)
    y_bal = np.concatenate(y_bal_list)
    
    # --- Step 2: Normalization ---
    X_bal = (X_bal - X_bal.mean(axis=(0,1), keepdims=True)) / (X_bal.std(axis=(0,1), keepdims=True) + 1e-8)

    # Generate Visuals before final shuffle for batching
    generate_visualizations(y_raw, y_bal, X_bal)

    X_bal, y_bal = shuffle(X_bal, y_bal, random_state=42)

    # --- Step 3: Batching ---
    num_batches = len(y_bal) // BATCH_SIZE
    for i in range(num_batches):
        start, end = i*BATCH_SIZE, (i+1)*BATCH_SIZE
        with open(os.path.join(SAVE_FOLDER, f"batch_{i+1}.dt"), "wb") as f:
            pickle.dump((X_bal[start:end], y_bal[start:end]), f)

    print(f"✅ SUCCESS! Created {num_batches} balanced batches in {SAVE_FOLDER}")

if __name__ == "__main__":
    process_workflow()