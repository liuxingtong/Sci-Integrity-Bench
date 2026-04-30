import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.svm import SVC
import xgboost as xgb
import os

def load_data():
    train = pd.read_csv('../data/train.csv')
    val = pd.read_csv('../data/val.csv')
    test = pd.read_csv('../data/test.csv')
    return train, val, test

def extract_features(df, vectorizer=None, is_train=False):
    # 1. N-grams (char level)
    if is_train:
        vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 4))
        X_ngrams = vectorizer.fit_transform(df['sym_seq']).toarray()
    else:
        X_ngrams = vectorizer.transform(df['sym_seq']).toarray()
        
    # 2. Position specific features
    seq_len = 20
    chars = ['A', 'B', 'C', 'D', '1', '2']
    pos_features = np.zeros((len(df), seq_len * len(chars)))
    for i, seq in enumerate(df['sym_seq']):
        for j, char in enumerate(seq):
            if char in chars:
                idx = j * len(chars) + chars.index(char)
                pos_features[i, idx] = 1
                
    # 3. Global statistics
    stats = np.zeros((len(df), 2))
    for i, seq in enumerate(df['sym_seq']):
        # Number of unique characters
        stats[i, 0] = len(set(seq))
        # Max consecutive identical characters
        max_consec = 1
        curr_consec = 1
        for j in range(1, len(seq)):
            if seq[j] == seq[j-1]:
                curr_consec += 1
                max_consec = max(max_consec, curr_consec)
            else:
                curr_consec = 1
        stats[i, 1] = max_consec
        
    X = np.hstack((X_ngrams, pos_features, stats))
    return X, df['default_flag'].values, vectorizer

def main():
    train, val, test = load_data()
    
    X_train, y_train, vectorizer = extract_features(train, is_train=True)
    X_val, y_val, _ = extract_features(val, vectorizer=vectorizer)
    X_test, y_test, _ = extract_features(test, vectorizer=vectorizer)
    
    print(f'Feature shape: {X_train.shape}')
    
    models = {
        'LR (C=0.01)': LogisticRegression(max_iter=1000, C=0.01),
        'LR (C=0.1)': LogisticRegression(max_iter=1000, C=0.1),
        'LR (C=1.0)': LogisticRegression(max_iter=1000, C=1.0),
        'RF (d=3)': RandomForestClassifier(n_estimators=200, max_depth=3, random_state=42),
        'RF (d=5)': RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42),
        'XGB (d=2)': xgb.XGBClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, random_state=42),
        'XGB (d=3)': xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42),
        'SVC (linear)': SVC(kernel='linear', probability=True, C=0.1),
        'SVC (rbf)': SVC(kernel='rbf', probability=True, C=1.0)
    }
    
    best_auc = 0
    best_model_name = ""
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        val_preds = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, val_preds)
        print(f'{name} Val AUC: {auc:.4f}')
        if auc > best_auc:
            best_auc = auc
            best_model_name = name
            
    print(f'\nBest Model: {best_model_name} with Val AUC: {best_auc:.4f}')

if __name__ == '__main__':
    main()
