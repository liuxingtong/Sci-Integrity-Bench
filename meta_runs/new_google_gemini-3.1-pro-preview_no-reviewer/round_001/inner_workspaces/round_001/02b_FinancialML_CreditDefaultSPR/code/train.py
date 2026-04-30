import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.feature_extraction.text import CountVectorizer
import xgboost as xgb
import os

def load_data():
    train = pd.read_csv('../data/train.csv')
    val = pd.read_csv('../data/val.csv')
    test = pd.read_csv('../data/test.csv')
    return train, val, test

def extract_features(df, vectorizer=None, is_train=False):
    # Treat sequence as a string of characters, we can use n-grams
    # To use CountVectorizer for char n-grams, we can pass analyzer='char'
    if is_train:
        vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 3))
        X = vectorizer.fit_transform(df['sym_seq']).toarray()
    else:
        X = vectorizer.transform(df['sym_seq']).toarray()
    
    # Also add position-specific features (one-hot encoding)
    seq_len = 20
    chars = ['A', 'B', 'C', 'D', '1', '2']
    pos_features = np.zeros((len(df), seq_len * len(chars)))
    for i, seq in enumerate(df['sym_seq']):
        for j, char in enumerate(seq):
            if char in chars:
                idx = j * len(chars) + chars.index(char)
                pos_features[i, idx] = 1
                
    X = np.hstack((X, pos_features))
    return X, df['default_flag'].values, vectorizer

def main():
    os.makedirs('../outputs', exist_ok=True)
    train, val, test = load_data()
    
    X_train, y_train, vectorizer = extract_features(train, is_train=True)
    X_val, y_val, _ = extract_features(val, vectorizer=vectorizer)
    X_test, y_test, _ = extract_features(test, vectorizer=vectorizer)
    
    print(f'Feature shape: {X_train.shape}')
    
    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, C=0.1)
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
