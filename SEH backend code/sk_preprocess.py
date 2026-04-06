import os
import json
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.utils import resample, shuffle

# ================= CONFIGURATION =================
RAW_JSON_DIR = r"E:\muruga\data\DREAMdataset"
SAVE_FOLDER = r"E:\muruga\hgnn\dream"
DIAGNOSTIC_PLOT = r"E:\muruga\hgnn\data_diagnostics.png"

SEQ_LEN = 30  
BATCH_SIZE = 64
LABEL_MAP = {"IM": 0, "TT": 1, "JA": 2} 
# =================================================

os.makedirs(SAVE_FOLDER, exist_ok=True)

def extract_data_and_label(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        task_info = data.get('task', {})
        ability = task_info.get('ability')
        if not ability:
            ability = data.get('condition')
            
        ability_str = str(ability).upper() if ability else "UNKNOWN"

        final_label = None
        for key in LABEL_MAP.keys():
            if key in ability_str:
                final_label = LABEL_MAP[key]
                break
        
        if final_label is None:
            return None, None, f"Unknown Task: {ability_str}"

        joints = data.get('skeleton', {})
        if not joints: 
            return None, None, "No Skeleton Data"
        
        all_series = []
        for joint_name in sorted(joints.keys()):
            j = joints[joint_name]
            xs, ys, zs = j.get('x', []), j.get('y', []), j.get('z', [])
            if not xs: return None, None, f"Empty Joint: {joint_name}"
            all_series.append([v if v is not None else np.nan for v in xs])
            all_series.append([v if v is not None else np.nan for v in ys])
            all_series.append([v if v is not None else np.nan for v in zs])
        
        series_np = np.array(all_series).T 
        clean_series = series_np[~np.isnan(series_np).any(axis=1)]
        
        if clean_series.shape[0] < SEQ_LEN:
            return None, None, f"Too Short ({clean_series.shape[0]})"
            
        clean_series = clean_series - clean_series[0, :]
        return clean_series[:SEQ_LEN, :].astype(np.float32), final_label, "Success"
    except Exception as e:
        return None, None, f"Error: {str(e)}"

# --- STEP 1: balance_data (Oversampling) ---
def balance_multiclass_data(X, y):
    """Grows minority classes to match the size of the majority class."""
    counts = Counter(y)
    max_samples = max(counts.values())
    
    X_balanced = []
    y_balanced = []
    
    for label_code in LABEL_MAP.values():
        X_class = X[y == label_code]
        if len(X_class) == 0: continue
        
        # Oversample each class to match max_samples
        X_resampled = resample(X_class, 
                               replace=True, 
                               n_samples=max_samples, 
                               random_state=42)
        
        X_balanced.append(X_resampled)
        y_balanced.append(np.full(max_samples, label_code))
    
    X_final = np.concatenate(X_balanced, axis=0)
    y_final = np.concatenate(y_balanced, axis=0)
    
    # --- STEP 3: shuffle (Randomization) ---
    return shuffle(X_final, y_final, random_state=42)

# --- STEP 2: create_batches (Structured Split) ---
def create_balanced_batches(X, y):
    """Creates batches where classes are represented as evenly as possible."""
    n_classes = len(LABEL_MAP)
    samples_per_class = BATCH_SIZE // n_classes
    
    indices_by_class = [np.where(y == i)[0] for i in range(n_classes)]
    # Shuffle indices for variety
    for idx_list in indices_by_class:
        np.random.shuffle(idx_list)
        
    batches = []
    # Find how many batches we can make where every class has 'samples_per_class'
    num_full_batches = min(len(idx) for idx in indices_by_class) // samples_per_class
    
    for i in range(num_full_batches):
        batch_indices = []
        for c in range(n_classes):
            start = i * samples_per_class
            end = (i + 1) * samples_per_class
            batch_indices.extend(indices_by_class[c][start:end])
        
        # Shuffle the internal batch so the model doesn't see classes in order
        np.random.shuffle(batch_indices)
        batches.append((X[batch_indices], y[batch_indices]))
        
    return batches

def process_workflow():
    all_windows, all_labels = [], []
    print(f"🚀 Processing DREAM Dataset...")
    
    for root, _, files in os.walk(RAW_JSON_DIR):
        for fn in files:
            if fn.endswith('.json'):
                series, lab, status = extract_data_and_label(os.path.join(root, fn))
                if series is not None:
                    all_windows.append(series); all_labels.append(lab)

    if not all_windows:
        print("❌ No data found.")
        return

    X_raw = np.array(all_windows)
    y_raw = np.array(all_labels)

    # Apply Step 1 & 3
    print("⚖️ Balancing dataset via Oversampling...")
    X_bal, y_bal = balance_multiclass_data(X_raw, y_raw)
    
    # Normalization
    X_bal = (X_bal - X_bal.mean(axis=(0,1), keepdims=True)) / (X_bal.std(axis=(0,1), keepdims=True) + 1e-8)

    # Apply Step 2
    print(f"📦 Creating structured batches (Size: {BATCH_SIZE})...")
    batches = create_balanced_batches(X_bal, y_bal)

    for i, (bx, by) in enumerate(batches):
        with open(os.path.join(SAVE_FOLDER, f"batch_{i+1}.dt"), "wb") as f:
            pickle.dump((bx, by), f)

    print(f"✅ SUCCESS! Created {len(batches)} balanced batches.")
    print(f"Total samples used: {len(batches) * BATCH_SIZE}")
    print(f"Each batch has ~{BATCH_SIZE//3} samples of IM, TT, and JA.")

if __name__ == "__main__":
    process_workflow()