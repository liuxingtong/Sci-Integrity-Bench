import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer
import xgboost as xgb
import os

def load_data():
    train = pd.read_csv('../data/train.csv')
    val = pd.read_csv('../data/val.csv')
    test = pd.read_csv('../data/test.csv')
    return train, val, test

def extract_features(df, vectorizer=None, is_train=False):
    if is_train:
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 5))
        X = vectorizer.fit_transform(df['sym_seq']).toarray()
    else:
        X = vectorizer.transform(df['sym_seq']).toarray()
    
    return X, df['default_flag'].values, vectorizer

def main():
    train, val, test = load_data()
    
    X_train, y_train, vectorizer = extract_features(train, is_train=True)
    X_val, y_val, _ = extract_features(val, vectorizer=vectorizer)
    X_test, y_test, _ = extract_features(test, vectorizer=vectorizer)
    
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
