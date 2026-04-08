#!/usr/bin/env python3
"""
Variable Star Classification - Version 8
Focus on matching baseline with better feature engineering
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
from sklearn.naive_bayes import MultinomialNB, BernoulliNB, GaussianNB
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
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
    print(f"Train class balance: {y_train.mean():.3f}")
    print(f"Val class balance: {y_val.mean():.3f}")
    print(f"Test class balance: {y_test.mean():.3f}")
    
    # Approach 1: Pure TF-IDF with various classifiers
    print("\n=== Approach 1: TF-IDF ===")
    
    tfidf_configs = [
        (1, 2, 50),
        (1, 3, 100),
        (2, 3, 100),
        (2, 4, 150),
        (1, 4, 200),
    ]
    
    best_tfidf_result = None
    best_tfidf_score = 0
    
    for ngram_min, ngram_max, max_feat in tfidf_configs:
        tfidf = TfidfVectorizer(ngram_range=(ngram_min, ngram_max), max_features=max_feat, analyzer='char')
        X_train = tfidf.fit_transform(train_df['symbol_series'])
        X_val = tfidf.transform(val_df['symbol_series'])
        X_test = tfidf.transform(test_df['symbol_series'])
        
        # Try different classifiers
        classifiers = {
            'NB': MultinomialNB(alpha=0.5),
            'LR': LogisticRegression(C=1.0, max_iter=1000),
            'RF': RandomForestClassifier(n_estimators=100, max_depth=5),
        }
        
        for clf_name, clf in classifiers.items():
            clf.fit(X_train, y_train)
            val_pred = clf.predict(X_val)
            test_pred = clf.predict(X_test)
            val_score = balanced_accuracy_score(y_val, val_pred)
            test_score = balanced_accuracy_score(y_test, test_pred)
            
            name = f'TFIDF({ngram_min},{ngram_max},{max_feat})_{clf_name}'
            print(f"{name}: Val={val_score:.4f}, Test={test_score:.4f}")
            
            if val_score > best_tfidf_score:
                best_tfidf_score = val_score
                best_tfidf_result = {'name': name, 'val': val_score, 'test': test_score, 'pred': test_pred}
    
    # Approach 2: Character frequency features
    print("\n=== Approach 2: Character Frequencies ===")
    
    def get_char_features(series):
        n = len(series)
        counts = Counter(series)
        features = {}
        for c in '.*uvwxyz':
            features[f'freq_{c}'] = counts.get(c, 0) / n
        return features
    
    def process_char_features(df):
        feats = []
        for idx, row in df.iterrows():
            f = get_char_features(row['symbol_series'])
            fld = int(row['field_id'].replace('fld', ''))
            for i in range(1, 6):
                f[f'fld_{i}'] = 1 if fld == i else 0
            feats.append(f)
        return pd.DataFrame(feats)
    
    train_char = process_char_features(train_df)
    val_char = process_char_features(val_df)
    test_char = process_char_features(test_df)
    
    char_cols = list(train_char.columns)
    X_train_char = train_char[char_cols].values
    X_val_char = val_char[char_cols].values
    X_test_char = test_char[char_cols].values
    
    scaler = StandardScaler()
    X_train_char_s = scaler.fit_transform(X_train_char)
    X_val_char_s = scaler.transform(X_val_char)
    X_test_char_s = scaler.transform(X_test_char)
    
    char_classifiers = {
        'LR_C0.1': LogisticRegression(C=0.1, max_iter=1000),
        'LR_C1': LogisticRegression(C=1.0, max_iter=1000),
        'RF_d2': RandomForestClassifier(n_estimators=200, max_depth=2),
        'RF_d3': RandomForestClassifier(n_estimators=200, max_depth=3),
        'SVM_rbf': SVC(kernel='rbf', C=1.0),
        'KNN_10': KNeighborsClassifier(n_neighbors=10),
        'KNN_20': KNeighborsClassifier(n_neighbors=20),
        'LDA': LinearDiscriminantAnalysis(),
        'QDA': QuadraticDiscriminantAnalysis(),
    }
    
    best_char_result = None
    best_char_score = 0
    
    for name, clf in char_classifiers.items():
        try:
            clf.fit(X_train_char_s, y_train)
            val_pred = clf.predict(X_val_char_s)
            test_pred = clf.predict(X_test_char_s)
            val_score = balanced_accuracy_score(y_val, val_pred)
            test_score = balanced_accuracy_score(y_test, test_pred)
            
            full_name = f'Char_{name}'
            print(f"{full_name}: Val={val_score:.4f}, Test={test_score:.4f}")
            
            if val_score > best_char_score:
                best_char_score = val_score
                best_char_result = {'name': full_name, 'val': val_score, 'test': test_score, 'pred': test_pred}
        except Exception as e:
            print(f"{name}: Error - {e}")
    
    # Approach 3: Combined TF-IDF + Character features
    print("\n=== Approach 3: Combined ===")
    
    tfidf_comb = TfidfVectorizer(ngram_range=(1, 3), max_features=100, analyzer='char')
    X_train_tfidf = tfidf_comb.fit_transform(train_df['symbol_series']).toarray()
    X_val_tfidf = tfidf_comb.transform(val_df['symbol_series']).toarray()
    X_test_tfidf = tfidf_comb.transform(test_df['symbol_series']).toarray()
    
    X_train_comb = np.hstack([X_train_char_s, X_train_tfidf])
    X_val_comb = np.hstack([X_val_char_s, X_val_tfidf])
    X_test_comb = np.hstack([X_test_char_s, X_test_tfidf])
    
    comb_classifiers = {
        'LR_C0.1': LogisticRegression(C=0.1, max_iter=1000),
        'RF_d2': RandomForestClassifier(n_estimators=200, max_depth=2),
        'RF_d3': RandomForestClassifier(n_estimators=200, max_depth=3),
    }
    
    best_comb_result = None
    best_comb_score = 0
    
    for name, clf in comb_classifiers.items():
        clf.fit(X_train_comb, y_train)
        val_pred = clf.predict(X_val_comb)
        test_pred = clf.predict(X_test_comb)
        val_score = balanced_accuracy_score(y_val, val_pred)
        test_score = balanced_accuracy_score(y_test, test_pred)
        
        full_name = f'Comb_{name}'
        print(f"{full_name}: Val={val_score:.4f}, Test={test_score:.4f}")
        
        if val_score > best_comb_score:
            best_comb_score = val_score
            best_comb_result = {'name': full_name, 'val': val_score, 'test': test_score, 'pred': test_pred}
    
    # Find overall best
    all_results = [
        best_tfidf_result,
        best_char_result,
        best_comb_result
    ]
    all_results = [r for r in all_results if r is not None]
    
    best_overall = max(all_results, key=lambda x: x['val'])
    print(f"\n=== Best Overall (by val) ===")
    print(f"Model: {best_overall['name']}")
    print(f"Val: {best_overall['val']:.4f}")
    print(f"Test: {best_overall['test']:.4f}")
    
    # Also check best test
    best_test = max(all_results, key=lambda x: x['test'])
    print(f"\n=== Best by Test ===")
    print(f"Model: {best_test['name']}")
    print(f"Test: {best_test['test']:.4f}")
    
    # Use best validation for final
    final_result = best_overall
    
    # Plots
    # Confusion matrix
    cm = confusion_matrix(y_test, final_result['pred'])
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Non-Variable (0)', 'Variable (1)'],
                yticklabels=['Non-Variable (0)', 'Variable (1)'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(f'Confusion Matrix ({final_result["name"]})')
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
    
    # Feature importance for character-based models
    if 'Char' in final_result['name'] or 'Comb' in final_result['name']:
        # Get the model and extract importance if possible
        pass
    
    # Model comparison bar chart
    plt.figure(figsize=(10, 6))
    models_to_show = [
        ('TF-IDF Best', best_tfidf_result['val'], best_tfidf_result['test']),
        ('Char Best', best_char_result['val'], best_char_result['test']),
        ('Comb Best', best_comb_result['val'], best_comb_result['test']),
    ]
    names = [m[0] for m in models_to_show]
    x = np.arange(len(names))
    width = 0.35
    plt.bar(x - width/2, [m[1] for m in models_to_show], width, label='Val', alpha=0.8)
    plt.bar(x + width/2, [m[2] for m in models_to_show], width, label='Test', alpha=0.8)
    plt.axhline(y=0.78, color='r', linestyle='--', label='Baseline (0.78)')
    plt.xlabel('Approach')
    plt.ylabel('Balanced Accuracy')
    plt.title('Approach Comparison')
    plt.xticks(x, names)
    plt.legend()
    plt.ylim(0.4, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    
    # Character frequency comparison
    plt.figure(figsize=(12, 4))
    train_char['label'] = y_train
    for i, c in enumerate('.*uvwxyz'):
        plt.subplot(2, 4, i+1)
        sns.kdeplot(data=train_char, x=f'freq_{c}', hue='label', fill=True, alpha=0.3)
        plt.title(f'freq_{c}')
    plt.tight_layout()
    plt.savefig('report/images/feature_distributions.png', dpi=150)
    plt.close()
    
    print(f"\n{'='*50}")
    print(f"FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Best Model: {final_result['name']}")
    print(f"Test Balanced Accuracy: {final_result['test']:.4f}")
    print(f"Baseline: 0.78")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, final_result['pred'], target_names=['Non-Variable', 'Variable']))
    
    # Save summary
    summary = pd.DataFrame({
        'approach': ['TF-IDF', 'Char', 'Comb'],
        'val': [best_tfidf_result['val'], best_char_result['val'], best_comb_result['val']],
        'test': [best_tfidf_result['test'], best_char_result['test'], best_comb_result['test']]
    })
    summary.to_csv('outputs/results_summary.csv', index=False)

if __name__ == '__main__':
    main()
