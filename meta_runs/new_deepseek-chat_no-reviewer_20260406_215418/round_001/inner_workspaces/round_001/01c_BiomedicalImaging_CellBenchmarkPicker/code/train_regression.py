import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Mapping from bucket to continuous value (midpoint)
bucket_to_cont = {0: 0.125, 1: 0.375, 2: 0.625, 3: 0.875}

def bucket_to_continuous(y):
    return np.array([bucket_to_cont[int(val)] for val in y])

def continuous_to_binary(y_cont, threshold=0.5):
    return (y_cont >= threshold).astype(int)

def compute_binary_dice(y_true_bin, y_pred_bin, eps=1e-7):
    intersection = np.sum(y_true_bin * y_pred_bin)
    union = np.sum(y_true_bin) + np.sum(y_pred_bin)
    return (2. * intersection + eps) / (union + eps)

class MLPRegressor(nn.Module):
    def __init__(self, input_dim, hidden_dims=[64, 32], dropout=0.2):
        super(MLPRegressor, self).__init__()
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = h_dim
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Sigmoid())  # output in [0,1]
        self.net = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.net(x).squeeze()

def train_regression(dataset_id, epochs=200, lr=0.001, batch_size=16):
    print(f"\n=== Regression MLP on {dataset_id} ===")
    train_df = pd.read_csv(f'../data/patches/{dataset_id}/train.csv')
    val_df = pd.read_csv(f'../data/patches/{dataset_id}/val.csv')
    test_df = pd.read_csv(f'../data/patches/{dataset_id}/test.csv')
    
    combined_df = pd.concat([train_df, val_df], ignore_index=True)
    
    X_train = combined_df.drop('label', axis=1).values.astype(np.float32)
    y_train = combined_df['label'].values.astype(np.int64)
    X_test = test_df.drop('label', axis=1).values.astype(np.float32)
    y_test = test_df['label'].values.astype(np.int64)
    
    # Convert labels to continuous
    y_train_cont = bucket_to_continuous(y_train).astype(np.float32)
    y_test_cont = bucket_to_continuous(y_test).astype(np.float32)
    
    # Binary ground truth for Dice
    y_test_bin = continuous_to_binary(y_test_cont, threshold=0.5)
    
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    X_train_t = torch.tensor(X_train)
    y_train_t = torch.tensor(y_train_cont)
    X_test_t = torch.tensor(X_test)
    y_test_t = torch.tensor(y_test_cont)
    
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    input_dim = X_train.shape[1]
    model = MLPRegressor(input_dim)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
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
    
    model.eval()
    with torch.no_grad():
        test_outputs = model(X_test_t).cpu().numpy()
        # Clip to [0,1]
        test_outputs = np.clip(test_outputs, 0, 1)
        # Convert to binary
        test_bin = (test_outputs >= 0.5).astype(int)
        dice = compute_binary_dice(y_test_bin, test_bin)
        mse = np.mean((test_outputs - y_test_cont)**2)
        
        # Also compute accuracy if we bucketize predictions
        pred_bucket = np.digitize(test_outputs, bins=[0.25, 0.5, 0.75]) - 1
        pred_bucket = np.clip(pred_bucket, 0, 3)
        accuracy = np.mean(pred_bucket == y_test)
    
    print(f"  Test MSE: {mse:.4f}")
    print(f"  Binary Dice (threshold 0.5): {dice:.4f}")
    print(f"  Bucket Accuracy: {accuracy:.4f}")
    
    return {
        'dataset_id': dataset_id,
        'mse': float(mse),
        'dice': float(dice),
        'accuracy': float(accuracy)
    }

if __name__ == '__main__':
    selected = ['D0014', 'D0010', 'D0009', 'D0008']
    results = []
    for dataset_id in selected:
        res = train_regression(dataset_id)
        results.append(res)
    
    print("\n=== Summary ===")
    for res in results:
        print(f"{res['dataset_id']}: Binary Dice = {res['dice']:.4f}, Accuracy = {res['accuracy']:.4f}")
    
    import json
    import os
    os.makedirs('../outputs', exist_ok=True)
    with open('../outputs/regression_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to outputs/regression_results.json")
