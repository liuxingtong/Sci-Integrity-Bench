#!/usr/bin/env python3
"""
Variable Star Classification - Final Attempt
Comprehensive search for best model
"""

import pandas as pd
import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import MultinomialNB, GaussianNB
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score
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
    
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    # Feature extraction
    print("\n=== Feature Extraction ===")
    
    def extract_features(series):
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
        features['median'] = np.median(numeric)
        features['p25'] = np.percentile(numeric, 25)
        features['p75'] = np.percentile(numeric, 75)
        features['iqr'] = features['p75'] - features['p25']
        
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
        
        # Unique
        features['unique'] = len(counts)
        
        # Dominant
        if counts:
            dom = counts.most_common(1)[0]
            features['dom_ratio'] = dom[1] / n
        else:
            features['dom_ratio'] = 0
        
        # Transitions
        diffs = np.diff(numeric)
        features['mean_abs_diff'] = np.mean(np.abs(diffs)) if len(diffs) > 0 else 0
        features['std_diff'] = np.std(diffs) if len(diffs) > 0 else 0
        features['total_var'] = np.sum(np.abs(diffs)) if len(diffs) > 0 else 0
        features['var_rate'] = features['total_var'] / (n - 1) if n > 1 else 0
        
        # Direction changes
        if len(diffs) > 1:
            sign_changes = sum(1 for i in range(1, len(diffs)) if diffs[i] * diffs[i-1] < 0)
            features['dir_change'] = sign_changes / len(diffs)
        else:
            features['dir_change'] = 0
        
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
        features['std_run'] = np.std(runs)
        features['max_run'] = max(runs)
        features['num_runs'] = len(runs)
        features['run_rate'] = len(runs) / n
        
        # High/low/mid
        high = sum(counts.get(c, 0) for c in 'xyz')
        mid = sum(counts.get(c, 0) for c in 'w')
        low = sum(counts.get(c, 0) for c in '.*uv')
        features['high_ratio'] = high / n
        features['mid_ratio'] = mid / n
        features['low_ratio'] = low / n
        features['high_low'] = high / (low + 1)
        features['high_mid_low'] = (high + 1) / (low + 1)
        
        # Specific
        features['n_stars'] = counts.get('*', 0)
        features['n_dots'] = counts.get('.', 0)
        features['cv'] = features['std'] / (features['mean'] + 1e-6)
        
        return features
    
    def process(df):
        feats = []
        for idx, row in df.iterrows():
            f = extract_features(row['symbol_series'])
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
    
    # TF-IDF features
    print("\n=== TF-IDF Features ===")
    tfidf = TfidfVectorizer(ngram_range=(1, 3), max_features=100, analyzer='char')
    X_train_tfidf = tfidf.fit_transform(train_df['symbol_series']).toarray()
    X_val_tfidf = tfidf.transform(val_df['symbol_series']).toarray()
    X_test_tfidf = tfidf.transform(test_df['symbol_series']).toarray()
    
    # Combined
    X_train_comb = np.hstack([X_train_s, X_train_tfidf])
    X_val_comb = np.hstack([X_val_s, X_val_tfidf])
    X_test_comb = np.hstack([X_test_s, X_test_tfidf])
    
    # Train many models
    print("\n=== Training Models ===")
    
    all_results = {}
    
    # Feature-based models
    feature_models = {
        'RF_d2': RandomForestClassifier(n_estimators=500, max_depth=2, min_samples_leaf=15, random_state=42, n_jobs=-1),
        'RF_d3': RandomForestClassifier(n_estimators=500, max_depth=3, min_samples_leaf=10, random_state=42, n_jobs=-1),
        'RF_d4': RandomForestClassifier(n_estimators=500, max_depth=4, min_samples_leaf=5, random_state=42, n_jobs=-1),
        'ET_d2': ExtraTreesClassifier(n_estimators=500, max_depth=2, min_samples_leaf=15, random_state=42, n_jobs=-1),
        'ET_d3': ExtraTreesClassifier(n_estimators=500, max_depth=3, min_samples_leaf=10, random_state=42, n_jobs=-1),
        'GB_d2': GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, min_samples_leaf=15, random_state=42),
        'GB_d3': GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, min_samples_leaf=10, random_state=42),
        'LR_C0.01': LogisticRegression(C=0.01, max_iter=1000, random_state=42),
        'LR_C0.1': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
        'LR_C1': LogisticRegression(C=1.0, max_iter=1000, random_state=42),
        'KNN_10': KNeighborsClassifier(n_neighbors=10),
        'KNN_20': KNeighborsClassifier(n_neighbors=20),
        'LDA': LinearDiscriminantAnalysis(),
        'Ridge': RidgeClassifier(alpha=1.0),
    }
    
    for name, model in feature_models.items():
        model.fit(X_train_s, y_train)
        val_pred = model.predict(X_val_s)
        test_pred = model.predict(X_test_s)
        val_score = balanced_accuracy_score(y_val, val_pred)
        test_score = balanced_accuracy_score(y_test, test_pred)
        all_results[f'Feat_{name}'] = {'val': val_score, 'test': test_score, 'pred': test_pred, 'model': model}
        print(f"Feat_{name}: Val={val_score:.4f}, Test={test_score:.4f}")
    
    # TF-IDF models
    tfidf_models = {
        'NB': MultinomialNB(alpha=0.5),
        'LR': LogisticRegression(C=1.0, max_iter=1000),
        'RF': RandomForestClassifier(n_estimators=200, max_depth=5),
    }
    
    for name, model in tfidf_models.items():
        model.fit(X_train_tfidf, y_train)
        val_pred = model.predict(X_val_tfidf)
        test_pred = model.predict(X_test_tfidf)
        val_score = balanced_accuracy_score(y_val, val_pred)
        test_score = balanced_accuracy_score(y_test, test_pred)
        all_results[f'TFIDF_{name}'] = {'val': val_score, 'test': test_score, 'pred': test_pred}
        print(f"TFIDF_{name}: Val={val_score:.4f}, Test={test_score:.4f}")
    
    # Combined models
    comb_models = {
        'RF_d2': RandomForestClassifier(n_estimators=300, max_depth=2, min_samples_leaf=15, random_state=42, n_jobs=-1),
        'RF_d3': RandomForestClassifier(n_estimators=300, max_depth=3, min_samples_leaf=10, random_state=42, n_jobs=-1),
        'LR_C0.1': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
    }
    
    for name, model in comb_models.items():
        model.fit(X_train_comb, y_train)
        val_pred = model.predict(X_val_comb)
        test_pred = model.predict(X_test_comb)
        val_score = balanced_accuracy_score(y_val, val_pred)
        test_score = balanced_accuracy_score(y_test, test_pred)
        all_results[f'Comb_{name}'] = {'val': val_score, 'test': test_score, 'pred': test_pred}
        print(f"Comb_{name}: Val={val_score:.4f}, Test={test_score:.4f}")
    
    # Find best
    best_name = max(all_results, key=lambda x: all_results[x]['val'])
    print(f"\n=== Best (by val) ===")
    print(f"Model: {best_name}")
    print(f"Val: {all_results[best_name]['val']:.4f}")
    print(f"Test: {all_results[best_name]['test']:.4f}")
    
    best_test_name = max(all_results, key=lambda x: all_results[x]['test'])
    print(f"\n=== Best (by test) ===")
    print(f"Model: {best_test_name}")
    print(f"Test: {all_results[best_test_name]['test']:.4f}")
    
    final_result = all_results[best_name]
    
    # Feature importance
    if hasattr(final_result['model'], 'feature_importances_'):
        imp_df = pd.DataFrame({
            'feature': feat_cols,
            'importance': final_result['model'].feature_importances_
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
    
    # Model comparison
    plt.figure(figsize=(14, 8))
    names = list(all_results.keys())
    x = np.arange(len(names))
    width = 0.35
    plt.bar(x - width/2, [all_results[n]['val'] for n in names], width, label='Val', alpha=0.8)
    plt.bar(x + width/2, [all_results[n]['test'] for n in names], width, label='Test', alpha=0.8)
    plt.axhline(y=0.78, color='r', linestyle='--', label='Baseline (0.78)')
    plt.xlabel('Model')
    plt.ylabel('Balanced Accuracy')
    plt.title('Model Comparison')
    plt.xticks(x, names, rotation=90, ha='right')
    plt.legend()
    plt.ylim(0.35, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    
    # Feature distributions
    plt.figure(figsize=(12, 8))
    train_feat['label'] = y_train
    numeric_feats = ['std', 'entropy', 'mean_abs_diff', 'dir_change', 'high_ratio', 'low_ratio']
    for i, feat in enumerate(numeric_feats):
        if feat in train_feat.columns:
            plt.subplot(2, 3, i+1)
            sns.kdeplot(data=train_feat, x=feat, hue='label', fill=True, alpha=0.3)
            plt.title(feat)
    plt.tight_layout()
    plt.savefig('report/images/feature_distributions.png', dpi=150)
    plt.close()
    
    print(f"\n{'='*50}")
    print(f"FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Best Model: {best_name}")
    print(f"Test Balanced Accuracy: {final_result['test']:.4f}")
    print(f"Baseline: 0.78")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, final_result['pred'], target_names=['Non-Variable', 'Variable']))
    
    # Save summary
    summary = pd.DataFrame({
        'model': list(all_results.keys()),
        'val': [all_results[n]['val'] for n in all_results],
        'test': [all_results[n]['test'] for n in all_results]
    })
    summary.to_csv('outputs/results_summary.csv', index=False)

if __name__ == '__main__':
    main()
