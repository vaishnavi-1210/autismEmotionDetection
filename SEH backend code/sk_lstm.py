import os
import pickle
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset, random_split

# ---------- USER CONFIG ----------
DATA_FOLDER = r"E:\muruga\hgnn_a\dream"   
MODEL_PATH = r"E:\muruga\hgnn_a\bilstm_skeleton_model.pth"
HIDDEN_SIZE = 128   
NUM_LAYERS = 2
LEARNING_RATE = 0.0003 
EPOCHS = 30          
BATCH_SIZE = 64      
TARGET_SEQ_LEN = 30 
VAL_SPLIT = 0.2  # 20% for validation
# ---------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 

class BiLSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, num_classes=3, bidirectional=True):
        super().__init__()
        self.hidden_size = hidden_size
        self.lstm = nn.LSTM(input_size=input_size,
                            hidden_size=hidden_size,
                            num_layers=num_layers,
                            batch_first=True,
                            bidirectional=bidirectional)
        
        self.multiplier = 2 if bidirectional else 1
        
        # --- TEMPORAL ATTENTION LAYER ---
        # This sub-network learns to score each time step
        self.attention = nn.Sequential(
            nn.Linear(hidden_size * self.multiplier, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
        self.fc = nn.Linear(hidden_size * self.multiplier, num_classes)

    def forward(self, x):
        # x shape: [batch, seq_len, input_size]
        lstm_out, _ = self.lstm(x)  # [batch, 30, hidden_size * 2]
        
        # 1. Compute Attention Scores
        # weights shape: [batch, 30, 1]
        attn_scores = self.attention(lstm_out)
        
        # 2. Normalize scores using Softmax across the time dimension (dim=1)
        attn_weights = torch.softmax(attn_scores, dim=1)
        
        # 3. Create Context Vector (Weighted sum of hidden states)
        # context shape: [batch, hidden_size * 2]
        context = torch.sum(attn_weights * lstm_out, dim=1)
        
        # 4. Final Classification
        return self.fc(context)

def init_weights(m):
    if isinstance(m, nn.LSTM):
        for name, param in m.named_parameters():
            if 'weight_ih' in name: torch.nn.init.xavier_uniform_(param.data)
            elif 'weight_hh' in name: torch.nn.init.orthogonal_(param.data)
            elif 'bias' in name: param.data.fill_(0)
    elif isinstance(m, nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight)
        if m.bias is not None:
            m.bias.data.fill_(0)

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
    
    if not X_list:
        return None, None
        
    return np.concatenate(X_list, axis=0), np.concatenate(y_list, axis=0)

def main():
    # 1. Load Data
    X, y = load_batches(DATA_FOLDER)
    if X is None:
        print("❌ No data loaded. Check your path or TARGET_SEQ_LEN.")
        return

    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.long)
    
    print(f"📊 Dataset Loaded. Shape: {X.shape}. Features: {X.shape[2]}")

    # 2. Split into Train/Val
    full_dataset = TensorDataset(X_tensor, y_tensor)
    val_size = int(len(full_dataset) * VAL_SPLIT)
    train_size = len(full_dataset) - val_size
    train_ds, val_ds = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

    # 3. Model Setup
    model = BiLSTMClassifier(input_size=X.shape[2], hidden_size=HIDDEN_SIZE).to(device)
    model.apply(init_weights)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    print(f"🚀 Training Skeleton BiLSTM with Attention on {device}...")

    # 4. Training Loop
    for epoch in range(EPOCHS):
        # --- TRAIN ---
        model.train()
        tr_loss, tr_correct, tr_total = 0.0, 0, 0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            
            if torch.isnan(loss):
                print("❌ NaN detected in Loss! Check input data range.")
                return

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            tr_loss += loss.item() * batch_y.size(0)
            tr_correct += (outputs.argmax(1) == batch_y).sum().item()
            tr_total += batch_y.size(0)

        # --- VALIDATE ---
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                v_loss = criterion(outputs, batch_y)
                val_loss += v_loss.item() * batch_y.size(0)
                val_correct += (outputs.argmax(1) == batch_y).sum().item()
                val_total += batch_y.size(0)

        print(f"Epoch [{epoch+1}/{EPOCHS}] "
              f"Tr Loss: {tr_loss/tr_total:.4f} Acc: {tr_correct/tr_total:.4f} | "
              f"Val Loss: {val_loss/val_total:.4f} Acc: {val_correct/val_total:.4f}")

    # 5. Save Model
    torch.save({"model_state_dict": model.state_dict()}, MODEL_PATH)
    print("\n✅ Model Saved.")

if __name__ == "__main__":
    main()