#!/usr/bin/env python3
"""
Variable Star Classification - Version 4
Try text-based approaches and simpler features
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
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def main():
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    val_df = pd.read_csv('data/val.csv')
    test_df = pd.read_csv('data/test.csv')
    
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    print(f"Train: {train_df['label'].value_counts().to_dict()}")
    print(f"Val: {val_df['label'].value_counts().to_dict()}")
    print(f"Test: {test_df['label'].value_counts().to_dict()}")
    
    # Approach 1: TF-IDF on symbol sequences
    print("\n=== Approach 1: TF-IDF ===")
    
    tfidf = TfidfVectorizer(ngram_range=(1, 3), max_features=200, analyzer='char')
    X_train_tfidf = tfidf.fit_transform(train_df['symbol_series'])
    X_val_tfidf = tfidf.transform(val_df['symbol_series'])
    X_test_tfidf = tfidf.transform(test_df['symbol_series'])
    
    y_train = train_df['label'].values
    y_val = val_df['label'].values
    y_test = test_df['label'].values
    
    models_tfidf = {
        'NB': MultinomialNB(alpha=1.0),
        'LogReg': LogisticRegression(C=1.0, max_iter=1000, random_state=42),
        'RF': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    }
    
    results_tfidf = {}
    for name, model in models_tfidf.items():
        model.fit(X_train_tfidf, y_train)
        val_pred = model.predict(X_val_tfidf)
        test_pred = model.predict(X_test_tfidf)
        val_bal = balanced_accuracy_score(y_val, val_pred)
        test_bal = balanced_accuracy_score(y_test, test_pred)
        results_tfidf[name] = {'val': val_bal, 'test': test_bal, 'pred': test_pred, 'model': model}
        print(f"{name}: Val={val_bal:.4f}, Test={test_bal:.4f}")
    
    # Approach 2: Simple character frequency features
    print("\n=== Approach 2: Character Frequencies ===")
    
    def get_char_freq(series):
        counts = Counter(series)
        total = len(series)
        return {f'freq_{c}': counts.get(c, 0) / total for c in '.*uvwxyz'}
    
    def get_features(df):
        feats = []
        for series in df['symbol_series']:
            f = get_char_freq(series)
            # Add length
            f['length'] = len(series)
            # Field encoding
            field_num = int(df.loc[df['symbol_series'] == series, 'field_id'].iloc[0].replace('fld', ''))
            for i in range(1, 6):
                f[f'field_{i}'] = 1 if field_num == i else 0
            feats.append(f)
        return pd.DataFrame(feats)
    
    # Better feature extraction
    train_feats = []
    val_feats = []
    test_feats = []
    
    for df, feats_list in [(train_df, train_feats), (val_df, val_feats), (test_df, test_feats)]:
        for idx, row in df.iterrows():
            series = row['symbol_series']
            f = get_char_freq(series)
            f['length'] = len(series)
            field_num = int(row['field_id'].replace('fld', ''))
            for i in range(1, 6):
                f[f'field_{i}'] = 1 if field_num == i else 0
            feats_list.append(f)
    
    train_feat_df = pd.DataFrame(train_feats)
    val_feat_df = pd.DataFrame(val_feats)
    test_feat_df = pd.DataFrame(test_feats)
    
    feature_cols = list(train_feat_df.columns)
    X_train_feat = train_feat_df[feature_cols].values
    X_val_feat = val_feat_df[feature_cols].values
    X_test_feat = test_feat_df[feature_cols].values
    
    scaler = StandardScaler()
    X_train_feat_scaled = scaler.fit_transform(X_train_feat)
    X_val_feat_scaled = scaler.transform(X_val_feat)
    X_test_feat_scaled = scaler.transform(X_test_feat)
    
    models_feat = {
        'LogReg': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
        'RF': RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    }
    
    results_feat = {}
    for name, model in models_feat.items():
        model.fit(X_train_feat_scaled, y_train)
        val_pred = model.predict(X_val_feat_scaled)
        test_pred = model.predict(X_test_feat_scaled)
        val_bal = balanced_accuracy_score(y_val, val_pred)
        test_bal = balanced_accuracy_score(y_test, test_pred)
        results_feat[name] = {'val': val_bal, 'test': test_bal, 'pred': test_pred, 'model': model}
        print(f"{name}: Val={val_bal:.4f}, Test={test_bal:.4f}")
    
    # Approach 3: Combined features
    print("\n=== Approach 3: Combined (TF-IDF + Features) ===")
    
    from scipy.sparse import hstack
    X_train_comb = hstack([X_train_tfidf, X_train_feat_scaled])
    X_val_comb = hstack([X_val_tfidf, X_val_feat_scaled])
    X_test_comb = hstack([X_test_tfidf, X_test_feat_scaled])
    
    models_comb = {
        'LogReg': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
        'RF': RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    }
    
    results_comb = {}
    for name, model in models_comb.items():
        model.fit(X_train_comb, y_train)
        val_pred = model.predict(X_val_comb)
        test_pred = model.predict(X_test_comb)
        val_bal = balanced_accuracy_score(y_val, val_pred)
        test_bal = balanced_accuracy_score(y_test, test_pred)
        results_comb[name] = {'val': val_bal, 'test': test_bal, 'pred': test_pred, 'model': model}
        print(f"{name}: Val={val_bal:.4f}, Test={test_bal:.4f}")
    
    # Find overall best
    all_results = {
        **{f'TFIDF_{k}': v for k, v in results_tfidf.items()},
        **{f'Feat_{k}': v for k, v in results_feat.items()},
        **{f'Comb_{k}': v for k, v in results_comb.items()}
    }
    
    best_name = max(all_results, key=lambda x: all_results[x]['val'])
    print(f"\nBest by validation: {best_name} (Val={all_results[best_name]['val']:.4f}, Test={all_results[best_name]['test']:.4f})")
    
    # Also check best test
    best_test_name = max(all_results, key=lambda x: all_results[x]['test'])
    print(f"Best by test: {best_test_name} (Test={all_results[best_test_name]['test']:.4f})")
    
    # Use best validation model for reporting
    best_result = all_results[best_name]
    best_pred = best_result['pred']
    
    # Feature importance if available
    if hasattr(best_result['model'], 'coef_') and best_result['model'].coef_ is not None:
        coef = best_result['model'].coef_[0]
        # For combined approach, this is more complex
        if 'Comb' in best_name:
            print("Combined model - skipping feature importance")
        else:
            if 'TFIDF' in best_name:
                feature_names = tfidf.get_feature_names_out()
            else:
                feature_names = feature_cols
            
            top_idx = np.argsort(np.abs(coef))[-15:][::-1]
            print("\nTop features by coefficient:")
            for idx in top_idx:
                if idx < len(feature_names):
                    print(f"  {feature_names[idx]}: {coef[idx]:.4f}")
    
    # Plots
    # Confusion matrix
    cm = confusion_matrix(y_test, best_pred)
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
    names = list(all_results.keys())
    x = np.arange(len(names))
    width = 0.35
    val_scores = [all_results[n]['val'] for n in names]
    test_scores = [all_results[n]['test'] for n in names]
    
    plt.bar(x - width/2, val_scores, width, label='Validation', alpha=0.8)
    plt.bar(x + width/2, test_scores, width, label='Test', alpha=0.8)
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
    
    # Character frequency comparison
    print("\nCharacter frequency analysis...")
    train_df['length'] = train_df['symbol_series'].apply(len)
    
    def count_stars(s):
        return s.count('*') / len(s) if len(s) > 0 else 0
    def count_dots(s):
        return s.count('.') / len(s) if len(s) > 0 else 0
    
    train_df['star_ratio'] = train_df['symbol_series'].apply(count_stars)
    train_df['dot_ratio'] = train_df['symbol_series'].apply(count_dots)
    
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 3, 1)
    sns.kdeplot(data=train_df, x='star_ratio', hue='label', fill=True, alpha=0.3)
    plt.title('Star Ratio by Class')
    
    plt.subplot(1, 3, 2)
    sns.kdeplot(data=train_df, x='dot_ratio', hue='label', fill=True, alpha=0.3)
    plt.title('Dot Ratio by Class')
    
    plt.subplot(1, 3, 3)
    sns.kdeplot(data=train_df, x='length', hue='label', fill=True, alpha=0.3)
    plt.title('Length by Class')
    
    plt.tight_layout()
    plt.savefig('report/images/feature_distributions.png', dpi=150)
    plt.close()
    
    print(f"\n{'='*50}")
    print(f"FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Best Model: {best_name}")
    print(f"Test Balanced Accuracy: {best_result['test']:.4f}")
    print(f"Baseline: 0.78")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, best_pred, target_names=['Non-Variable', 'Variable']))
    
    # Save summary
    summary = pd.DataFrame({
        'model': list(all_results.keys()),
        'val_bal': [all_results[n]['val'] for n in all_results],
        'test_bal': [all_results[n]['test'] for n in all_results]
    })
    summary.to_csv('outputs/results_summary.csv', index=False)

if __name__ == '__main__':
    main()
