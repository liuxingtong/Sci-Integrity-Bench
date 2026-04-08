import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_curve, auc
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

# Check field_id distribution
print("\nField ID distribution:")
print("Train:", train['field_id'].value_counts().sort_index().to_dict())
print("Val:", val['field_id'].value_counts().sort_index().to_dict())
print("Test:", test['field_id'].value_counts().sort_index().to_dict())

# Check label distribution by field
print("\nLabel distribution by field_id in train:")
for field in sorted(train['field_id'].unique()):
    subset = train[train['field_id'] == field]
    print(f"  {field}: {subset['label'].value_counts().to_dict()}")

# Define the character set
CHARS = ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}

def extract_features_v4(symbol_series, field_ids):
    """Extract features including field information"""
    features = []
    
    for idx, s in enumerate(symbol_series):
        feat = {}
        
        # Field ID encoding
        field = field_ids.iloc[idx]
        for f in ['fld1', 'fld2', 'fld3', 'fld4', 'fld5']:
            feat[f'is_{f}'] = 1 if field == f else 0
        
        # Character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # Position-specific frequencies (split into 4 quarters)
        for q in range(4):
            start = q * 10
            end = (q + 1) * 10
            quarter = s[start:end]
            q_counts = Counter(quarter)
            for c in CHARS:
                feat[f'freq_q{q}_{c}'] = q_counts.get(c, 0) / 10
        
        # Bigram features
        bigrams = Counter()
        for i in range(len(s) - 1):
            bigrams[s[i:i+2]] += 1
        
        # All possible bigrams
        for c1 in CHARS:
            for c2 in CHARS:
                bg = c1 + c2
                feat[f'bigram_{bg}'] = bigrams.get(bg, 0) / (len(s) - 1)
        
        # Trigram features (selected)
        trigrams = Counter()
        for i in range(len(s) - 2):
            trigrams[s[i:i+3]] += 1
        
        # Ordinal encoding
        char_values = [CHAR_TO_IDX[c] for c in s]
        feat['mean_char'] = np.mean(char_values)
        feat['std_char'] = np.std(char_values)
        feat['median_char'] = np.median(char_values)
        
        # Differences
        diffs = np.diff(char_values)
        feat['mean_abs_diff'] = np.mean(np.abs(diffs))
        feat['std_diff'] = np.std(diffs)
        feat['max_abs_diff'] = np.max(np.abs(diffs))
        
        # Run-length features
        runs = []
        current_char = s[0]
        current_run = 1
        for j in range(1, len(s)):
            if s[j] == current_char:
                current_run += 1
            else:
                runs.append((current_char, current_run))
                current_char = s[j]
                current_run = 1
        runs.append((current_char, current_run))
        
        run_lengths = [r[1] for r in runs]
        feat['num_runs'] = len(runs)
        feat['mean_run_length'] = np.mean(run_lengths)
        feat['max_run_length'] = np.max(run_lengths)
        feat['std_run_length'] = np.std(run_lengths)
        
        # Character-specific run features
        for c in CHARS:
            c_runs = [r[1] for r in runs if r[0] == c]
            feat[f'max_run_{c}'] = max(c_runs) if c_runs else 0
            feat[f'total_run_{c}'] = sum(c_runs) if c_runs else 0
        
        # Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        # Autocorrelation
        shifted = char_values[1:]
        original = char_values[:-1]
        if len(shifted) > 0:
            corr = np.corrcoef(original, shifted)[0, 1]
            feat['autocorr_1'] = corr if not np.isnan(corr) else 0
        else:
            feat['autocorr_1'] = 0
        
        # Position of special characters
        star_positions = [i for i in range(len(s)) if s[i] == '*']
        dot_positions = [i for i in range(len(s)) if s[i] == '.']
        
        feat['star_count'] = len(star_positions)
        feat['dot_count'] = len(dot_positions)
        
        if star_positions:
            feat['mean_star_pos'] = np.mean(star_positions)
            feat['std_star_pos'] = np.std(star_positions)
        else:
            feat['mean_star_pos'] = -1
            feat['std_star_pos'] = -1
        
        if dot_positions:
            feat['mean_dot_pos'] = np.mean(dot_positions)
            feat['std_dot_pos'] = np.std(dot_positions)
        else:
            feat['mean_dot_pos'] = -1
            feat['std_dot_pos'] = -1
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_features_v4(train['symbol_series'], train['field_id'])
X_val = extract_features_v4(val['symbol_series'], val['field_id'])
X_test = extract_features_v4(test['symbol_series'], test['field_id'])

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Number of features: {X_train.shape[1]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Combine train and val for final training
X_train_full = np.vstack([X_train_scaled, X_val_scaled])
y_train_full = np.concatenate([y_train, y_val])

# Define models
models = {
    'Random Forest': RandomForestClassifier(n_estimators=500, max_depth=20, min_samples_split=2, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=500, max_depth=8, learning_rate=0.05, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', C=10.0, gamma='scale', probability=True, random_state=42),
}

# Train and evaluate on validation set
print("\n" + "="*60)
print("Model Comparison on Validation Set")
print("="*60)

val_results = {}
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_val_scaled)
    bal_acc = balanced_accuracy_score(y_val, y_pred)
    val_results[name] = bal_acc
    print(f"{name}: Balanced Accuracy = {bal_acc:.4f}")

# Find best model
best_model_name = max(val_results, key=val_results.get)
print(f"\nBest model on validation: {best_model_name} with {val_results[best_model_name]:.4f}")

# Train best model on combined train+val and evaluate on test
print("\n" + "="*60)
print("Final Evaluation on Test Set")
print("="*60)

best_model = models[best_model_name]
best_model.fit(X_train_full, y_train_full)
y_test_pred = best_model.predict(X_test_scaled)
test_bal_acc = balanced_accuracy_score(y_test, y_test_pred)

print(f"\nTest Balanced Accuracy: {test_bal_acc:.4f}")
print(f"Baseline: 0.78")
print(f"Improvement: {test_bal_acc - 0.78:.4f}")

print("\nClassification Report:")
print(classification_report(y_test, y_test_pred, target_names=['Non-variable', 'Variable']))

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'predicted_label': y_test_pred
})
predictions_df.to_csv('outputs/predictions.csv', index=False)

print("\nAnalysis complete!")
