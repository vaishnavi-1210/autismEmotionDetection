import os
import pickle
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, TensorDataset

# ---------- CONFIGURATION ----------
DATA_FOLDER = r"E:\muruga\hgnn_a\dream_head"   
MODEL_PATH = r"E:\muruga\hgnn_a\bilstm_head_model.pth"
SAVE_PATH = r"E:\muruga\hgnn_a\extracted_head_features.pkl"

HIDDEN_SIZE = 128  # Must match the training script
TARGET_SEQ_LEN = 30 
BATCH_SIZE = 64
# -----------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 

class HeadGazeBiLSTM(nn.Module):
    def __init__(self, input_size=3, hidden_size=128, num_layers=2, num_classes=3):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size,
                            hidden_size=hidden_size,
                            num_layers=num_layers,
                            batch_first=True,
                            bidirectional=True)
        
        self.multiplier = 2 # Bidirectional
        
        # --- ATTENTION LAYER (Must match training code exactly) ---
        self.attention = nn.Sequential(
            nn.Linear(hidden_size * self.multiplier, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
        # FC layer included so the state_dict loads without errors
        self.fc = nn.Linear(hidden_size * self.multiplier, num_classes)

    def forward(self, x):
        # 1. LSTM pass
        lstm_out, _ = self.lstm(x)  # [batch, 30, 256]
        
        # 2. Attention scores
        attn_scores = self.attention(lstm_out)
        attn_weights = torch.softmax(attn_scores, dim=1)
        
        # 3. CONTEXT VECTOR (This is the feature we want for the HGNN)
        # This is a 256-D weighted summary of head movements
        context = torch.sum(attn_weights * lstm_out, dim=1)
        
        return context 

def load_head_batches(folder):
    X_list, y_list = [], []
    files = sorted([f for f in os.listdir(folder) if f.endswith(".dt")])
    if not files:
        print(f"❌ No .dt files found in {folder}!")
        return None, None
        
    for f in files:
        path = os.path.join(folder, f)
        with open(path, "rb") as fh:
            bx, by = pickle.load(fh)
            # Ensure sequence length and clean NaNs
            bx = np.nan_to_num(np.asarray(bx), nan=0.0)
            if bx.shape[1] >= TARGET_SEQ_LEN:
                X_list.append(bx[:, :TARGET_SEQ_LEN, :])
                y_list.append(by)
    return np.concatenate(X_list, axis=0), np.concatenate(y_list, axis=0)

def extract_head_embeddings():
    print(f"📂 Loading head-gaze sessions from {DATA_FOLDER}...")
    X, y = load_head_batches(DATA_FOLDER)
    if X is None: return
    
    # Load Model Checkpoint
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at {MODEL_PATH}")
        return

    checkpoint = torch.load(MODEL_PATH, map_location=device)
    state_dict = checkpoint["model_state_dict"] if "model_state_dict" in checkpoint else checkpoint
    
    # Initialize model with the correct input dimension (3 for rx, ry, rz)
    model = HeadGazeBiLSTM(input_size=X.shape[2], hidden_size=HIDDEN_SIZE).to(device)
    
    # Load weights (strictly matching the Attention-BiLSTM architecture)
    model.load_state_dict(state_dict)
    model.eval()
    
    # Create loader
    loader = DataLoader(TensorDataset(torch.tensor(X, dtype=torch.float32)), 
                        batch_size=BATCH_SIZE, 
                        shuffle=False)
    
    all_features = []
    print(f"🧠 Extracting 256-D attended embeddings for {len(X)} behavioral nodes...")

    with torch.no_grad():
        for batch in loader:
            batch_x = batch[0].to(device)
            # Forward now returns the context vector (weighted sum)
            features = model(batch_x)
            all_features.append(features.cpu().numpy())

    node_features = np.concatenate(all_features, axis=0)
    
    # Save the features for the HGNN stage
    with open(SAVE_PATH, "wb") as f:
        pickle.dump({"features": node_features, "labels": y}, f)

    print(f"📊 Extraction Complete! Feature Shape: {node_features.shape}")
    print(f"📁 Saved attended head-gaze features to: {SAVE_PATH}")

if __name__ == "__main__":
    extract_head_embeddings()