import os
import pickle
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, TensorDataset

# ---------- CONFIGURATION ----------
DATA_FOLDER = r"E:\muruga\hgnn_a\dream"   
MODEL_PATH = r"E:\muruga\hgnn_a\bilstm_skeleton_model.pth"
SAVE_PATH = r"E:\muruga\hgnn_a\extracted_skeleton_features.pkl"

HIDDEN_SIZE = 128  
TARGET_SEQ_LEN = 30 
BATCH_SIZE = 64
# -----------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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
        
        self.fc = nn.Linear(hidden_size * self.multiplier, num_classes)

    def forward(self, x):
        # 1. LSTM pass
        lstm_out, _ = self.lstm(x)  # [batch, 30, 256]
        
        # 2. Attention pass
        attn_scores = self.attention(lstm_out)
        attn_weights = torch.softmax(attn_scores, dim=1)
        
        # 3. Context Vector (This is the "Feature" we want for HGNN)
        context = torch.sum(attn_weights * lstm_out, dim=1)
        
        return context # Returns the 256-D attended temporal summary

def load_batches(folder):
    X_list, y_list = [], []
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return None, None

    files = sorted([f for f in os.listdir(folder) if f.endswith(".dt")])
    for f in files:
        with open(os.path.join(folder, f), "rb") as fh:
            data, labels = pickle.load(fh)
            data = np.nan_to_num(np.asarray(data), nan=0.0)
            if data.shape[1] >= TARGET_SEQ_LEN:
                X_list.append(data[:, :TARGET_SEQ_LEN, :])
                y_list.append(np.asarray(labels))
    return np.concatenate(X_list, axis=0), np.concatenate(y_list, axis=0)

def extract():
    print("📂 Loading sessions for extraction...")
    X, y = load_batches(DATA_FOLDER)
    
    if X is None:
        print("❌ Loading failed. Check your data path.")
        return

    # 1. Load Model
    print(f"🔄 Loading trained model from: {MODEL_PATH}")
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    
    # Initialize model structure
    model = BiLSTMClassifier(input_size=X.shape[2], hidden_size=HIDDEN_SIZE).to(device)
    
    # Load the weights
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    
    # 2. Prepare Data Loader
    loader = DataLoader(TensorDataset(torch.tensor(X, dtype=torch.float32)), 
                        batch_size=BATCH_SIZE, 
                        shuffle=False)
    
    all_features = []
    print(f"💾 Extracting Attended Features for {len(X)} nodes...")
    
    # 3. Extraction Loop
    with torch.no_grad():
        for batch in loader:
            # The forward pass now returns the context vector instead of the last state
            features = model(batch[0].to(device))
            all_features.append(features.cpu().numpy())

    node_features = np.concatenate(all_features, axis=0)
    
    # 4. Save for HGNN phase
    with open(SAVE_PATH, "wb") as f:
        pickle.dump({"features": node_features, "labels": y}, f)

    print(f"📊 Extraction Complete! Feature Shape: {node_features.shape}")
    print(f"📁 Saved features to: {SAVE_PATH}")

if __name__ == "__main__":
    extract()