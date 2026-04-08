import pandas as pd
import numpy as np
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# Load data
print("Loading data...")
train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Deep analysis of what distinguishes default from non-default
print("\n" + "="*50)
print("Deep Pattern Analysis")
print("="*50)

# Analyze by position
def analyze_positions(df, name):
    default = df[df['default_flag'] == 1]
    non_default = df[df['default_flag'] == 0]
    
    print(f"\n{name} - Position Analysis:")
    chars = ['A', 'B', 'C', 'D', '1', '2']
    
    significant_patterns = []
    for pos in range(20):
        for c in chars:
            def_freq = (default['sym_seq'].apply(lambda x: x[pos] == c).mean())
            nondef_freq = (non_default['sym_seq'].apply(lambda x: x[pos] == c).mean())
            diff = def_freq - nondef_freq
            if abs(diff) > 0.08:
                significant_patterns.append((pos, c, diff, def_freq, nondef_freq))
    
    for pos, c, diff, def_freq, nondef_freq in sorted(significant_patterns, key=lambda x: abs(x[2]), reverse=True)[:10]:
        print(f"  Position {pos}, char '{c}': default={def_freq:.3f}, non-default={nondef_freq:.3f}, diff={diff:+.3f}")
    
    return significant_patterns

train_patterns = analyze_positions(train_df, "Training Data")

# Feature engineering based on analysis
def extract_targeted_features(seq):
    features = {}
    n = len(seq)
    chars = ['A', 'B', 'C', 'D', '1', '2']
    
    # Position-specific features (most important from analysis)
    for i in range(n):
        for c in chars:
            features[f'p{i}_{c}'] = 1 if seq[i] == c else 0
    
    # Character frequencies
    for c in chars:
        features[f'freq_{c}'] = seq.count(c) / n
    
    # Segment frequencies
    for seg in range(4):
        segment = seq[seg*5:(seg+1)*5]
        for c in chars:
            features[f'seg{seg}_{c}'] = segment.count(c) / 5
    
    # Key bigrams
    bigrams = ['AA', 'BB', 'CC', 'DD', '11', '22', 'AB', 'BA', 'CD', 'DC', '12', '21',
               'AC', 'CA', 'BD', 'DB', 'AD', 'DA', 'BC', 'CB',
               '1A', '1B', '1C', '1D', '2A', '2B', '2C', '2D',
               'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2']
    for bg in bigrams:
        features[f'bigram_{bg}'] = seq.count(bg) / (n - 1)
    
    # Transitions
    trans = sum(1 for i in range(n-1) if seq[i] != seq[i+1])
    features['transitions'] = trans / (n - 1)
    
    # Entropy
    counts = Counter(seq)
    probs = [v/n for v in counts.values()]
    features['entropy'] = -sum(p*np.log2(p) for p in probs)
    
    # Letter ratio
    features['letter_ratio'] = sum(1 for c in seq if c in 'ABCD') / n
    
    # First and last chars
    for c in chars:
        features[f'first_{c}'] = 1 if seq[0] == c else 0
        features[f'last_{c}'] = 1 if seq[-1] == c else 0
    
    return features

def create_features(df):
    return pd.DataFrame([extract_targeted_features(s) for s in df['sym_seq']]).fillna(0)

print("\nExtracting features...")
X_train = create_features(train_df)
X_val = create_features(val_df)
X_test = create_features(test_df)

# Align columns
all_cols = sorted(set(X_train.columns) | set(X_val.columns) | set(X_test.columns))
X_train = X_train.reindex(columns=all_cols, fill_value=0)
X_val = X_val.reindex(columns=all_cols, fill_value=0)
X_test = X_test.reindex(columns=all_cols, fill_value=0)

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Features: {X_train.shape[1]}")

# Standardize
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s = scaler.transform(X_val)
X_test_s = scaler.transform(X_test)

print("\n" + "="*50)
print("Model Training")
print("="*50)

results = {}

# 1. Logistic Regression with various C
print("\n1. Logistic Regression...")
best_lr = None
best_score = 0
for C in [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0]:
    lr = LogisticRegression(C=C, max_iter=5000, random_state=42)
    lr.fit(X_train_s, y_train)
    val_auc = roc_auc_score(y_val, lr.predict_proba(X_val_s)[:, 1])
    test_auc = roc_auc_score(y_test, lr.predict_proba(X_test_s)[:, 1])
    train_auc = roc_auc_score(y_train, lr.predict_proba(X_train_s)[:, 1])
    print(f"  C={C}: train={train_auc:.4f}, val={val_auc:.4f}, test={test_auc:.4f}")
    if val_auc > best_score:
        best_score = val_auc
        best_lr = {'C': C, 'train_auc': train_auc, 'val_auc': val_auc, 'test_auc': test_auc, 'model': lr}
results['Logistic Regression'] = best_lr

# 2. Gradient Boosting
print("\n2. Gradient Boosting...")
best_gb = None
best_score = 0
for depth in [1, 2, 3]:
    for lr_rate in [0.01, 0.05, 0.1]:
        for n_est in [50, 100, 200]:
            gb = GradientBoostingClassifier(n_estimators=n_est, max_depth=depth,
                                            learning_rate=lr_rate, min_samples_leaf=20,
                                            subsample=0.8, random_state=42)
            gb.fit(X_train, y_train)
            val_auc = roc_auc_score(y_val, gb.predict_proba(X_val)[:, 1])
            test_auc = roc_auc_score(y_test, gb.predict_proba(X_test)[:, 1])
            train_auc = roc_auc_score(y_train, gb.predict_proba(X_train)[:, 1])
            if val_auc > best_score:
                best_score = val_auc
                best_gb = {'depth': depth, 'lr': lr_rate, 'n_est': n_est,
                          'train_auc': train_auc, 'val_auc': val_auc, 'test_auc': test_auc, 'model': gb}
print(f"  Best: depth={best_gb['depth']}, lr={best_gb['lr']}, n_est={best_gb['n_est']}")
print(f"  train={best_gb['train_auc']:.4f}, val={best_gb['val_auc']:.4f}, test={best_gb['test_auc']:.4f}")
results['Gradient Boosting'] = best_gb

# 3. Random Forest
print("\n3. Random Forest...")
best_rf = None
best_score = 0
for depth in [2, 3, 4, 5]:
    for min_leaf in [10, 20, 30]:
        rf = RandomForestClassifier(n_estimators=300, max_depth=depth,
                                    min_samples_leaf=min_leaf, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        val_auc = roc_auc_score(y_val, rf.predict_proba(X_val)[:, 1])
        test_auc = roc_auc_score(y_test, rf.predict_proba(X_test)[:, 1])
        train_auc = roc_auc_score(y_train, rf.predict_proba(X_train)[:, 1])
        if val_auc > best_score:
            best_score = val_auc
            best_rf = {'depth': depth, 'min_leaf': min_leaf,
                      'train_auc': train_auc, 'val_auc': val_auc, 'test_auc': test_auc, 'model': rf}
print(f"  Best: depth={best_rf['depth']}, min_leaf={best_rf['min_leaf']}")
print(f"  train={best_rf['train_auc']:.4f}, val={best_rf['val_auc']:.4f}, test={best_rf['test_auc']:.4f}")
results['Random Forest'] = best_rf

# Best model
best_name = max(results.keys(), key=lambda x: results[x]['val_auc'])
best = results[best_name]

print(f"\n{'='*50}")
print(f"Best Model: {best_name}")
print(f"Val AUC: {best['val_auc']:.4f}")
print(f"Test AUC: {best['test_auc']:.4f}")
print(f"Baseline: 0.72")
print(f"{'='*50}")

# Save results
pd.DataFrame({
    'model': list(results.keys()),
    'train_auc': [results[m]['train_auc'] for m in results],
    'val_auc': [results[m]['val_auc'] for m in results],
    'test_auc': [results[m]['test_auc'] for m in results]
}).to_csv('outputs/model_results.csv', index=False)

# Feature importance
if best_name in ['Random Forest', 'Gradient Boosting']:
    fi = pd.DataFrame({'feature': X_train.columns, 'importance': best['model'].feature_importances_})
    fi = fi.sort_values('importance', ascending=False)
    fi.to_csv('outputs/feature_importance.csv', index=False)
    print("\nTop 20 Features:")
    print(fi.head(20).to_string())

print("\nDone!")
