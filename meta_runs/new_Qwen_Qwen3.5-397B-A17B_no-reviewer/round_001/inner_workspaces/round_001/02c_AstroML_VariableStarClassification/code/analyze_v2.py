#!/usr/bin/env python3
"""
Variable Star Classification using Symbol Series Features - Version 2
Focus on variability patterns in symbolic light curves
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
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import os
import re

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def extract_variability_features(symbol_series):
    """
    Extract features that capture variability in the symbolic light curve.
    Variable stars should show more variation in brightness (different symbols).
    """
    features = {}
    n = len(symbol_series)
    
    if n == 0:
        return {f'feat_{i}': 0 for i in range(20)}
    
    # Map symbols to numeric values for analysis
    # Order: . < * < u < v < w < x < y < z (assuming alphabetical order represents brightness)
    symbol_order = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
    
    # Convert to numeric
    numeric = [symbol_order.get(c, 0) for c in symbol_series]
    numeric = np.array(numeric)
    
    # Basic statistics
    features['mean_brightness'] = np.mean(numeric)
    features['std_brightness'] = np.std(numeric)
    features['min_brightness'] = np.min(numeric)
    features['max_brightness'] = np.max(numeric)
    features['range_brightness'] = features['max_brightness'] - features['min_brightness']
    
    # Variability measures
    features['variance'] = np.var(numeric)
    
    # Count transitions (changes between consecutive symbols)
    transitions = sum(1 for i in range(1, n) if symbol_series[i] != symbol_series[i-1])
    features['transition_count'] = transitions
    features['transition_rate'] = transitions / (n - 1) if n > 1 else 0
    
    # Count large jumps (brightness changes > 2 levels)
    large_jumps = sum(1 for i in range(1, n) if abs(numeric[i] - numeric[i-1]) > 2)
    features['large_jump_count'] = large_jumps
    features['large_jump_rate'] = large_jumps / (n - 1) if n > 1 else 0
    
    # Symbol distribution
    char_counts = Counter(symbol_series)
    features['unique_symbols'] = len(char_counts)
    features['symbol_entropy'] = 0
    for count in char_counts.values():
        p = count / n
        if p > 0:
            features['symbol_entropy'] -= p * np.log2(p)
    
    # Dominant symbol ratio
    if char_counts:
        most_common = char_counts.most_common(1)[0]
        features['dominant_ratio'] = most_common[1] / n
    else:
        features['dominant_ratio'] = 0
    
    # Special character ratios
    features['star_ratio'] = char_counts.get('*', 0) / n
    features['dot_ratio'] = char_counts.get('.', 0) / n
    
    # High vs low brightness ratio
    high_symbols = sum(char_counts.get(c, 0) for c in ['y', 'z'])
    low_symbols = sum(char_counts.get(c, 0) for c in ['.', '*', 'u'])
    features['high_low_ratio'] = high_symbols / (low_symbols + 1)
    
    # Run length statistics (consecutive same symbols)
    run_lengths = []
    current_run = 1
    for i in range(1, n):
        if symbol_series[i] == symbol_series[i-1]:
            current_run += 1
        else:
            run_lengths.append(current_run)
            current_run = 1
    run_lengths.append(current_run)
    
    if run_lengths:
        features['mean_run_length'] = np.mean(run_lengths)
        features['std_run_length'] = np.std(run_lengths)
        features['max_run_length'] = max(run_lengths)
        features['min_run_length'] = min(run_lengths)
    else:
        features['mean_run_length'] = n
        features['std_run_length'] = 0
        features['max_run_length'] = n
        features['min_run_length'] = n
    
    # Autocorrelation-like measure (lag-1)
    if n > 1:
        lag1_corr = np.corrcoef(numeric[:-1], numeric[1:])[0, 1] if len(numeric) > 2 else 0
        features['lag1_correlation'] = lag1_corr if not np.isnan(lag1_corr) else 0
    else:
        features['lag1_correlation'] = 1
    
    return features

def main():
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    val_df = pd.read_csv('data/val.csv')
    test_df = pd.read_csv('data/test.csv')
    
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    print(f"Train label distribution: {train_df['label'].value_counts().to_dict()}")
    print(f"Val label distribution: {val_df['label'].value_counts().to_dict()}")
    print(f"Test label distribution: {test_df['label'].value_counts().to_dict()}")
    
    # Extract features
    print("\nExtracting variability features...")
    
    def process_df(df):
        features_list = []
        for idx, row in df.iterrows():
            feats = extract_variability_features(row['symbol_series'])
            # Field ID encoding
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
    
    feature_cols = [c for c in train_features.columns if c not in ['label']]
    
    X_train = train_features[feature_cols].values
    y_train = train_features['label'].values
    X_val = val_features[feature_cols].values
    y_val = val_features['label'].values
    X_test = test_features[feature_cols].values
    y_test = test_features['label'].values
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Try different models with regularization
    print("\nTraining models...")
    
    models = {
        'RF_shallow': RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42, n_jobs=-1),
        'RF_medium': RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1),
        'GB_shallow': GradientBoostingClassifier(n_estimators=50, max_depth=2, learning_rate=0.1, random_state=42),
        'LogReg_L2': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
        'SVM_rbf': SVC(kernel='rbf', C=1.0, gamma='scale', random_state=42)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_scaled, y_train)
        
        train_pred = model.predict(X_train_scaled)
        val_pred = model.predict(X_val_scaled)
        test_pred = model.predict(X_test_scaled)
        
        train_bal_acc = balanced_accuracy_score(y_train, train_pred)
        val_bal_acc = balanced_accuracy_score(y_val, val_pred)
        test_bal_acc = balanced_accuracy_score(y_test, test_pred)
        
        results[name] = {
            'model': model,
            'train_bal_acc': train_bal_acc,
            'val_bal_acc': val_bal_acc,
            'test_bal_acc': test_bal_acc,
            'test_pred': test_pred
        }
        
        print(f"  Train: {train_bal_acc:.4f}, Val: {val_bal_acc:.4f}, Test: {test_bal_acc:.4f}")
    
    # Find best model based on validation
    best_model_name = max(results, key=lambda x: results[x]['val_bal_acc'])
    print(f"\nBest model (by val): {best_model_name}")
    
    # Also check best test performance
    best_test_name = max(results, key=lambda x: results[x]['test_bal_acc'])
    print(f"Best model (by test): {best_test_name}")
    
    # Feature importance
    best_model = results[best_model_name]['model']
    if hasattr(best_model, 'feature_importances_'):
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop features:")
        print(importance_df.head(15))
        
        plt.figure(figsize=(10, 8))
        top_features = importance_df.head(15)
        plt.barh(range(len(top_features)), top_features['importance'].values)
        plt.yticks(range(len(top_features)), top_features['feature'].values)
        plt.xlabel('Importance')
        plt.title(f'Top 15 Feature Importances ({best_model_name})')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('report/images/feature_importance.png', dpi=150)
        plt.close()
    
    # Confusion matrix
    best_test_pred = results[best_model_name]['test_pred']
    cm = confusion_matrix(y_test, best_test_pred)
    
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Non-Variable (0)', 'Variable (1)'],
                yticklabels=['Non-Variable (0)', 'Variable (1)'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(f'Confusion Matrix - Test Set ({best_model_name})')
    plt.tight_layout()
    plt.savefig('report/images/confusion_matrix.png', dpi=150)
    plt.close()
    
    # Class distribution
    plt.figure(figsize=(8, 5))
    all_labels = pd.concat([train_df['label'], val_df['label'], test_df['label']])
    sns.countplot(x='label', hue='label', data=pd.DataFrame({'label': all_labels}), palette='Set2', legend=False)
    plt.xlabel('Label (0=Non-Variable, 1=Variable)')
    plt.ylabel('Count')
    plt.title('Class Distribution Across All Splits')
    plt.tight_layout()
    plt.savefig('report/images/class_distribution.png', dpi=150)
    plt.close()
    
    # Model comparison
    plt.figure(figsize=(10, 6))
    model_names = list(results.keys())
    train_scores = [results[m]['train_bal_acc'] for m in model_names]
    val_scores = [results[m]['val_bal_acc'] for m in model_names]
    test_scores = [results[m]['test_bal_acc'] for m in model_names]
    
    x = np.arange(len(model_names))
    width = 0.25
    
    plt.bar(x - width, train_scores, width, label='Train', alpha=0.8)
    plt.bar(x, val_scores, width, label='Validation', alpha=0.8)
    plt.bar(x + width, test_scores, width, label='Test', alpha=0.8)
    
    plt.axhline(y=0.78, color='r', linestyle='--', label='Baseline (0.78)')
    
    plt.xlabel('Model')
    plt.ylabel('Balanced Accuracy')
    plt.title('Model Comparison - Balanced Accuracy')
    plt.xticks(x, model_names, rotation=15)
    plt.legend()
    plt.ylim(0.4, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    
    # Feature correlation heatmap
    plt.figure(figsize=(12, 10))
    corr_matrix = train_features[feature_cols].corr()
    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0)
    plt.title('Feature Correlation Matrix')
    plt.tight_layout()
    plt.savefig('report/images/feature_correlation.png', dpi=150)
    plt.close()
    
    print(f"\n{'='*50}")
    print(f"FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Best Model: {best_model_name}")
    print(f"Test Balanced Accuracy: {results[best_model_name]['test_bal_acc']:.4f}")
    print(f"Baseline: 0.78")
    
    print(f"\nClassification Report (Test Set):")
    print(classification_report(y_test, best_test_pred, target_names=['Non-Variable', 'Variable']))
    
    # Save summary
    summary = pd.DataFrame({
        'model': list(results.keys()),
        'train_bal_acc': [results[m]['train_bal_acc'] for m in results],
        'val_bal_acc': [results[m]['val_bal_acc'] for m in results],
        'test_bal_acc': [results[m]['test_bal_acc'] for m in results]
    })
    summary.to_csv('outputs/results_summary.csv', index=False)
    
    return results

if __name__ == '__main__':
    main()
