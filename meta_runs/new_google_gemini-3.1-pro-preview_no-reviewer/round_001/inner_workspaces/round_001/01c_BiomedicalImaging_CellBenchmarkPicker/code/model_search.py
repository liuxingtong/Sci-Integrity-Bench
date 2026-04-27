import pandas as pd
import numpy as np
import json
import os
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

datasets = ['D0001', 'D0002', 'D0013', 'D0014']

def pseudo_dice(y_true, y_pred):
    intersection = np.minimum(y_true, y_pred).sum()
    total_size = y_true.sum() + y_pred.sum()
    if total_size == 0:
        return 1.0
    return 2 * intersection / total_size

results = []

for ds in datasets:
    train_df = pd.read_csv(f'data/patches/{ds}/train.csv')
    val_df = pd.read_csv(f'data/patches/{ds}/val.csv')
    test_df = pd.read_csv(f'data/patches/{ds}/test.csv')
    
    X_train = train_df.drop(columns=['label'])
    y_train_class = train_df['label']
    y_train_frac = train_df['label'] / 3.0
    
    X_val = val_df.drop(columns=['label'])
    y_val_class = val_df['label']
    y_val_frac = val_df['label'] / 3.0
    
    X_test = test_df.drop(columns=['label'])
    y_test_class = test_df['label']
    y_test_frac = test_df['label'] / 3.0
    
    # Model 1: Logistic Regression
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train_class)
    lr_pred = lr.predict(X_test) / 3.0
    
    # Model 2: Ridge Regression
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train_frac)
    ridge_pred = np.clip(ridge.predict(X_test), 0, 1)
    
    # Model 3: MLP Classifier
    mlp = MLPClassifier(hidden_layer_sizes=(32,), max_iter=2000, random_state=42)
    mlp.fit(X_train, y_train_class)
    mlp_pred = mlp.predict(X_test) / 3.0
    
    # Model 4: Random Forest
    rf = RandomForestClassifier(n_estimators=50, random_state=42)
    rf.fit(X_train, y_train_class)
    rf_pred = rf.predict(X_test) / 3.0
    
    results.append({
        'dataset': ds,
        'LR_Dice': pseudo_dice(y_test_frac, lr_pred),
        'Ridge_Dice': pseudo_dice(y_test_frac, ridge_pred),
        'MLP_Dice': pseudo_dice(y_test_frac, mlp_pred),
        'RF_Dice': pseudo_dice(y_test_frac, rf_pred)
    })

results_df = pd.DataFrame(results)
print(results_df)
