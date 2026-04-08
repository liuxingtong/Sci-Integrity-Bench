#!/usr/bin/env python3
"""
Variable Star Classification - Version 5
Deeper analysis of symbol patterns
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
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_curve, auc
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def analyze_patterns():
    """Analyze what distinguishes variable from non-variable stars"""
    train_df = pd.read_csv('data/train.csv')
    
    # Separate by class
    var_df = train_df[train_df['label'] == 1]
    nonvar_df = train_df[train_df['label'] == 0]
    
    print("=== Pattern Analysis ===")
    print(f"Variable stars: {len(var_df)}, Non-variable: {len(nonvar_df)}")
    
    # Analyze symbol distributions
    all_var_symbols = ''.join(var_df['symbol_series'])
    all_nonvar_symbols = ''.join(nonvar_df['symbol_series'])
    
    var_counts = Counter(all_var_symbols)
    nonvar_counts = Counter(all_nonvar_symbols)
    
    print("\nSymbol distribution comparison:")
    all_chars = sorted(set(all_var_symbols) | set(all_nonvar_symbols))
    for c in all_chars:
        var_ratio = var_counts[c] / len(all_var_symbols)
        nonvar_ratio = nonvar_counts[c] / len(all_nonvar_symbols)
        diff = var_ratio - nonvar_ratio
        print(f"  {c}: Var={var_ratio:.4f}, NonVar={nonvar_ratio:.4f}, Diff={diff:+.4f}")
    
    # Analyze sequence properties
    def get_seq_stats(series_list):
        stats = {
            'lengths': [],
            'unique_counts': [],
            'transitions': [],
            'star_runs': [],
            'dot_runs': []
        }
        for series in series_list:
            stats['lengths'].append(len(series))
            stats['unique_counts'].append(len(set(series)))
            
            # Transitions
            trans = sum(1 for i in range(1, len(series)) if series[i] != series[i-1])
            stats['transitions'].append(trans / (len(series) - 1) if len(series) > 1 else 0)
            
            # Star runs
            star_run = 0
            in_run = False
            for c in series:
                if c == '*':
                    if not in_run:
                        star_run += 1
                        in_run = True
                else:
                    in_run = False
            stats['star_runs'].append(star_run)
            
            # Dot runs
            dot_run = 0
            in_run = False
            for c in series:
                if c == '.':
                    if not in_run:
                        dot_run += 1
                        in_run = True
                else:
                    in_run = False
            stats['dot_runs'].append(dot_run)
        
        return stats
    
    var_stats = get_seq_stats(var_df['symbol_series'])
    nonvar_stats = get_seq_stats(nonvar_df['symbol_series'])
    
    print("\nSequence statistics:")
    print(f"  Length - Var: {np.mean(var_stats['lengths']):.1f}, NonVar: {np.mean(nonvar_stats['lengths']):.1f}")
    print(f"  Unique - Var: {np.mean(var_stats['unique_counts']):.2f}, NonVar: {np.mean(nonvar_stats['unique_counts']):.2f}")
    print(f"  Transition rate - Var: {np.mean(var_stats['transitions']):.3f}, NonVar: {np.mean(nonvar_stats['transitions']):.3f}")
    print(f"  Star runs - Var: {np.mean(var_stats['star_runs']):.2f}, NonVar: {np.mean(nonvar_stats['star_runs']):.2f}")
    print(f"  Dot runs - Var: {np.mean(var_stats['dot_runs']):.2f}, NonVar: {np.mean(nonvar_stats['dot_runs']):.2f}")

def extract_comprehensive_features(symbol_series):
    """Extract comprehensive features from symbol series"""
    features = {}
    n = len(symbol_series)
    if n == 0:
        return features
    
    # Symbol mapping
    sym_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
    numeric = np.array([sym_map.get(c, 0) for c in symbol_series])
    
    # Basic stats
    features['mean'] = np.mean(numeric)
    features['std'] = np.std(numeric)
    features['min'] = np.min(numeric)
    features['max'] = np.max(numeric)
    features['range'] = features['max'] - features['min']
    features['median'] = np.median(numeric)
    features['p10'] = np.percentile(numeric, 10)
    features['p90'] = np.percentile(numeric, 90)
    
    # Symbol counts (normalized)
    counts = Counter(symbol_series)
    for c in '.*uvwxyz':
        features[f'freq_{c}'] = counts.get(c, 0) / n
    
    # Unique count
    features['unique'] = len(counts)
    
    # Entropy
    entropy = 0
    for cnt in counts.values():
        p = cnt / n
        if p > 0:
            entropy -= p * np.log2(p)
    features['entropy'] = entropy
    
    # Transition features
    diffs = np.diff(numeric)
    features['mean_abs_diff'] = np.mean(np.abs(diffs)) if len(diffs) > 0 else 0
    features['std_diff'] = np.std(diffs) if len(diffs) > 0 else 0
    features['sum_abs_diff'] = np.sum(np.abs(diffs)) if len(diffs) > 0 else 0
    
    # Direction changes
    if len(diffs) > 1:
        sign_changes = sum(1 for i in range(1, len(diffs)) if diffs[i] * diffs[i-1] < 0)
        features['dir_changes'] = sign_changes / len(diffs)
    else:
        features['dir_changes'] = 0
    
    # Run length stats
    runs = []
    curr = 1
    for i in range(1, n):
        if symbol_series[i] == symbol_series[i-1]:
            curr += 1
        else:
            runs.append(curr)
            curr = 1
    runs.append(curr)
    
    features['mean_run'] = np.mean(runs)
    features['std_run'] = np.std(runs)
    features['max_run'] = max(runs)
    features['num_runs'] = len(runs)
    features['run_entropy'] = 0
    run_counts = Counter(runs)
    for rc in run_counts.values():
        p = rc / len(runs)
        if p > 0:
            features['run_entropy'] -= p * np.log2(p)
    
    # High/low brightness
    high = sum(counts.get(c, 0) for c in 'xyz')
    mid = sum(counts.get(c, 0) for c in 'uvw')
    low = sum(counts.get(c, 0) for c in '.*')
    features['high_ratio'] = high / n
    features['mid_ratio'] = mid / n
    features['low_ratio'] = low / n
    features['high_low'] = high / (low + 1)
    
    # Specific patterns
    features['n_stars'] = counts.get('*', 0)
    features['n_dots'] = counts.get('.', 0)
    
    # Consecutive same symbol (max)
    features['max_consec'] = max(runs)
    
    # Variability index (combination of features)
    features['var_index'] = features['std'] * features['entropy'] * features['dir_changes']
    
    return features

def main():
    # First, analyze patterns
    analyze_patterns()
    
    print("\n" + "="*50)
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    val_df = pd.read_csv('data/val.csv')
    test_df = pd.read_csv('data/test.csv')
    
    y_train = train_df['label'].values
    y_val = val_df['label'].values
    y_test = test_df['label'].values
    
    # Extract features
    print("\nExtracting features...")
    
    def process(df):
        feats = []
        for idx, row in df.iterrows():
            f = extract_comprehensive_features(row['symbol_series'])
            # Field encoding
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
    
    # Scale
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)
    
    # Try many models with different hyperparameters
    print("\nTraining models...")
    
    models = {
        'RF_d2': RandomForestClassifier(n_estimators=200, max_depth=2, min_samples_leaf=20, random_state=42, n_jobs=-1),
        'RF_d3': RandomForestClassifier(n_estimators=200, max_depth=3, min_samples_leaf=10, random_state=42, n_jobs=-1),
        'RF_d4': RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=5, random_state=42, n_jobs=-1),
        'ET_d2': ExtraTreesClassifier(n_estimators=200, max_depth=2, min_samples_leaf=20, random_state=42, n_jobs=-1),
        'ET_d3': ExtraTreesClassifier(n_estimators=200, max_depth=3, min_samples_leaf=10, random_state=42, n_jobs=-1),
        'GB_d2': GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, min_samples_leaf=20, random_state=42),
        'GB_d3': GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, min_samples_leaf=10, random_state=42),
        'LR_C0.01': LogisticRegression(C=0.01, max_iter=1000, random_state=42),
        'LR_C0.1': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
        'LR_C1': LogisticRegression(C=1.0, max_iter=1000, random_state=42),
        'KNN_5': KNeighborsClassifier(n_neighbors=5),
        'KNN_10': KNeighborsClassifier(n_neighbors=10),
        'KNN_20': KNeighborsClassifier(n_neighbors=20),
    }
    
    results = {}
    for name, model in models.items():
        model.fit(X_train_s, y_train)
        val_pred = model.predict(X_val_s)
        test_pred = model.predict(X_test_s)
        val_bal = balanced_accuracy_score(y_val, val_pred)
        test_bal = balanced_accuracy_score(y_test, test_pred)
        results[name] = {'val': val_bal, 'test': test_bal, 'pred': test_pred, 'model': model}
        print(f"{name}: Val={val_bal:.4f}, Test={test_bal:.4f}")
    
    # Best by validation
    best_name = max(results, key=lambda x: results[x]['val'])
    print(f"\nBest (val): {best_name} -> Val={results[best_name]['val']:.4f}, Test={results[best_name]['test']:.4f}")
    
    # Feature importance
    best_model = results[best_name]['model']
    if hasattr(best_model, 'feature_importances_'):
        imp_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 15 features:")
        print(imp_df.head(15))
        
        plt.figure(figsize=(10, 8))
        top = imp_df.head(15)
        plt.barh(range(len(top)), top['importance'].values)
        plt.yticks(range(len(top)), top['feature'].values)
        plt.xlabel('Importance')
        plt.title(f'Top Features ({best_name})')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('report/images/feature_importance.png', dpi=150)
        plt.close()
    
    # Confusion matrix
    cm = confusion_matrix(y_test, results[best_name]['pred'])
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
    plt.figure(figsize=(12, 6))
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
    plt.ylim(0.4, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    
    # Feature distributions
    plt.figure(figsize=(12, 8))
    train_feat['label'] = y_train
    numeric_feats = ['std', 'entropy', 'mean_abs_diff', 'dir_changes', 'high_ratio', 'low_ratio']
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
    print(f"Test Balanced Accuracy: {results[best_name]['test']:.4f}")
    print(f"Baseline: 0.78")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, results[best_name]['pred'], target_names=['Non-Variable', 'Variable']))
    
    # Save
    summary = pd.DataFrame({
        'model': list(results.keys()),
        'val': [results[n]['val'] for n in results],
        'test': [results[n]['test'] for n in results]
    })
    summary.to_csv('outputs/results_summary.csv', index=False)

if __name__ == '__main__':
    main()
