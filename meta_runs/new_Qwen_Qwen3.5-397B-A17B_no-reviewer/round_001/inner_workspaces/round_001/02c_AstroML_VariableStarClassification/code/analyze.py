#!/usr/bin/env python3
"""
Variable Star Classification using Symbol Series Features
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
import os

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def extract_features(symbol_series):
    features = {}
    features['length'] = len(symbol_series)
    char_counts = Counter(symbol_series)
    features['star_count'] = char_counts.get('*', 0)
    features['dot_count'] = char_counts.get('.', 0)
    letters = [c for c in symbol_series if c.isalpha()]
    features['letter_count'] = len(letters)
    features['unique_chars'] = len(set(symbol_series))
    
    if len(symbol_series) > 0:
        features['star_ratio'] = features['star_count'] / len(symbol_series)
        features['dot_ratio'] = features['dot_count'] / len(symbol_series)
        features['letter_ratio'] = features['letter_count'] / len(symbol_series)
    else:
        features['star_ratio'] = 0
        features['dot_ratio'] = 0
        features['letter_ratio'] = 0
    
    star_runs = 0
    in_star_run = False
    for c in symbol_series:
        if c == '*':
            if not in_star_run:
                star_runs += 1
                in_star_run = True
        else:
            in_star_run = False
    features['star_runs'] = star_runs
    
    dot_runs = 0
    in_dot_run = False
    for c in symbol_series:
        if c == '.':
            if not in_dot_run:
                dot_runs += 1
                in_dot_run = True
        else:
            in_dot_run = False
    features['dot_runs'] = dot_runs
    
    changes = sum(1 for i in range(1, len(symbol_series)) if symbol_series[i] != symbol_series[i-1])
    features['alternation_rate'] = changes / max(len(symbol_series) - 1, 1)
    
    if letters:
        letter_counts = Counter(letters)
        total = len(letters)
        entropy = 0
        for count in letter_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        features['letter_entropy'] = entropy
        most_common = letter_counts.most_common(1)[0][1] if letter_counts else 0
        features['max_letter_ratio'] = most_common / total if total > 0 else 0
    else:
        features['letter_entropy'] = 0
        features['max_letter_ratio'] = 0
    
    return features

def get_all_char_features(symbol_series, all_chars):
    char_counts = Counter(symbol_series)
    features = {}
    length = len(symbol_series) if len(symbol_series) > 0 else 1
    for char in all_chars:
        features[f'char_{char}'] = char_counts.get(char, 0) / length
    return features

def main():
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    val_df = pd.read_csv('data/val.csv')
    test_df = pd.read_csv('data/test.csv')
    
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    print(f"Train label distribution: {train_df['label'].value_counts().to_dict()}")
    
    print("\nExtracting features...")
    all_chars = set()
    for series in pd.concat([train_df, val_df, test_df])['symbol_series']:
        all_chars.update(series)
    all_chars = sorted(all_chars)
    print(f"Unique characters in data: {all_chars}")
    
    def process_dataframe(df, all_chars):
        features_list = []
        for idx, row in df.iterrows():
            feats = extract_features(row['symbol_series'])
            char_feats = get_all_char_features(row['symbol_series'], all_chars)
            feats.update(char_feats)
            field_num = int(row['field_id'].replace('fld', ''))
            for i in range(1, 6):
                feats[f'field_{i}'] = 1 if field_num == i else 0
            features_list.append(feats)
        feature_df = pd.DataFrame(features_list)
        feature_df['label'] = df['label'].values
        feature_df['object_id'] = df['object_id'].values
        return feature_df
    
    train_features = process_dataframe(train_df, all_chars)
    val_features = process_dataframe(val_df, all_chars)
    test_features = process_dataframe(test_df, all_chars)
    
    feature_cols = [c for c in train_features.columns if c not in ['label', 'object_id']]
    
    X_train = train_features[feature_cols].values
    y_train = train_features['label'].values
    X_val = val_features[feature_cols].values
    y_val = val_features['label'].values
    X_test = test_features[feature_cols].values
    y_test = test_features['label'].values
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    print("\nTraining models...")
    
    models = {
        'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
        'GradientBoosting': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42),
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42)
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
        
        print(f"  Train balanced accuracy: {train_bal_acc:.4f}")
        print(f"  Val balanced accuracy: {val_bal_acc:.4f}")
        print(f"  Test balanced accuracy: {test_bal_acc:.4f}")
    
    best_model_name = max(results, key=lambda x: results[x]['val_bal_acc'])
    best_model = results[best_model_name]['model']
    print(f"\nBest model: {best_model_name}")
    
    if hasattr(best_model, 'feature_importances_'):
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 20 features:")
        print(importance_df.head(20))
        
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
    
    plt.figure(figsize=(8, 5))
    all_labels = pd.concat([train_df['label'], val_df['label'], test_df['label']])
    sns.countplot(x='label', data=pd.DataFrame({'label': all_labels}), palette='Set2')
    plt.xlabel('Label (0=Non-Variable, 1=Variable)')
    plt.ylabel('Count')
    plt.title('Class Distribution Across All Splits')
    plt.tight_layout()
    plt.savefig('report/images/class_distribution.png', dpi=150)
    plt.close()
    
    plt.figure(figsize=(8, 5))
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
    plt.xticks(x, model_names)
    plt.legend()
    plt.ylim(0.5, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    
    print(f"\n{'='*50}")
    print(f"FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Best Model: {best_model_name}")
    print(f"Test Balanced Accuracy: {results[best_model_name]['test_bal_acc']:.4f}")
    print(f"Baseline: 0.78")
    print(f"Improvement: {results[best_model_name]['test_bal_acc'] - 0.78:.4f}")
    
    print(f"\nClassification Report (Test Set):")
    print(classification_report(y_test, best_test_pred, target_names=['Non-Variable', 'Variable']))
    
    return results

if __name__ == '__main__':
    main()
