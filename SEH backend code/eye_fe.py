import os
import pickle
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, TensorDataset

# ---------- CONFIGURATION ----------
DATA_FOLDER = r"E:\muruga\hgnn_a\dream_gaze"   
MODEL_PATH = r"E:\muruga\hgnn_a\bilstm_gaze_model.pth"
SAVE_PATH = r"E:\muruga\hgnn_a\extracted_gaze_features.pkl"

HIDDEN_SIZE = 128  
TARGET_SEQ_LEN = 30 
BATCH_SIZE = 64
# -----------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 

class BiLSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=2, num_classes=3, bidirectional=True):
        super().__init__()
        self.hidden_size = hidden_size
        self.lstm = nn.LSTM(input_size=input_size,
                            hidden_size=hidden_size,
                            num_layers=num_layers,
                            batch_first=True,
                            bidirectional=bidirectional)
        
        self.multiplier = 2 if bidirectional else 1
        
        # --- ATTENTION LAYER (Must match training code exactly) ---
        self.attention = nn.Sequential(
            nn.Linear(hidden_size * self.multiplier, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
        # FC layer defined to ensure state_dict loads correctly, 
        # though we won't use it for extraction.
        self.fc = nn.Linear(hidden_size * self.multiplier, num_classes)

    def forward(self, x):
        # 1. LSTM pass
        lstm_out, _ = self.lstm(x)  # [batch, 30, 256]
        
        # 2. Attention pass
        attn_scores = self.attention(lstm_out)
        attn_weights = torch.softmax(attn_scores, dim=1)
        
        # 3. Context Vector (The "Feature" summary for HGNN)
        context = torch.sum(attn_weights * lstm_out, dim=1)
        
        return context 

def load_batches(folder):
    X_list, y_list = [], []
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return None, None

    files = sorted([f for f in os.listdir(folder) if f.endswith(".dt")])
    for f in files:
        path = os.path.join(folder, f)
        with open(path, "rb") as fh:
            data, labels = pickle.load(fh)
            data = np.nan_to_num(np.asarray(data), nan=0.0)
            if data.shape[1] >= TARGET_SEQ_LEN:
                X_list.append(data[:, :TARGET_SEQ_LEN, :])
                y_list.append(np.asarray(labels))
    return np.concatenate(X_list, axis=0), np.concatenate(y_list, axis=0)

def extract():
    print("📂 Loading Gaze sessions for embedding extraction...")
    X, y = load_batches(DATA_FOLDER)
    
    if X is None:
        print("❌ Loading failed. Check your data path.")
        return

    # 1. Load Model Checkpoint
    print(f"🔄 Loading trained Gaze model from: {MODEL_PATH}")
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    
    # 2. Initialize model with the correct input dimension
    input_dim = X.shape[2]
    model = BiLSTMClassifier(input_size=input_dim, hidden_size=HIDDEN_SIZE).to(device)
    
    # 3. Load weights
    # strict=False is fine here as we only care about the LSTM and Attention layers
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    
    loader = DataLoader(TensorDataset(torch.tensor(X, dtype=torch.float32)), 
                        batch_size=BATCH_SIZE, 
                        shuffle=False)
    
    all_features = []
    print(f"💾 Generating 256-D attended embeddings for {len(X)} gaze nodes...")

    with torch.no_grad():
        for batch in loader:
            # Returns the context vector (the attended summary)
            features = model(batch[0].to(device))
            all_features.append(features.cpu().numpy())

    node_features = np.concatenate(all_features, axis=0)
    
    # 4. Save the embeddings for the HGNN phase
    with open(SAVE_PATH, "wb") as f:
        pickle.dump({"features": node_features, "labels": y}, f)

    print(f"📊 Extraction Complete! Feature Shape: {node_features.shape}")
    print(f"📁 Saved attended gaze embeddings to: {SAVE_PATH}")

if __name__ == "__main__":
    extract()