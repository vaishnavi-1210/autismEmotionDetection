import os
import pickle
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from torch.utils.data import Dataset, DataLoader, Subset
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_recall_curve, roc_curve, classification_report, 
    confusion_matrix, auc, cohen_kappa_score, matthews_corrcoef, f1_score
)
from sklearn.preprocessing import label_binarize
from sklearn.neighbors import NearestNeighbors

# ---------- USER CONFIG ----------
SKEL_PATH = r"E:\muruga\hgnn_a\extracted_skeleton_features.pkl"
EYE_PATH  = r"E:\muruga\hgnn_a\extracted_gaze_features.pkl"
HEAD_PATH = r"E:\muruga\hgnn_a\extracted_head_features.pkl"
RESULTS_FOLDER = r"E:\muruga\hgnn_a\triple_fusion_results"
PDF_REPORT_PATH = os.path.join(RESULTS_FOLDER, "Triple_Fusion_HGNN_Report.pdf")
MODEL_SAVE_PATH = os.path.join(RESULTS_FOLDER, "triple_fusion_hgnn_final.pth")

INPUT_DIM = 768 # 256*3
HIDDEN_DIM = 256
NUM_CLASSES = 3
NUM_EPOCHS = 100
BATCH_SIZE = 64
K_NEIGHBORS = 20
CLASS_NAMES = ["IM", "TT", "JA"]

# Standardized Academic Font Settings
plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 14})
# ---------------------------------

os.makedirs(RESULTS_FOLDER, exist_ok=True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- 1. TRIPLE-SYNC DATA PREPARATION ---
def prepare_triple_data():
    print("📂 Syncing Triple Modalities (Skeleton, Eye, Head)...")
    with open(SKEL_PATH, 'rb') as f: skel = pickle.load(f)
    with open(EYE_PATH, 'rb')  as f: eye  = pickle.load(f)
    with open(HEAD_PATH, 'rb') as f: head = pickle.load(f)
    
    min_samples = min(len(skel['features']), len(eye['features']), len(head['features']))
    print(f"⚖️ Triple Sync: {min_samples} common samples found.")

    combined = np.concatenate([
        skel['features'][:min_samples], 
        eye['features'][:min_samples], 
        head['features'][:min_samples]
    ], axis=1)
    
    combined = np.nan_to_num(combined)
    return combined, skel['labels'][:min_samples]

class IndexedTripleDataset(Dataset):
    def __init__(self, x, y):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
    def __len__(self): return len(self.y)
    def __getitem__(self, idx):
        return self.x[idx], self.y[idx], idx

# --- 2. TOPOLOGY: GLOBAL LAPLACIAN ---
def construct_global_hgnn_laplacian(features, k=20):
    print(f"🌐 Building Triple Global Topology for {features.shape[0]} nodes...")
    norm_features = F.normalize(features, p=2, dim=1).cpu().numpy()
    knn = NearestNeighbors(n_neighbors=k+1).fit(norm_features)
    indices = knn.kneighbors(norm_features)[1]
    
    H = np.zeros((features.shape[0], features.shape[0]))
    for i, neighbors in enumerate(indices):
        H[i, neighbors] = 1 

    H = torch.tensor(H, dtype=torch.float32).to(device)
    D_v = torch.sum(H, dim=1) + 1e-6
    D_e = torch.sum(H, dim=0) + 1e-6
    
    Dv_inv_sqrt = torch.diag(torch.pow(D_v, -0.5))
    De_inv = torch.diag(torch.pow(D_e, -1.0))
    
    return Dv_inv_sqrt @ H @ De_inv @ H.t() @ Dv_inv_sqrt

# --- 3. MODEL ARCHITECTURE ---
class TripleFusionHGNN(nn.Module):
    def __init__(self, in_dim, h_dim, out_dim):
        super().__init__()
        self.hconv1 = nn.Linear(in_dim, h_dim)
        self.hconv2 = nn.Linear(h_dim, h_dim)
        self.classifier = nn.Linear(h_dim, out_dim)

    def forward(self, x, G_batch):
        x = F.relu(torch.matmul(G_batch, self.hconv1(x)))
        x = F.dropout(x, p=0.3, training=self.training)
        x = F.relu(torch.matmul(G_batch, self.hconv2(x)))
        return self.classifier(x)

# --- 4. CONSOLIDATED VISUALIZATION ---
def generate_triple_report(history, y_true, y_probs, y_preds):
    with PdfPages(PDF_REPORT_PATH) as pdf:
        # PAGE 1: Learning Curves
        fig1, ax = plt.subplots(1, 2, figsize=(14, 6))
        ax[0].plot(history['t_loss'], label='Train Loss', color='#1f78b4', lw=2)
        ax[0].plot(history['v_loss'], label='Val Loss', color='#ff7f0e', lw=2)
        ax[0].set_title('Triple Fusion Loss', fontweight='bold')
        ax[0].set_xlabel('Epochs'); ax[0].set_ylabel('Loss')
        ax[0].legend(); ax[0].grid(True, alpha=0.3)

        ax[1].plot(history['t_acc'], label='Train Acc', color='#1f78b4', lw=2)
        ax[1].plot(history['v_acc'], label='Val Acc', color='#ff7f0e', lw=2)
        ax[1].set_title('Triple Fusion Accuracy', fontweight='bold')
        ax[1].set_xlabel('Epochs'); ax[1].set_ylabel('Accuracy')
        ax[1].legend(); ax[1].grid(True, alpha=0.3)
        plt.tight_layout()
        pdf.savefig(fig1); plt.close()

        # PAGE 2: ROC & PR Curves
        fig2, ax = plt.subplots(1, 2, figsize=(14, 6))
        y_true_bin = label_binarize(y_true, classes=[0, 1, 2])
        for i, name in enumerate(CLASS_NAMES):
            fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_probs[:, i])
            ax[0].plot(fpr, tpr, label=f'{name} (AUC={auc(fpr, tpr):.2f})', lw=2)
        ax[0].plot([0, 1], [0, 1], 'k--', alpha=0.4)
        ax[0].set_title('AUC-ROC Curve', fontweight='bold')
        ax[0].set_xlabel('FPR'); ax[0].set_ylabel('TPR'); ax[0].legend()

        for i, name in enumerate(CLASS_NAMES):
            p, r, _ = precision_recall_curve(y_true_bin[:, i], y_probs[:, i])
            ax[1].plot(r, p, label=f'{name} (AUC={auc(r, p):.2f})', lw=2)
        ax[1].set_title('Precision-Recall Curve', fontweight='bold')
        ax[1].set_xlabel('Recall'); ax[1].set_ylabel('Precision'); ax[1].legend()
        plt.tight_layout()
        pdf.savefig(fig2); plt.close()

        # PAGE 3: Confusion Matrix
        fig3, ax = plt.subplots(figsize=(8, 7))
        cm = confusion_matrix(y_true, y_preds)
        sns.heatmap(cm, annot=True, fmt='d', cmap='YlGnBu', xticklabels=CLASS_NAMES, 
                    yticklabels=CLASS_NAMES, annot_kws={"size": 22, "weight": "bold"})
        ax.set_title('Triple Fusion Confusion Matrix', fontweight='bold', pad=20)
        ax.set_xlabel('Predicted Label'); ax.set_ylabel('True Label')
        plt.tight_layout()
        pdf.savefig(fig3); plt.close()

        # PAGE 4: Statistical Report
        fig4 = plt.figure(figsize=(10, 10))
        plt.axis('off')
        report = classification_report(y_true, y_preds, target_names=CLASS_NAMES)
        kappa = cohen_kappa_score(y_true, y_preds)
        mcc = matthews_corrcoef(y_true, y_preds)
        
        extra_metrics = ""
        for i, name in enumerate(CLASS_NAMES):
            tp = cm[i, i]
            fn = np.sum(cm[i, :]) - tp
            fp = np.sum(cm[:, i]) - tp
            tn = np.sum(cm) - (tp + fp + fn)
            spec = tn / (tn + fp + 1e-8)
            sens = tp / (tp + fn + 1e-8)
            extra_metrics += f"{name:2} | Sensitivity: {sens:.4f} | Specificity: {spec:.4f}\n"

        metrics_text = (
            f"--- Triple Fusion (SKEL+EYE+HEAD) Performance ---\n\n"
            f"{report}\n"
            f"--------------------------------------------------\n"
            f"Per-Class Metrics:\n{extra_metrics}\n"
            f"--------------------------------------------------\n"
            f"Additional Global Metrics:\n"
            f"Cohen’s Kappa Score:    {kappa:.4f}\n"
            f"Matthews Correlation:   {mcc:.4f}\n"
            f"--------------------------------------------------\n"
        )
        plt.text(0.05, 0.95, metrics_text, fontsize=14, family='monospace', verticalalignment='top')
        plt.title("Triple Fusion Statistical Summary", fontsize=18, fontweight='bold')
        pdf.savefig(fig4); plt.close()

# --- 5. MAIN EXECUTION ---
def main():
    combined_x, combined_y = prepare_triple_data()
    full_ds = IndexedTripleDataset(combined_x, combined_y)
    features_all = full_ds.x.to(device)
    G_GLOBAL = construct_global_hgnn_laplacian(features_all, k=K_NEIGHBORS)

    tr_idx, val_idx = train_test_split(range(len(full_ds)), test_size=0.2, random_state=42, stratify=combined_y)
    train_loader = DataLoader(Subset(full_ds, tr_idx), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(Subset(full_ds, val_idx), batch_size=BATCH_SIZE, shuffle=False)

    model = TripleFusionHGNN(INPUT_DIM, HIDDEN_DIM, NUM_CLASSES).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=5e-4)
    criterion = nn.CrossEntropyLoss()
    
    history = {'t_loss': [], 'v_loss': [], 't_acc': [], 'v_acc': []}

    print(f"🚀 Training Triple Fusion HGNN for {NUM_EPOCHS} epochs...")
    print("-" * 80)
    print(f"{'Epoch':<8} | {'Tr. Loss':<10} | {'Tr. Acc':<10} | {'Val Loss':<10} | {'Val Acc':<10}")
    print("-" * 80)

    for epoch in range(NUM_EPOCHS):
        model.train()
        t_loss, t_correct, t_total = 0, 0, 0
        for bx, by, idx in train_loader:
            bx, by = bx.to(device), by.to(device)
            G_batch = G_GLOBAL[idx][:, idx]
            optimizer.zero_grad()
            out = model(bx, G_batch)
            loss = criterion(out, by)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            t_loss += loss.item() * by.size(0); t_correct += (out.argmax(1) == by).sum().item(); t_total += by.size(0)

        model.eval()
        v_loss, v_correct, v_total = 0, 0, 0
        with torch.no_grad():
            for bx, by, idx in val_loader:
                bx, by = bx.to(device), by.to(device)
                G_batch = G_GLOBAL[idx][:, idx]
                out = model(bx, G_batch)
                v_loss += criterion(out, by).item() * by.size(0); v_correct += (out.argmax(1) == by).sum().item(); v_total += by.size(0)

        history['t_loss'].append(t_loss/t_total); history['v_loss'].append(v_loss/v_total)
        history['t_acc'].append(t_correct/t_total); history['v_acc'].append(v_correct/v_total)

        print(f"{epoch+1:<8} | {history['t_loss'][-1]:<10.4f} | {history['t_acc'][-1]:<10.4f} | {history['v_loss'][-1]:<10.4f} | {history['v_acc'][-1]:<10.4f}")

    print("-" * 80)

    # Final Evaluation & Visualization
    model.eval()
    y_true, y_preds, y_probs = [], [], []
    with torch.no_grad():
        for bx, by, idx in val_loader:
            bx, by = bx.to(device), by.to(device)
            G_batch = G_GLOBAL[idx][:, idx]
            out = model(bx, G_batch)
            y_true.extend(by.cpu().numpy()); y_preds.extend(out.argmax(1).cpu().numpy()); y_probs.extend(torch.softmax(out, dim=1).cpu().numpy())

    generate_triple_report(history, np.array(y_true), np.array(y_probs), np.array(y_preds))
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"✅ Triple Fusion Report saved to: {PDF_REPORT_PATH}")

if __name__ == "__main__":
    main()