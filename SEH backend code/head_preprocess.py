import os
import json
import numpy as np
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.utils import resample, shuffle

# ---------- USER CONFIG ----------
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_JSON_DIR = str(DATA_DIR / "dream_dataset")
SAVE_FOLDER = str(DATA_DIR / "processed" / "dream_head")
DIAGNOSTIC_PLOT = os.path.join(SAVE_FOLDER, "head_data_diagnostics.pdf")
SEQ_LEN = 30
BATCH_SIZE = 64
LABEL_MAP = {"IM": 0, "TT": 1, "JA": 2}

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman'], 'font.size': 14})
# ---------------------------------

os.makedirs(SAVE_FOLDER, exist_ok=True)

def extract_head_gaze(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ability = data.get('task', {}).get('ability') or data.get('condition')
        ability_str = str(ability).upper() if ability else "UNKNOWN"
        final_label = next((LABEL_MAP[k] for k in LABEL_MAP if k in ability_str), None)
        if final_label is None: return None, None
        
        head_data = data.get('head_gaze', {})
        df = pd.DataFrame({'rx': head_data.get('rx', []), 'ry': head_data.get('ry', []), 'rz': head_data.get('rz', [])})
        if df.empty: return None, None

        # Interpolation for continuity
        df = df.interpolate(method='linear', limit_direction='both').fillna(0)
        series_np = df.values
        if series_np.shape[0] < SEQ_LEN: return None, None
            
        # Orientation Invariance (Relative to start)
        series_np = series_np - series_np[0, :]
        return series_np[:SEQ_LEN, :].astype(np.float32), final_label
    except: return None, None

# --- NEW: VISUALIZATION OF PREPROCESSED DATA ---
def plot_data_diagnostics(X, y):
    """Generates PDF visualizations of the processed head-gaze distributions."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # 1. Distribution Plot (Are the angles normalized?)
    for i, axis_name in enumerate(['Pitch (rx)', 'Yaw (ry)', 'Roll (rz)']):
        sns.kdeplot(X[:, :, i].flatten(), ax=ax1, label=axis_name)
    ax1.set_title("Distribution of Head Rotations")
    ax1.set_xlabel("Normalized Value"); ax1.set_ylabel("Density"); ax1.legend()

    # 2. Class Balance Plot
    class_names = list(LABEL_MAP.keys())
    counts = [Counter(y)[LABEL_MAP[k]] for k in class_names]
    sns.barplot(x=class_names, y=counts, ax=ax2, palette="viridis")
    ax2.set_title("Dataset Balance (Oversampled)")
    ax2.set_ylabel("Number of Sequences")

    plt.tight_layout()
    plt.savefig(DIAGNOSTIC_PLOT)
    plt.close()
    print(f"📊 Diagnostic plots saved: {DIAGNOSTIC_PLOT}")

def process_workflow():
    all_windows, all_labels = [], []
    print(f"🚀 Preprocessing Head Gaze...")
    
    for root, _, files in os.walk(RAW_JSON_DIR):
        for fn in files:
            if fn.endswith('.json'):
                series, lab = extract_head_gaze(os.path.join(root, fn))
                if series is not None:
                    all_windows.append(series); all_labels.append(lab)

    X_raw, y_raw = np.array(all_windows), np.array(all_labels)
    
    # Step 1: Oversampling
    counts = Counter(y_raw)
    max_s = max(counts.values())
    X_bal, y_bal = [], []
    for code in LABEL_MAP.values():
        X_c = X_raw[y_raw == code]
        X_res = resample(X_c, replace=True, n_samples=max_s, random_state=42)
        X_bal.append(X_res); y_bal.append(np.full(max_s, code))
    X_bal, y_bal = shuffle(np.concatenate(X_bal), np.concatenate(y_bal), random_state=42)

    # Step 2: Global Normalization
    X_bal = (X_bal - X_bal.mean()) / (X_bal.std() + 1e-8)

    # Generate the Diagnostic Visuals before batching
    plot_data_diagnostics(X_bal, y_bal)

    # Step 3: Batching
    n_classes = len(LABEL_MAP)
    s_per_c = BATCH_SIZE // n_classes
    idx_by_c = [np.where(y_bal == i)[0] for i in range(n_classes)]
    num_batches = min(len(idx) for idx in idx_by_c) // s_per_c

    for i in range(num_batches):
        b_idx = []
        for c in range(n_classes):
            b_idx.extend(idx_by_c[c][i*s_per_c : (i+1)*s_per_c])
        np.random.shuffle(b_idx)
        with open(os.path.join(SAVE_FOLDER, f"batch_{i+1}.dt"), "wb") as f:
            pickle.dump((X_bal[b_idx], y_bal[b_idx]), f)

    print(f"✅ Success! Created {num_batches} batches.")

if __name__ == "__main__":
    process_workflow()