import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, StratifiedKFold
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
print("Loading data...")
train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

print(f"Train size: {len(train)}, Val size: {len(val)}, Test size: {len(test)}")

# Define the character set
CHARS = ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}

# Check distribution differences between train and test
print("\n" + "="*60)
print("Distribution Analysis")
print("="*60)

print("\nLabel distribution:")
print(f"Train: {train['label'].value_counts().to_dict()}")
print(f"Val: {val['label'].value_counts().to_dict()}")
print(f"Test: {test['label'].value_counts().to_dict()}")

print("\nField distribution:")
print(f"Train: {train['field_id'].value_counts().sort_index().to_dict()}")
print(f"Val: {val['field_id'].value_counts().sort_index().to_dict()}")
print(f"Test: {test['field_id'].value_counts().sort_index().to_dict()}")

# Check character frequency distribution
print("\nCharacter frequency distribution:")
for dataset_name, dataset in [('Train', train), ('Val', val), ('Test', test)]:
    all_chars = ''.join(dataset['symbol_series'].tolist())
    counts = Counter(all_chars)
    total = len(all_chars)
    print(f"\n{dataset_name}:")
    for c in sorted(CHARS):
        print(f"  {c}: {counts.get(c, 0)/total*100:.2f}%")

# Try cross-validation on train+val
print("\n" + "="*60)
print("Cross-Validation Analysis")
print("="*60)

# Combine train and val
train_val = pd.concat([train, val], ignore_index=True)
print(f"Combined train+val size: {len(train_val)}")

def extract_freq_features(symbol_series):
    """Extract frequency-based features"""
    features = []
    for s in symbol_series:
        feat = []
        char_counts = Counter(s)
        
        # Overall frequencies
        for c in CHARS:
            feat.append(char_counts.get(c, 0) / len(s))
        
        # Quarter-based frequencies
        for q in range(4):
            start = q * 10
            end = (q + 1) * 10
            quarter = s[start:end]
            q_counts = Counter(quarter)
            for c in CHARS:
                feat.append(q_counts.get(c, 0) / 10)
        
        # Half-based frequencies
        first_half = s[:20]
        second_half = s[20:]
        for half in [first_half, second_half]:
            h_counts = Counter(half)
            for c in CHARS:
                feat.append(h_counts.get(c, 0) / 20)
        
        # Frequency differences between halves
        first_counts = Counter(first_half)
        second_counts = Counter(second_half)
        for c in CHARS:
            diff = (second_counts.get(c, 0) - first_counts.get(c, 0)) / 20
            feat.append(diff)
        
        features.append(feat)
    return np.array(features)

X_train_val = extract_freq_features(train_val['symbol_series'])
y_train_val = train_val['label'].values

X_test = extract_freq_features(test['symbol_series'])
y_test = test['label'].values

print(f"Features shape: {X_train_val.shape}")

# Cross-validation
rf = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(rf, X_train_val, y_train_val, cv=cv, scoring='balanced_accuracy')
print(f"\nCross-validation scores: {cv_scores}")
print(f"Mean CV score: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")

# Train on full train+val and evaluate on test
rf.fit(X_train_val, y_train_val)
y_test_pred = rf.predict(X_test)
test_bal_acc = balanced_accuracy_score(y_test, y_test_pred)

print(f"\nTest Balanced Accuracy: {test_bal_acc:.4f}")
print(f"Baseline: 0.78")

print("\nClassification Report:")
print(classification_report(y_test, y_test_pred, target_names=['Non-variable', 'Variable']))

# Try different random states to see if results are stable
print("\n" + "="*60)
print("Stability Analysis")
print("="*60)

test_scores = []
for rs in range(10):
    rf = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=rs, n_jobs=-1)
    rf.fit(X_train_val, y_train_val)
    y_pred = rf.predict(X_test)
    score = balanced_accuracy_score(y_test, y_pred)
    test_scores.append(score)
    print(f"Random state {rs}: {score:.4f}")

print(f"\nMean test score: {np.mean(test_scores):.4f} (+/- {np.std(test_scores):.4f})")

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'predicted_label': y_test_pred
})
predictions_df.to_csv('outputs/predictions.csv', index=False)

print("\nAnalysis complete!")
