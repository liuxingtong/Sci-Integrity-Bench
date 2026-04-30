import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb
import os

def load_data():
    train = pd.read_csv('../data/train.csv')
    val = pd.read_csv('../data/val.csv')
    test = pd.read_csv('../data/test.csv')
    return train, val, test

def extract_features(df):
    chars = ['A', 'B', 'C', 'D', '1', '2']
    char_to_idx = {c: i for i, c in enumerate(chars)}
    
    # Transition counts
    n_chars = len(chars)
    X_trans = np.zeros((len(df), n_chars * n_chars))
    
    # Motif counts (length 3)
    # X_motifs = ...
    
    for i, seq in enumerate(df['sym_seq']):
        for j in range(len(seq) - 1):
            c1, c2 = seq[j], seq[j+1]
            if c1 in char_to_idx and c2 in char_to_idx:
                idx = char_to_idx[c1] * n_chars + char_to_idx[c2]
                X_trans[i, idx] += 1
                
    # Character counts
    X_counts = np.zeros((len(df), n_chars))
    for i, seq in enumerate(df['sym_seq']):
        for c in seq:
            if c in char_to_idx:
                X_counts[i, char_to_idx[c]] += 1
                
    X = np.hstack((X_trans, X_counts))
    return X, df['default_flag'].values

def main():
    train, val, test = load_data()
    
    X_train, y_train = extract_features(train)
    X_val, y_val = extract_features(val)
    X_test, y_test = extract_features(test)
    
    print(f'Feature shape: {X_train.shape}')
    
    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, C=1.0)
    lr.fit(X_train, y_train)
    val_preds_lr = lr.predict_proba(X_val)[:, 1]
    print(f'LR Val AUC: {roc_auc_score(y_val, val_preds_lr):.4f}')
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    val_preds_rf = rf.predict_proba(X_val)[:, 1]
    print(f'RF Val AUC: {roc_auc_score(y_val, val_preds_rf):.4f}')
    
    # XGBoost
    xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    xgb_model.fit(X_train, y_train)
    val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
    print(f'XGB Val AUC: {roc_auc_score(y_val, val_preds_xgb):.4f}')

if __name__ == '__main__':
    main()
