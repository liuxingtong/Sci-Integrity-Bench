#!/usr/bin/env python3
"""
Variable Star Classification - Version 6
Focus on positional patterns and sequence structure
"""

import pandas as pd
import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, BernoulliNB
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def extract_positional_features(symbol_series):
    """Extract features based on position in sequence"""
    features = {}
    n = len(symbol_series)
    if n == 0:
        return features
    
    sym_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
    numeric = np.array([sym_map.get(c, 0) for c in symbol_series])
    
    # First half vs second half
    mid = n // 2
    first_half = numeric[:mid]
    second_half = numeric[mid:]
    
    features['first_mean'] = np.mean(first_half) if len(first_half) > 0 else 0
    features['second_mean'] = np.mean(second_half) if len(second_half) > 0 else 0
    features['half_diff'] = features['second_mean'] - features['first_mean']
    features['half_diff_abs'] = abs(features['half_diff'])
    
    # First quarter vs last quarter
    q = n // 4
    first_q = numeric[:q] if q > 0 else numeric[:1]
    last_q = numeric[-q:] if q > 0 else numeric[-1:]
    features['first_q_mean'] = np.mean(first_q)
    features['last_q_mean'] = np.mean(last_q)
    features['quarter_diff'] = features['last_q_mean'] - features['first_q_mean']
    
    # Edge vs center
    edge_len = max(1, n // 5)
    edges = np.concatenate([numeric[:edge_len], numeric[-edge_len:]])
    center = numeric[edge_len:-edge_len] if n > 2*edge_len else numeric
    features['edge_mean'] = np.mean(edges)
    features['center_mean'] = np.mean(center) if len(center) > 0 else 0
    features['edge_center_diff'] = features['edge_mean'] - features['center_mean']
    
    # Position-weighted statistics
    positions = np.arange(n)
    features['pos_weighted_mean'] = np.sum(numeric * positions) / np.sum(positions) if np.sum(positions) > 0 else 0
    
    # Trend (linear regression slope)
    if n > 1:
        slope = np.corrcoef(positions, numeric)[0, 1] if len(positions) > 1 else 0
        features['trend'] = slope if not np.isnan(slope) else 0
    else:
        features['trend'] = 0
    
    # Peaks and valleys
    peaks = 0
    valleys = 0
    for i in range(1, n-1):
        if numeric[i] > numeric[i-1] and numeric[i] > numeric[i+1]:
            peaks += 1
        if numeric[i] < numeric[i-1] and numeric[i] < numeric[i+1]:
            valleys += 1
    features['peaks'] = peaks / n
    features['valleys'] = valleys / n
    features['peak_valley_ratio'] = (peaks + 1) / (valleys + 1)
    
    return features

def extract_shape_features(symbol_series):
    """Extract shape-related features"""
    features = {}
    n = len(symbol_series)
    if n == 0:
        return features
    
    sym_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
    numeric = np.array([sym_map.get(c, 0) for c in symbol_series])
    
    # Moving average deviation
    window = 5
    if n >= window:
        ma = np.convolve(numeric, np.ones(window)/window, mode='valid')
        center_start = window // 2
        center_end = n - (window - 1 - center_start)
        if center_end > center_start:
            center_part = numeric[center_start:center_end]
            features['ma_deviation'] = np.mean(np.abs(center_part - ma)) if len(ma) > 0 else 0
        else:
            features['ma_deviation'] = 0
    else:
        features['ma_deviation'] = 0
    
    # Zero crossings (crossing the mean)
    mean_val = np.mean(numeric)
    centered = numeric - mean_val
    crossings = sum(1 for i in range(1, n) if centered[i] * centered[i-1] < 0)
    features['zero_crossings'] = crossings / n
    
    # Amplitude measures
    features['amplitude'] = np.max(numeric) - np.min(numeric)
    
    # RMS
    features['rms'] = np.sqrt(np.mean(numeric**2))
    
    # Crest factor
    features['crest_factor'] = np.max(np.abs(numeric)) / (features['rms'] + 1e-6)
    
    return features

def main():
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    val_df = pd.read_csv('data/val.csv')
    test_df = pd.read_csv('data/test.csv')
    
    y_train = train_df['label'].values
    y_val = val_df['label'].values
    y_test = test_df['label'].values
    
    # Extract all features
    print("\nExtracting features...")
    
    def process(df):
        feats = []
        for idx, row in df.iterrows():
            series = row['symbol_series']
            f = {}
            f.update(extract_positional_features(series))
            f.update(extract_shape_features(series))
            
            # Basic features
            n = len(series)
            sym_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
            numeric = np.array([sym_map.get(c, 0) for c in series])
            
            f['mean'] = np.mean(numeric)
            f['std'] = np.std(numeric)
            f['range'] = np.max(numeric) - np.min(numeric)
            
            counts = Counter(series)
            for c in '.*uvwxyz':
                f[f'freq_{c}'] = counts.get(c, 0) / n
            
            f['entropy'] = 0
            for cnt in counts.values():
                p = cnt / n
                if p > 0:
                    f['entropy'] -= p * np.log2(p)
            
            # Field
            fld = int(row['field_id'].replace('fld', ''))
            for i in range(1, 6):
                f[f'fld_{i}'] = 1 if fld == i else 0
            
            feats.append(f)
        return pd.DataFrame(feats)
    
    train_feat = process(train_df)
    val_feat = process(val_df)
    test_feat = process(test_df)
    
    feature_cols = [c for c in train_feat.columns]
    X_train = train_feat[feature_cols].values
    X_val = val_feat[feature_cols].values
    X_test = test_feat[feature_cols].values
    
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)
    
    # Try TF-IDF approach as well
    print("\nTrying TF-IDF approach...")
    tfidf = TfidfVectorizer(ngram_range=(2, 4), max_features=100, analyzer='char')
    X_train_tfidf = tfidf.fit_transform(train_df['symbol_series']).toarray()
    X_val_tfidf = tfidf.transform(val_df['symbol_series']).toarray()
    X_test_tfidf = tfidf.transform(test_df['symbol_series']).toarray()
    
    # Combine
    X_train_comb = np.hstack([X_train_s, X_train_tfidf])
    X_val_comb = np.hstack([X_val_s, X_val_tfidf])
    X_test_comb = np.hstack([X_test_s, X_test_tfidf])
    
    print("\nTraining models...")
    
    models = {
        'RF_d2': RandomForestClassifier(n_estimators=300, max_depth=2, min_samples_leaf=15, random_state=42, n_jobs=-1),
        'RF_d3': RandomForestClassifier(n_estimators=300, max_depth=3, min_samples_leaf=10, random_state=42, n_jobs=-1),
        'GB_d2': GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, min_samples_leaf=15, random_state=42),
        'LR_C0.01': LogisticRegression(C=0.01, max_iter=1000, random_state=42),
        'LR_C0.1': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
        'SVM_rbf': SVC(kernel='rbf', C=0.5, gamma='scale', random_state=42),
        'SVM_linear': SVC(kernel='linear', C=0.1, random_state=42),
        'NB': MultinomialNB(alpha=0.5),
        'AdaBoost': AdaBoostClassifier(n_estimators=50, learning_rate=0.5, random_state=42),
    }
    
    results = {}
    for name, model in models.items():
        if name == 'NB':
            # NB needs non-negative features
            X_tr = X_train_tfidf
            X_va = X_val_tfidf
            X_te = X_test_tfidf
        else:
            X_tr = X_train_s
            X_va = X_val_s
            X_te = X_test_s
        
        model.fit(X_tr, y_train)
        val_pred = model.predict(X_va)
        test_pred = model.predict(X_te)
        val_bal = balanced_accuracy_score(y_val, val_pred)
        test_bal = balanced_accuracy_score(y_test, test_pred)
        results[name] = {'val': val_bal, 'test': test_bal, 'pred': test_pred, 'model': model}
        print(f"{name}: Val={val_bal:.4f}, Test={test_bal:.4f}")
    
    # Combined features
    print("\nTrying combined features...")
    models_comb = {
        'RF_d2_comb': RandomForestClassifier(n_estimators=200, max_depth=2, min_samples_leaf=15, random_state=42, n_jobs=-1),
        'LR_C0.1_comb': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
    }
    
    for name, model in models_comb.items():
        model.fit(X_train_comb, y_train)
        val_pred = model.predict(X_val_comb)
        test_pred = model.predict(X_test_comb)
        val_bal = balanced_accuracy_score(y_val, val_pred)
        test_bal = balanced_accuracy_score(y_test, test_pred)
        results[name] = {'val': val_bal, 'test': test_bal, 'pred': test_pred, 'model': model}
        print(f"{name}: Val={val_bal:.4f}, Test={test_bal:.4f}")
    
    # Best
    best_name = max(results, key=lambda x: results[x]['val'])
    print(f"\nBest (val): {best_name} -> Val={results[best_name]['val']:.4f}, Test={results[best_name]['test']:.4f}")
    
    best_test_name = max(results, key=lambda x: results[x]['test'])
    print(f"Best (test): {best_test_name} -> Test={results[best_test_name]['test']:.4f}")
    
    # Use best validation for reporting
    best_result = results[best_name]
    
    # Feature importance
    if hasattr(best_result['model'], 'feature_importances_'):
        imp_df = pd.DataFrame({
            'feature': feature_cols if 'comb' not in best_name else list(range(X_train_comb.shape[1])),
            'importance': best_result['model'].feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop features:")
        print(imp_df.head(15))
        
        plt.figure(figsize=(10, 8))
        top = imp_df.head(15)
        plt.barh(range(len(top)), top['importance'].values)
        plt.yticks(range(len(top)), [str(f) for f in top['feature'].values])
        plt.xlabel('Importance')
        plt.title(f'Top Features ({best_name})')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('report/images/feature_importance.png', dpi=150)
        plt.close()
    
    # Confusion matrix
    cm = confusion_matrix(y_test, best_result['pred'])
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Non-Variable (0)', 'Variable (1)'],
                yticklabels=['Non-Variable (0)', 'Variable (1)'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(f'Confusion Matrix ({best_name})')
    plt.tight_layout()
    plt.savefig('report/images/confusion_matrix.png', dpi=150)
    plt.close()
    
    # Class distribution
    plt.figure(figsize=(8, 5))
    all_labels = pd.concat([train_df['label'], val_df['label'], test_df['label']])
    sns.countplot(x='label', hue='label', data=pd.DataFrame({'label': all_labels}), palette='Set2', legend=False)
    plt.xlabel('Label')
    plt.ylabel('Count')
    plt.title('Class Distribution')
    plt.tight_layout()
    plt.savefig('report/images/class_distribution.png', dpi=150)
    plt.close()
    
    # Model comparison
    plt.figure(figsize=(14, 6))
    names = list(results.keys())
    x = np.arange(len(names))
    width = 0.35
    plt.bar(x - width/2, [results[n]['val'] for n in names], width, label='Val', alpha=0.8)
    plt.bar(x + width/2, [results[n]['test'] for n in names], width, label='Test', alpha=0.8)
    plt.axhline(y=0.78, color='r', linestyle='--', label='Baseline (0.78)')
    plt.xlabel('Model')
    plt.ylabel('Balanced Accuracy')
    plt.title('Model Comparison')
    plt.xticks(x, names, rotation=45, ha='right')
    plt.legend()
    plt.ylim(0.35, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    
    # Feature distributions
    plt.figure(figsize=(12, 8))
    train_feat['label'] = y_train
    numeric_feats = ['std', 'entropy', 'trend', 'peaks', 'valleys', 'zero_crossings']
    for i, feat in enumerate(numeric_feats):
        if feat in train_feat.columns:
            plt.subplot(2, 3, i+1)
            sns.kdeplot(data=train_feat, x=feat, hue='label', fill=True, alpha=0.3)
            plt.title(feat)
    plt.tight_layout()
    plt.savefig('report/images/feature_distributions.png', dpi=150)
    plt.close()
    
    print(f"\n{'='*50}")
    print(f"RESULTS")
    print(f"{'='*50}")
    print(f"Best Model: {best_name}")
    print(f"Test Balanced Accuracy: {best_result['test']:.4f}")
    print(f"Baseline: 0.78")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, best_result['pred'], target_names=['Non-Variable', 'Variable']))
    
    # Save
    summary = pd.DataFrame({
        'model': list(results.keys()),
        'val': [results[n]['val'] for n in results],
        'test': [results[n]['test'] for n in results]
    })
    summary.to_csv('outputs/results_summary.csv', index=False)

if __name__ == '__main__':
    main()
