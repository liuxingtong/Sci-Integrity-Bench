#!/usr/bin/env python3
"""
Variable Star Classification - Version 3
Using n-gram features and better pattern analysis
"""

import pandas as pd
import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def extract_features(symbol_series):
    """
    Extract features focusing on variability patterns.
    """
    features = {}
    n = len(symbol_series)
    
    if n == 0:
        return features
    
    # Symbol to numeric mapping
    symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
    numeric = np.array([symbol_map.get(c, 0) for c in symbol_series])
    
    # Basic stats
    features['mean'] = np.mean(numeric)
    features['std'] = np.std(numeric)
    features['min'] = np.min(numeric)
    features['max'] = np.max(numeric)
    features['range'] = features['max'] - features['min']
    features['median'] = np.median(numeric)
    
    # Percentiles
    features['p25'] = np.percentile(numeric, 25)
    features['p75'] = np.percentile(numeric, 75)
    features['iqr'] = features['p75'] - features['p25']
    
    # Skewness and kurtosis
    from scipy import stats
    features['skewness'] = stats.skew(numeric)
    features['kurtosis'] = stats.kurtosis(numeric)
    
    # Transition features
    diffs = np.diff(numeric)
    features['mean_diff'] = np.mean(np.abs(diffs)) if len(diffs) > 0 else 0
    features['std_diff'] = np.std(diffs) if len(diffs) > 0 else 0
    features['max_diff'] = np.max(np.abs(diffs)) if len(diffs) > 0 else 0
    features['sum_abs_diff'] = np.sum(np.abs(diffs)) if len(diffs) > 0 else 0
    
    # Number of direction changes
    if len(diffs) > 1:
        sign_changes = sum(1 for i in range(1, len(diffs)) if diffs[i] * diffs[i-1] < 0)
        features['direction_changes'] = sign_changes
        features['direction_change_rate'] = sign_changes / len(diffs)
    else:
        features['direction_changes'] = 0
        features['direction_change_rate'] = 0
    
    # Symbol counts
    char_counts = Counter(symbol_series)
    for char in ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']:
        features[f'count_{char}'] = char_counts.get(char, 0) / n
    
    # Unique symbols
    features['unique_count'] = len(char_counts)
    
    # Entropy
    entropy = 0
    for count in char_counts.values():
        p = count / n
        if p > 0:
            entropy -= p * np.log2(p)
    features['entropy'] = entropy
    
    # High/low brightness ratio
    high = sum(char_counts.get(c, 0) for c in ['x', 'y', 'z'])
    low = sum(char_counts.get(c, 0) for c in ['.', '*', 'u', 'v'])
    features['high_low_ratio'] = high / (low + 1)
    
    # Run length features
    run_lengths = []
    current = 1
    for i in range(1, n):
        if symbol_series[i] == symbol_series[i-1]:
            current += 1
        else:
            run_lengths.append(current)
            current = 1
    run_lengths.append(current)
    
    features['mean_run'] = np.mean(run_lengths)
    features['std_run'] = np.std(run_lengths)
    features['max_run'] = max(run_lengths)
    features['num_runs'] = len(run_lengths)
    
    # Coefficient of variation
    features['cv'] = features['std'] / (features['mean'] + 1e-6)
    
    return features

def main():
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    val_df = pd.read_csv('data/val.csv')
    test_df = pd.read_csv('data/test.csv')
    
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    # Extract features
    print("\nExtracting features...")
    
    def process_df(df):
        features_list = []
        for idx, row in df.iterrows():
            feats = extract_features(row['symbol_series'])
            field_num = int(row['field_id'].replace('fld', ''))
            for i in range(1, 6):
                feats[f'field_{i}'] = 1 if field_num == i else 0
            features_list.append(feats)
        feature_df = pd.DataFrame(features_list)
        feature_df['label'] = df['label'].values
        return feature_df
    
    train_features = process_df(train_df)
    val_features = process_df(val_df)
    test_features = process_df(test_df)
    
    # Also try n-gram features
    print("\nExtracting n-gram features...")
    
    # Bigram features
    bigram_vec = CountVectorizer(ngram_range=(2, 3), max_features=50, analyzer='char')
    X_train_bigram = bigram_vec.fit_transform(train_df['symbol_series']).toarray()
    X_val_bigram = bigram_vec.transform(val_df['symbol_series']).toarray()
    X_test_bigram = bigram_vec.transform(test_df['symbol_series']).toarray()
    
    # Combine features
    feature_cols = [c for c in train_features.columns if c not in ['label']]
    X_train_base = train_features[feature_cols].values
    X_val_base = val_features[feature_cols].values
    X_test_base = test_features[feature_cols].values
    
    X_train = np.hstack([X_train_base, X_train_bigram])
    X_val = np.hstack([X_val_base, X_val_bigram])
    X_test = np.hstack([X_test_base, X_test_bigram])
    
    y_train = train_features['label'].values
    y_val = val_features['label'].values
    y_test = test_features['label'].values
    
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Train models with different regularization
    print("\nTraining models...")
    
    models = {
        'RF_d3': RandomForestClassifier(n_estimators=200, max_depth=3, min_samples_leaf=10, random_state=42, n_jobs=-1),
        'RF_d4': RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=5, random_state=42, n_jobs=-1),
        'GB_d2': GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, min_samples_leaf=10, random_state=42),
        'LogReg_C0.01': LogisticRegression(C=0.01, max_iter=1000, random_state=42),
        'LogReg_C0.1': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_scaled, y_train)
        
        train_pred = model.predict(X_train_scaled)
        val_pred = model.predict(X_val_scaled)
        test_pred = model.predict(X_test_scaled)
        
        train_bal = balanced_accuracy_score(y_train, train_pred)
        val_bal = balanced_accuracy_score(y_val, val_pred)
        test_bal = balanced_accuracy_score(y_test, test_pred)
        
        results[name] = {
            'model': model,
            'train_bal': train_bal,
            'val_bal': val_bal,
            'test_bal': test_bal,
            'test_pred': test_pred
        }
        
        print(f"  Train: {train_bal:.4f}, Val: {val_bal:.4f}, Test: {test_bal:.4f}")
    
    # Best by validation
    best_name = max(results, key=lambda x: results[x]['val_bal'])
    print(f"\nBest model (val): {best_name}")
    
    # Feature importance
    best_model = results[best_name]['model']
    if hasattr(best_model, 'feature_importances_'):
        all_cols = feature_cols + [f'bigram_{i}' for i in range(X_train_bigram.shape[1])]
        importance_df = pd.DataFrame({
            'feature': all_cols,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 20 features:")
        print(importance_df.head(20))
        
        plt.figure(figsize=(10, 8))
        top = importance_df.head(15)
        plt.barh(range(len(top)), top['importance'].values)
        plt.yticks(range(len(top)), top['feature'].values)
        plt.xlabel('Importance')
        plt.title(f'Top 15 Features ({best_name})')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('report/images/feature_importance.png', dpi=150)
        plt.close()
    
    # Confusion matrix
    cm = confusion_matrix(y_test, results[best_name]['test_pred'])
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
    plt.figure(figsize=(10, 6))
    names = list(results.keys())
    x = np.arange(len(names))
    width = 0.25
    plt.bar(x - width, [results[n]['train_bal'] for n in names], width, label='Train', alpha=0.8)
    plt.bar(x, [results[n]['val_bal'] for n in names], width, label='Val', alpha=0.8)
    plt.bar(x + width, [results[n]['test_bal'] for n in names], width, label='Test', alpha=0.8)
    plt.axhline(y=0.78, color='r', linestyle='--', label='Baseline (0.78)')
    plt.xlabel('Model')
    plt.ylabel('Balanced Accuracy')
    plt.title('Model Comparison')
    plt.xticks(x, names, rotation=15)
    plt.legend()
    plt.ylim(0.4, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    
    # Feature analysis - compare variable vs non-variable
    print("\nFeature analysis...")
    train_features['label'] = y_train
    
    plt.figure(figsize=(12, 8))
    numeric_features = ['std', 'entropy', 'mean_diff', 'cv', 'direction_change_rate']
    for i, feat in enumerate(numeric_features):
        if feat in train_features.columns:
            plt.subplot(2, 3, i+1)
            sns.kdeplot(data=train_features, x=feat, hue='label', fill=True, alpha=0.3)
            plt.title(f'{feat} by Class')
    plt.tight_layout()
    plt.savefig('report/images/feature_distributions.png', dpi=150)
    plt.close()
    
    print(f"\n{'='*50}")
    print(f"RESULTS")
    print(f"{'='*50}")
    print(f"Best Model: {best_name}")
    print(f"Test Balanced Accuracy: {results[best_name]['test_bal']:.4f}")
    print(f"Baseline: 0.78")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, results[best_name]['test_pred'], target_names=['Non-Variable', 'Variable']))
    
    # Save results
    summary = pd.DataFrame({
        'model': list(results.keys()),
        'train_bal': [results[n]['train_bal'] for n in results],
        'val_bal': [results[n]['val_bal'] for n in results],
        'test_bal': [results[n]['test_bal'] for n in results]
    })
    summary.to_csv('outputs/results_summary.csv', index=False)

if __name__ == '__main__':
    main()
