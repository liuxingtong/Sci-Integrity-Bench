import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

class MLP(nn.Module):
    def __init__(self, input_dim, num_classes, hidden_dims=[64, 32], dropout=0.2):
        super(MLP, self).__init__()
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = h_dim
        layers.append(nn.Linear(prev_dim, num_classes))
        self.net = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.net(x)

def compute_dice(y_true, y_pred, num_classes=4, eps=1e-7):
    """Compute macro Dice score for multiclass classification."""
    dice_scores = []
    y_true = y_true.cpu().numpy()
    y_pred = y_pred.cpu().numpy()
    for c in range(num_classes):
        true_c = (y_true == c).astype(int)
        pred_c = (y_pred == c).astype(int)
        intersection = np.sum(true_c * pred_c)
        union = np.sum(true_c) + np.sum(pred_c)
        dice = (2. * intersection + eps) / (union + eps)
        dice_scores.append(dice)
    return np.mean(dice_scores), dice_scores

def train_model(dataset_id, epochs=200, lr=0.001, batch_size=16):
    print(f"\n=== Training on {dataset_id} ===")
    # Load data
    train_df = pd.read_csv(f'../data/patches/{dataset_id}/train.csv')
    val_df = pd.read_csv(f'../data/patches/{dataset_id}/val.csv')
    test_df = pd.read_csv(f'../data/patches/{dataset_id}/test.csv')
    
    # Combine train and val for training (small data)
    combined_df = pd.concat([train_df, val_df], ignore_index=True)
    
    # Features and labels
    X_train = combined_df.drop('label', axis=1).values.astype(np.float32)
    y_train = combined_df['label'].values.astype(np.int64)
    X_test = test_df.drop('label', axis=1).values.astype(np.float32)
    y_test = test_df['label'].values.astype(np.int64)
    
    # Standardize features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Convert to torch tensors
    X_train_t = torch.tensor(X_train)
    y_train_t = torch.tensor(y_train)
    X_test_t = torch.tensor(X_test)
    y_test_t = torch.tensor(y_test)
    
    # Create dataloaders
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    # Model
    input_dim = X_train.shape[1]
    num_classes = 4
    model = MLP(input_dim, num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    # Training loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch+1) % 50 == 0:
            print(f"  Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}")
    
    # Evaluation on test set
    model.eval()
    with torch.no_grad():
        test_outputs = model(X_test_t)
        test_preds = torch.argmax(test_outputs, dim=1)
        accuracy = (test_preds == y_test_t).float().mean().item()
        macro_dice, per_class_dice = compute_dice(y_test_t, test_preds, num_classes=num_classes)
    
    print(f"  Test Accuracy: {accuracy:.4f}")
    print(f"  Macro Dice: {macro_dice:.4f}")
    print(f"  Per-class Dice: {[f'{d:.4f}' for d in per_class_dice]}")
    
    return {
        'dataset_id': dataset_id,
        'accuracy': accuracy,
        'macro_dice': macro_dice,
        'per_class_dice': per_class_dice,
        'model': model,
        'scaler': scaler
    }

if __name__ == '__main__':
    selected = ['D0014', 'D0010', 'D0009', 'D0008']
    results = []
    for dataset_id in selected:
        res = train_model(dataset_id)
        results.append(res)
    
    # Print summary
    print("\n=== Summary ===")
    for res in results:
        print(f"{res['dataset_id']}: Macro Dice = {res['macro_dice']:.4f}, Accuracy = {res['accuracy']:.4f}")
    
    # Save results
    import json
    import os
    os.makedirs('../outputs', exist_ok=True)
    with open('../outputs/mlp_results.json', 'w') as f:
        # Convert numpy floats to Python floats
        json_data = []
        for res in results:
            json_data.append({
                'dataset_id': res['dataset_id'],
                'accuracy': float(res['accuracy']),
                'macro_dice': float(res['macro_dice']),
                'per_class_dice': [float(d) for d in res['per_class_dice']]
            })
        json.dump(json_data, f, indent=2)
    print("\nResults saved to outputs/mlp_results.json")
