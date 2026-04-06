import os
import pickle
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset

# ---------- USER CONFIG ----------
DATA_FOLDER = r"E:\muruga\hgnn_a\dream_head"   
MODEL_PATH = r"E:\muruga\hgnn_a\bilstm_head_model.pth"

HIDDEN_SIZE = 128   
NUM_LAYERS = 2
LEARNING_RATE = 0.0005 
EPOCHS = 60          
BATCH_SIZE = 64     
TARGET_SEQ_LEN = 30 
# ---------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")



class HeadGazeBiLSTM(nn.Module):
    def __init__(self, input_size=3, hidden_size=128, num_layers=2, num_classes=3):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Bi-LSTM for capturing temporal head movement patterns
        self.lstm = nn.LSTM(input_size=input_size,
                            hidden_size=hidden_size,
                            num_layers=num_layers,
                            batch_first=True,
                            bidirectional=True,
                            dropout=0.2) 
        
        self.multiplier = 2 # Because of bidirectional=True
        
        # --- TEMPORAL ATTENTION LAYER ---
        # Learned weights to focus on critical head orientations
        self.attention = nn.Sequential(
            nn.Linear(hidden_size * self.multiplier, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
        self.fc = nn.Linear(hidden_size * self.multiplier, num_classes)

    def forward(self, x):
        # x shape: (Batch, Seq_Len, 3)
        lstm_out, _ = self.lstm(x)  # [batch, 30, hidden_size * 2]
        
        # 1. Compute Attention Scores for each timestamp
        # attn_scores shape: [batch, 30, 1]
        attn_scores = self.attention(lstm_out)
        
        # 2. Normalize scores using Softmax over time (dim=1)
        attn_weights = torch.softmax(attn_scores, dim=1)
        
        # 3. Create Context Vector (Weighted sum of hidden states)
        # Effectively "compresses" the 30 frames into one meaningful vector
        context = torch.sum(attn_weights * lstm_out, dim=1)
        
        # 4. Final classification
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
            # Ensure sequence length is exactly TARGET_SEQ_LEN
            bx = np.nan_to_num(np.asarray(bx), nan=0.0)
            if bx.shape[1] >= TARGET_SEQ_LEN:
                X_list.append(bx[:, :TARGET_SEQ_LEN, :])
                y_list.append(by)
                
    return np.concatenate(X_list, axis=0), np.concatenate(y_list, axis=0)

def main():
    X, y = load_head_batches(DATA_FOLDER)
    if X is None: return
    
    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.long)
    dataset = TensorDataset(X_tensor, y_tensor)
    
    # Train/Val Split (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

    model = HeadGazeBiLSTM(input_size=X.shape[2], hidden_size=HIDDEN_SIZE).to(device)
    model.apply(init_weights)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    print(f"🚀 Training Head-Gaze Bi-LSTM with Attention on {device}...")
    
    for epoch in range(EPOCHS):
        # --- TRAIN ---
        model.train()
        t_loss, t_correct, t_total = 0, 0, 0
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            t_loss += loss.item() * by.size(0)
            t_correct += (out.argmax(1) == by).sum().item()
            t_total += by.size(0)

        # --- VALIDATE ---
        model.eval()
        v_loss, v_correct, v_total = 0, 0, 0
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(device), by.to(device)
                out = model(bx)
                v_loss += criterion(out, by).item() * by.size(0)
                v_correct += (out.argmax(1) == by).sum().item()
                v_total += by.size(0)

        print(f"Epoch [{epoch+1}/{EPOCHS}] "
              f"Tr Loss: {t_loss/t_total:.4f} Acc: {t_correct/t_total:.4f} | "
              f"Val Loss: {v_loss/v_total:.4f} Acc: {v_correct/v_total:.4f}")

    # Save the model
    torch.save({
        "model_state_dict": model.state_dict(), 
        "input_size": X.shape[2], 
        "hidden_size": HIDDEN_SIZE
    }, MODEL_PATH)
    print(f"✅ Head Gaze LSTM with Attention Saved to {MODEL_PATH}")

if __name__ == "__main__":
    main()