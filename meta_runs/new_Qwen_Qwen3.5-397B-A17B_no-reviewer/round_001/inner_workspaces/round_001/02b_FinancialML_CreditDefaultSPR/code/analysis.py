#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def extract_features(sym_seq):
    features = {}
    seq = str(sym_seq)
    features['length'] = len(seq)
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        features['count_' + char] = seq.count(char)
    total = len(seq)
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        features['prop_' + char] = seq.count(char) / total if total > 0 else 0
    letters = sum(seq.count(c) for c in ['A', 'B', 'C', 'D'])
    numbers = sum(seq.count(c) for c in ['1', '2'])
    features['prop_letters'] = letters / total if total > 0 else 0
    features['prop_numbers'] = numbers / total if total > 0 else 0
    features['letters_numbers_ratio'] = letters / numbers if numbers > 0 else 0
    char_to_num = {'A': 0, 'B': 1, 'C': 2, 'D': 3, '1': 4, '2': 5}
    features['first_char'] = char_to_num.get(seq[0], -1) if len(seq) > 0 else -1
    features['last_char'] = char_to_num.get(seq[-1], -1) if len(seq) > 0 else -1
    bigrams = [seq[i:i+2] for i in range(len(seq)-1)]
    for bg in ['AA', 'AB', 'AC', 'AD', 'BA', 'BB', 'BC', 'BD', 'CA', 'CB', 'CC', 'CD', 'DA', 'DB', 'DC', 'DD', '11', '12', '21', '22', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2', '1A', '1B', '1C', '1D', '2A', '2B', '2C', '2D']:
        features['bigram_' + bg] = bigrams.count(bg) / len(bigrams) if len(bigrams) > 0 else 0
    transitions = 0
    for i in range(len(seq) - 1):
        c1, c2 = seq[i], seq[i+1]
        if (c1 in 'ABCD') != (c2 in 'ABCD'):
            transitions += 1
    features['transition_rate'] = transitions / (len(seq) - 1) if len(seq) > 1 else 0
    features['unique_chars'] = len(set(seq))
    char_counts = {c: seq.count(c) for c in set(seq)}
    entropy = 0
    for count in char_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * np.log2(p)
    features['entropy'] = entropy    for char in ['A', 'B', 'C', 'D', '1', '2']:
        positions = [i for i, c in enumerate(seq) if c == char]
        features['avg_pos_' + char] = np.mean(positions) / total if positions and total > 0 else 0
    runs = 1
    for i in range(len(seq) - 1):
        if seq[i] != seq[i+1]:
            runs += 1
    features['run_count'] = runs
    features['avg_run_length'] = len(seq) / runs if runs > 0 else 0
    return features

def main():
    print('Loading data...')
    train_df = pd.read_csv('data/train.csv')
    val_df = pd.read_csv('data/val.csv')
    test_df = pd.read_csv('data/test.csv')
    print('Train:', len(train_df), 'Val:', len(val_df), 'Test:', len(test_df))
    print('Extracting features...')
    train_features = train_df['sym_seq'].apply(extract_features).apply(pd.Series)
    val_features = val_df['sym_seq'].apply(extract_features).apply(pd.Series)
    test_features = test_df['sym_seq'].apply(extract_features).apply(pd.Series)
    train_features['default_flag'] = train_df['default_flag']
    val_features['default_flag'] = val_df['default_flag']
    test_features['default_flag'] = test_df['default_flag']
    feature_cols = [c for c in train_features.columns if c != 'default_flag']
    X_train = np.nan_to_num(train_features[feature_cols].values, nan=0.0)
    y_train = train_features['default_flag'].values
    X_val = np.nan_to_num(val_features[feature_cols].values, nan=0.0)
    y_val = val_features['default_flag'].values
    X_test = np.nan_to_num(test_features[feature_cols].values, nan=0.0)
    y_test = test_features['default_flag'].values
    results = {}
    print('Training RF...')
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_val_pred = rf.predict_proba(X_val)[:, 1]
    rf_test_pred = rf.predict_proba(X_test)[:, 1]
    results['RF_val'] = roc_auc_score(y_val, rf_val_pred)
    results['RF_test'] = roc_auc_score(y_test, rf_test_pred)
    print('RF Val AUC:', round(results['RF_val'], 4), 'Test AUC:', round(results['RF_test'], 4))
    print('Training GB...')
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    gb.fit(X_train, y_train)
    gb_val_pred = gb.predict_proba(X_val)[:, 1]
    gb_test_pred = gb.predict_proba(X_test)[:, 1]
    results['GB_val'] = roc_auc_score(y_val, gb_val_pred)
    results['GB_test'] = roc_auc_score(y_test, gb_test_pred)
    print('GB Val AUC:', round(results['GB_val'], 4), 'Test AUC:', round(results['GB_test'], 4))
    print('Training LR...')
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    lr_val_pred = lr.predict_proba(X_val)[:, 1]
    lr_test_pred = lr.predict_proba(X_test)[:, 1]
    results['LR_val'] = roc_auc_score(y_val, lr_val_pred)
    results['LR_test'] = roc_auc_score(y_test, lr_test_pred)
    print('LR Val AUC:', round(results['LR_val'], 4), 'Test AUC:', round(results['LR_test'], 4))
    best_model = max([('RF', results['RF_val'], rf_test_pred), ('GB', results['GB_val'], gb_test_pred), ('LR', results['LR_val'], lq_test_pred)], key=lambda x: x[1])
    print('Best model:', best_model[0], 'Val AUC:', round(best_model[1], 4))
    results_df = pd.DataFrame({'Model': ['RF', 'GB', 'LR'], 'Val_AUC': [results['RF_val'], results['GB_val'], results['LR_val']], 'Test_AUC': [results['RF_test'], results['GB_test'], results['LR_test']]})
    results_df.to_csv('outputs/results.csv', index=False)
    # Plots: Model Comparison
    plt.figure(figsize=(10, 6))
    models = ['RF', 'GB', 'LR']
    val_aucs = [results['RF_val'], results['GB_val'], results['LR_val']]
    test_aucs = [results['RF_test'], results['GB_test'], results['LR_test']]
    x = np.arange(len(models))
    width = 0.35
    plt.bar(x - width/2, val_aucs, width, label='Validation AUC', color='steelblue')
    plt.bar(x + width/2, test_aucs, width, label='Test AUC', color='coral')
    plt.axhline(y=0.72, color='green', linestyle='--', label='Baseline (0.72)')
    plt.xlabel('Model')
    plt.ylabel('AUC Score')
    plt.title('Model Performance Comparison')
    plt.xticks(x, models)
    plt.legend()
    plt.ulim(0.5, 1.0)
    plt.tight_layout()
    plt.savefig('report/images/model_comparison.png', dpi=150)
    plt.close()
    # ROC curves
    plt.figure(figsize=(8, 8))
    fpr_rf, tpr_rf, _ = roc_curve(y_test, rf_test_pred)
    fpr_gb, tpr_gb, _ = roc_curve(y_test, gb_test_pred)
    fpr_lr, tpr_lr, _ = roc_curve(y_test, lr_test_pred)
    plt.plot(fpr_rf, tpr_rf, label='RF (AUC=' + str(round(results['RF_test'], 3)) + ')', linewidth=2)
    plt.plot(fpr_gb, tpr_gb, label='GB (AUC=' + str(round(results['GB_test'], 3)) + ')', linewidth=2)
    plt.plot(fpr_lr,,tpr_lr, label='LR (AUC=' + str(round(results['LR_test'], 3)) + ')', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves')
    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig('report/images/roc_curves.png', dpi=150)
    plt.close()
    # Feature importance
    plt.figure(figsize=(12, 10))
    importances = rf.feature_importances
    indices = np.argsort(importances)[[:1][:20]
    feature_names = [feature_cols[i] for i in indices]
    plt.barhhrange(len(indices)), importances[indices][::-1])
    plt.yticks(range(len(indices)), feature_names)
    plt.xlabel('Feature Importance')
    plt.title('Top 20 Feature Importances')
    plt.tight_layout()
    plt.savefig('report/images/feature_importance.png', dpi=150)
    plt.close()
    # Data overview
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 3, 1)
    splits = ['Train', 'Val', 'Test']
    counts = [len(train_df), len(val_df), len(test_df)]
    plt.bar(splits, counts, color=['steelblue', 'coral', 'green'])
    plt.ylabel('Number of Samples')
    plt.title('Dataset Split Sizes')
    plt.subplot(1, 3, 2)
    default_counts = [train_df['default_flag'].sum(), val_df['default_flag'].sum(), test_df['default_flag'].sum()]
    plt.bar(splits, default_counts, color=['steelblue', 'coral', 'green'])
    plt.ylabel('Number of Defaults')
    plt.title('Default Counts')
    plt.subplot(1, 3, 3)
    default_rates = [train_df['default_flag'].mean(), val_df['default_flag'].mean(), test_df['default_flag'].mean()]
    plt.bar(splits, default_rates, color=['steelblue', 'coral', 'green'])
    plt.ylabel('Default Rate')
    plt.title('Default Rate')
    plt.ulim(0, 1)
    plt.tight_layout()
    plt.savefig('report/images/data_overview.png', dpi=150)
    plt.close()
