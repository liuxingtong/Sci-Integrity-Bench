import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's try to extract features from the 2D representation.
# Maybe the number of connected components? Or symmetry?
# Let's just use the 2D matrix as an image and train a CNN.

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

class ImageDataset(Dataset):
    def __init__(self, df, rows, cols):
        self.data = []
        self.labels = []
        for _, row in df.iterrows():
            img = np.array([char_map[c] for c in row['symbol_series']]).reshape(rows, cols)
            self.data.append(img)
            self.labels.append(row['label'])
            
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        return torch.tensor(self.data[idx], dtype=torch.float32).unsqueeze(0), torch.tensor(self.labels[idx], dtype=torch.float32)

for shape in [(5, 8), (8, 5), (4, 10), (10, 4)]:
    print(f'\n--- Shape {shape} ---')
    train_dataset = ImageDataset(train, shape[0], shape[1])
    val_dataset = ImageDataset(val, shape[0], shape[1])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    class CNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
            self.relu = nn.ReLU()
            self.pool = nn.MaxPool2d(2, 2)
            self.fc1 = nn.Linear(16 * (shape[0]//2) * (shape[1]//2), 32)
            self.fc2 = nn.Linear(32, 1)
            
        def forward(self, x):
            x = self.pool(self.relu(self.conv1(x)))
            x = x.view(x.size(0), -1)
            x = self.relu(self.fc1(x))
            x = self.fc2(x)
            return x
            
    model = CNN()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCEWithLogitsLoss()
    
    best_acc = 0
    for epoch in range(20):
        model.train()
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            predictions = model(batch_x).squeeze(1)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            
        model.eval()
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                predictions = model(batch_x).squeeze(1)
                preds = torch.round(torch.sigmoid(predictions))
                all_preds.extend(preds.numpy())
                all_labels.extend(batch_y.numpy())
                
        acc = balanced_accuracy_score(all_labels, all_preds)
        if acc > best_acc:
            best_acc = acc
    print(f'Best Val Balanced Acc: {best_acc:.4f}')
