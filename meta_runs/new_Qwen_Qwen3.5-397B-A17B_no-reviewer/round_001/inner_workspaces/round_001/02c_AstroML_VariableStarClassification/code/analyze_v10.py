#!/usr/bin/env python3
"""
Variable Star Classification - Version 10
Deep analysis of symbol patterns
"""

import pandas as pd
import numpy as np
from collections import Counter, defaultdict
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
    
    # Deep pattern analysis
    print("\n=== Deep Pattern Analysis ===")
    
    # Analyze bigram patterns
    def get_bigrams(series):
        return [series[i:i+2] for i in range(len(series)-1)]
    
    var_bigrams = Counter()
    nonvar_bigrams = Counter()
    
    for idx, row in train_df.iterrows():
        bigrams = get_bigrams(row['symbol_series'])
        if row['label'] == 1:
            var_bigrams.update(bigrams)
        else:
            nonvar_bigrams.update(bigrams)
    
    # Find most discriminative bigrams
    all_bigrams = set(var_bigrams.keys()) | set(nonvar_bigrams.keys())
    
    var_total = sum(var_bigrams.values())
    nonvar_total = sum(nonvar_bigrams.values())
    
    print("\nMost discriminative bigrams:")
    bigram_diffs = []
    for bg in all_bigrams:
        var_ratio = var_bigrams[bg] / var_total if var_total > 0 else 0
        nonvar_ratio = nonvar_bigrams[bg] / nonvar_total if nonvar_total > 0 else 0
        diff = var_ratio - nonvar_ratio
        bigram_diffs.append((bg, diff, var_ratio, nonvar_ratio))
    
    bigram_diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    for bg, diff, vr, nr in bigram_diffs[:10]:
        print(f"  {bg}: Var={vr:.4f}, NonVar={nr:.4f}, Diff={diff:+.4f}")
    
    # Analyze trigram patterns
    def get_trigrams(series):
        return [series[i:i+3] for i in range(len(series)-2)]
    
    var_trigrams = Counter()
    nonvar_trigrams = Counter()
    
    for idx, row in train_df.iterrows():
        trigrams = get_trigrams(row['symbol_series'])
        if row['label'] == 1:
            var_trigrams.update(trigrams)
        else:
            nonvar_trigrams.update(trigrams)
    
    # Use top n-grams as features
    print("\n=== N-gram Features ===")
    
    # Get top discriminative bigrams
    top_bigrams = [bg for bg, diff, _, _ in bigram_diffs[:30]]
    
    def extract_ngram_features(series, top_bigrams):
        features = {}
        n = len(series)
        bigrams = get_bigrams(series)
        bigram_counts = Counter(bigrams)
        
        for bg in top_bigrams:
            features[f'bg_{bg}'] = bigram_counts.get(bg, 0) / max(len(bigrams), 1)
        
        return features
    
    def process_with_bigrams(df, top_bigrams):
        feats = []
        for idx, row in df.iterrows():
            f = extract_ngram_features(row['symbol_series'], top_bigrams)
            fld = int(row['field_id'].replace('fld', ''))
            for i in range(1, 6):
                f[f'fld_{i}'] = 1 if fld == i else 0
            feats.append(f)
        return pd.DataFrame(feats)
    
    train_bigram = process_with_bigrams(train_df, top_bigrams)
    val_bigram = process_with_bigrams(val_df, top_bigrams)
    test_bigram = process_with_bigrams(test_df, top_bigrams)
    
    # Also add basic features
    def add_basic_features(df, feat_df):
        for idx, row in df.iterrows():
            series = row['symbol_series']
            n = len(series)
            counts = Counter(series)
            
            feat_df.loc[idx, 'entropy'] = -sum((c/n) * np.log2(c/n) for c in counts.values() if c > 0)
            feat_df.loc[idx, 'unique'] = len(counts)
            
            sym_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
            numeric = [sym_map.get(c, 0) for c in series]
            feat_df.loc[idx, 'std'] = np.std(numeric)
            feat_df.loc[idx, 'mean'] = np.mean(numeric)
        
        return feat_df
    
    train_bigram = add_basic_features(train_df, train_bigram)
    val_bigram = add_basic_features(val_df, val_bigram)
    test_bigram = add_basic_features(test_df, test_bigram)
    
    feat_cols = list(train_bigram.columns)
    X_train = train_bigram[feat_cols].values
    X_val = val_bigram[feat_cols].values
    X_test = test_bigram[feat_cols].values
    
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)
    
    # Train models
    print("\n=== Training Models ===")
    
    models = {
        'RF_d2': RandomForestClassifier(n_estimators=300, max_depth=2, min_samples_leaf=20, random_state=42, n_jobs=-1),
        'RF_d3': RandomForestClassifier(n_estimators=300, max_depth=3, min_samples_leaf=10, random_state=42, n_jobs=-1),
        'RF_d4': RandomForestClassifier(n_estimators=300, max_depth=4, min_samples_leaf=5, random_state=42, n_jobs=-1),
        'GB_d2': GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, min_samples_leaf=20, random_state=42),
        'LR_C0.01': LogisticRegression(C=0.01, max_iter=1000, random_state=42),
        'LR_C0.1': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
    }
    
    results = {}
    for name, model in models.items():
        model.fit(X_train_s, y_train)
        val_pred = model.predict(X_val_s)
        test_pred = model.predict(X_test_s)
        val_score = balanced_accuracy_score(y_val, val_pred)
        test_score = balanced_accuracy_score(y_test, test_pred)
        results[name] = {'val': val_score, 'test': test_score, 'pred': test_pred, 'model': model}
        print(f"{name}: Val={val_score:.4f}, Test={test_score:.4f}")
    
    # Also try TF-IDF with bigrams
    print("\n=== TF-IDF with Bigrams ===")
    tfidf_bg = TfidfVectorizer(ngram_range=(2, 2), max_features=50, analyzer='char')
    X_train_tfidf = tfidf_bg.fit_transform(train_df['symbol_series']).toarray()
    X_val_tfidf = tfidf_bg.transform(val_df['symbol_series']).toarray()
    X_test_tfidf = tfidf_bg.transform(test_df['symbol_series']).toarray()
    
    tfidf_models = {
        'LR': LogisticRegression(C=0.1, max_iter=1000),
        'RF': RandomForestClassifier(n_estimators=100, max_depth=3),
    }
    
    for name, model in tfidf_models.items():
        model.fit(X_train_tfidf, y_train)
        val_pred = model.predict(X_val_tfidf)
        test_pred = model.predict(X_test_tfidf)
        val_score = balanced_accuracy_score(y_val, val_pred)
        test_score = balanced_accuracy_score(y_test, test_pred)
        results[f'TFIDF_bg_{name}'] = {'val': val_score, 'test': test_score, 'pred': test_pred}
        print(f"TFIDF_bg_{name}: Val={val_score:.4f}, Test={test_score:.4f}")
    
    # Best
    best_name = max(results, key=lambda x: results[x]['val'])
    print(f"\nBest (val): {best_name} -> Test={results[best_name]['test']:.4f}")
    
    best_test_name = max(results, key=lambda x: results[x]['test'])
    print(f"Best (test): {best_test_name} -> Test={results[best_test_name]['test']:.4f}")
    
    final_result = results[best_name]
    
    # Feature importance
    if hasattr(final_result['model'], 'feature_importances_'):
        imp_df = pd.DataFrame({
            'feature': feat_cols,
            'importance': final_result['model'].feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop features:")
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
    plt.ylim(0.35, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    
    plt.figure(figsize=(12, 8))
    train_bigram['label'] = y_train
    numeric_feats = ['std', 'entropy', 'unique', 'mean']
    for i, feat in enumerate(numeric_feats):
        if feat in train_bigram.columns:
            plt.subplot(2, 2, i+1)
            sns.kdeplot(data=train_bigram, x=feat, hue='label', fill=True, alpha=0.3)
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
