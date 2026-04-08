#!/usr/bin/env python3
"""
Variable Star Classification - Version 9
Try different approaches including string-based methods
"""

import pandas as pd
import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer, HashingVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def main():
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    val_df = pd.read_csv('data/val.csv')
    test_df = pd.read_csv('data/test.csv')
    
    y_train = train_df['label'].values
    y_val = val_df['label'].values
    y_test = test_df['label'].values
    
    # Check if there's a simple heuristic
    print("\n=== Checking Simple Heuristics ===")
    
    # Try simple rules based on symbol frequencies
    def simple_rule(series):
        # Variable stars might have more diverse symbols
        unique = len(set(series))
        return 1 if unique >= 8 else 0
    
    val_pred = [simple_rule(s) for s in val_df['symbol_series']]
    test_pred = [simple_rule(s) for s in test_df['symbol_series']]
    print(f"Simple rule (unique >= 8): Val={balanced_accuracy_score(y_val, val_pred):.4f}, Test={balanced_accuracy_score(y_test, test_pred):.4f}")
    
    # Try based on transition rate
    def transition_rate(series):
        if len(series) < 2:
            return 0
        changes = sum(1 for i in range(1, len(series)) if series[i] != series[i-1])
        return changes / (len(series) - 1)
    
    val_trans = [transition_rate(s) for s in val_df['symbol_series']]
    test_trans = [transition_rate(s) for s in test_df['symbol_series']]
    
    for thresh in [0.8, 0.85, 0.9, 0.95]:
        val_pred = [1 if t > thresh else 0 for t in val_trans]
        test_pred = [1 if t > thresh else 0 for t in test_trans]
        print(f"Transition rate > {thresh}: Val={balanced_accuracy_score(y_val, val_pred):.4f}, Test={balanced_accuracy_score(y_test, test_pred):.4f}")
    
    # Try based on entropy
    def entropy(series):
        n = len(series)
        if n == 0:
            return 0
        counts = Counter(series)
        ent = 0
        for c in counts.values():
            p = c / n
            if p > 0:
                ent -= p * np.log2(p)
        return ent
    
    val_ent = [entropy(s) for s in val_df['symbol_series']]
    test_ent = [entropy(s) for s in test_df['symbol_series']]
    
    for thresh in [2.5, 2.7, 2.9, 3.0]:
        val_pred = [1 if e > thresh else 0 for e in val_ent]
        test_pred = [1 if e > thresh else 0 for e in test_ent]
        print(f"Entropy > {thresh}: Val={balanced_accuracy_score(y_val, val_pred):.4f}, Test={balanced_accuracy_score(y_test, test_pred):.4f}")
    
    # Comprehensive feature extraction
    print("\n=== Comprehensive Features ===")
    
    def extract_all_features(series):
        features = {}
        n = len(series)
        if n == 0:
            return features
        
        # Symbol mapping
        sym_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
        numeric = np.array([sym_map.get(c, 0) for c in series])
        
        # Basic stats
        features['mean'] = np.mean(numeric)
        features['std'] = np.std(numeric)
        features['min'] = np.min(numeric)
        features['max'] = np.max(numeric)
        features['range'] = features['max'] - features['min']
        
        # Symbol frequencies
        counts = Counter(series)
        for c in '.*uvwxyz':
            features[f'f_{c}'] = counts.get(c, 0) / n
        
        # Entropy
        ent = 0
        for cnt in counts.values():
            p = cnt / n
            if p > 0:
                ent -= p * np.log2(p)
        features['entropy'] = ent
        
        # Unique count
        features['unique'] = len(counts)
        
        # Transitions
        diffs = np.diff(numeric)
        features['mean_diff'] = np.mean(np.abs(diffs)) if len(diffs) > 0 else 0
        features['sum_diff'] = np.sum(np.abs(diffs)) if len(diffs) > 0 else 0
        
        # Direction changes
        if len(diffs) > 1:
            sign_changes = sum(1 for i in range(1, len(diffs)) if diffs[i] * diffs[i-1] < 0)
            features['dir_changes'] = sign_changes / len(diffs)
        else:
            features['dir_changes'] = 0
        
        # Run lengths
        runs = []
        curr = 1
        for i in range(1, n):
            if series[i] == series[i-1]:
                curr += 1
            else:
                runs.append(curr)
                curr = 1
        runs.append(curr)
        features['mean_run'] = np.mean(runs)
        features['max_run'] = max(runs)
        features['num_runs'] = len(runs)
        
        # High/low
        high = sum(counts.get(c, 0) for c in 'xyz')
        low = sum(counts.get(c, 0) for c in '.*uv')
        features['high_ratio'] = high / n
        features['low_ratio'] = low / n
        
        return features
    
    def process(df):
        feats = []
        for idx, row in df.iterrows():
            f = extract_all_features(row['symbol_series'])
            fld = int(row['field_id'].replace('fld', ''))
            for i in range(1, 6):
                f[f'fld_{i}'] = 1 if fld == i else 0
            feats.append(f)
        return pd.DataFrame(feats)
    
    train_feat = process(train_df)
    val_feat = process(val_df)
    test_feat = process(test_df)
    
    feat_cols = list(train_feat.columns)
    X_train = train_feat[feat_cols].values
    X_val = val_feat[feat_cols].values
    X_test = test_feat[feat_cols].values
    
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)
    
    # Try HashingVectorizer (no vocabulary issues)
    print("\n=== HashingVectorizer ===")
    for n_feat in [50, 100, 200]:
        hv = HashingVectorizer(n_features=n_feat, analyzer='char', ngram_range=(1, 3), alternate_sign=False)
        X_train_h = hv.transform(train_df['symbol_series'])
        X_val_h = hv.transform(val_df['symbol_series'])
        X_test_h = hv.transform(test_df['symbol_series'])
        
        for clf_name, clf in [('LR', LogisticRegression(max_iter=1000))]:
            clf.fit(X_train_h, y_train)
            val_pred = clf.predict(X_val_h)
            test_pred = clf.predict(X_test_h)
            val_score = balanced_accuracy_score(y_val, val_pred)
            test_score = balanced_accuracy_score(y_test, test_pred)
            print(f"Hash({n_feat})_{clf_name}: Val={val_score:.4f}, Test={test_score:.4f}")
    
    # Try with more aggressive regularization
    print("\n=== Regularized Models ===")
    
    models = {
        'LR_C0.0001': LogisticRegression(C=0.0001, max_iter=1000),
        'LR_C0.001': LogisticRegression(C=0.001, max_iter=1000),
        'RF_d1': RandomForestClassifier(n_estimators=100, max_depth=1, min_samples_leaf=50),
        'RF_d2': RandomForestClassifier(n_estimators=100, max_depth=2, min_samples_leaf=30),
        'GB_d1': GradientBoostingClassifier(n_estimators=50, max_depth=1, learning_rate=0.01),
    }
    
    results = {}
    for name, model in models.items():
        model.fit(X_train_s, y_train)
        val_pred = model.predict(X_val_s)
        test_pred = model.predict(X_test_s)
        val_score = balanced_accuracy_score(y_val, val_pred)
        test_score = balanced_accuracy_score(y_test, test_pred)
        results[name] = {'val': val_score, 'test': test_score, 'pred': test_pred}
        print(f"{name}: Val={val_score:.4f}, Test={test_score:.4f}")
    
    # Best
    best_name = max(results, key=lambda x: results[x]['val'])
    print(f"\nBest: {best_name} -> Test={results[best_name]['test']:.4f}")
    
    final_result = results[best_name]
    
    # Feature importance
    if hasattr(final_result['model'] if 'model' in dir(final_result) else None, 'feature_importances_'):
        pass
    
    # Plots
    cm = confusion_matrix(y_test, final_result['pred'])
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
    
    plt.figure(figsize=(8, 5))
    all_labels = pd.concat([train_df['label'], val_df['label'], test_df['label']])
    sns.countplot(x='label', hue='label', data=pd.DataFrame({'label': all_labels}), palette='Set2', legend=False)
    plt.xlabel('Label')
    plt.ylabel('Count')
    plt.title('Class Distribution')
    plt.tight_layout()
    plt.savefig('report/images/class_distribution.png', dpi=150)
    plt.close()
    
    plt.figure(figsize=(10, 6))
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
    
    plt.figure(figsize=(12, 8))
    train_feat['label'] = y_train
    numeric_feats = ['std', 'entropy', 'mean_diff', 'dir_changes', 'high_ratio', 'low_ratio', 'mean_run']
    for i, feat in enumerate(numeric_feats):
        if feat in train_feat.columns:
            plt.subplot(3, 3, i+1)
            sns.kdeplot(data=train_feat, x=feat, hue='label', fill=True, alpha=0.3)
            plt.title(feat)
    plt.tight_layout()
    plt.savefig('report/images/feature_distributions.png', dpi=150)
    plt.close()
    
    print(f"\n{'='*50}")
    print(f"RESULTS")
    print(f"{'='*50}")
    print(f"Best Model: {best_name}")
    print(f"Test Balanced Accuracy: {final_result['test']:.4f}")
    print(f"Baseline: 0.78")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, final_result['pred'], target_names=['Non-Variable', 'Variable']))
    
    summary = pd.DataFrame({
        'model': list(results.keys()),
        'val': [results[n]['val'] for n in results],
        'test': [results[n]['test'] for n in results]
    })
    summary.to_csv('outputs/results_summary.csv', index=False)

if __name__ == '__main__':
    main()
