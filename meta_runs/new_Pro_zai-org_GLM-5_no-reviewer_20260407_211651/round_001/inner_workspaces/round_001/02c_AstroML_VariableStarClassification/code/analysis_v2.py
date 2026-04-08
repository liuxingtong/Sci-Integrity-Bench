import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
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

# Define the character set
CHARS = ['x', 'w', 'z', 'u', '*', 'y', 'v', '.']
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}

# Analyze character distribution by class
print("\n" + "="*60)
print("Character Distribution Analysis by Class")
print("="*60)

for label in [0, 1]:
    subset = train[train['label'] == label]['symbol_series']
    all_chars = ''.join(subset.tolist())
    counts = Counter(all_chars)
    total = len(all_chars)
    label_name = 'Non-variable' if label == 0 else 'Variable'
    print(f"\nLabel {label} ({label_name}):")
    for c in sorted(CHARS):
        print(f"  {c}: {counts.get(c, 0)/total*100:.2f}%")

def extract_features_v2(symbol_series):
    """Extract improved features from symbol series"""
    features = []
    
    for s in symbol_series:
        feat = {}
        
        # Basic character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # N-gram features (bigrams and trigrams)
        bigrams = Counter()
        for i in range(len(s) - 1):
            bigrams[s[i:i+2]] += 1
        
        trigrams = Counter()
        for i in range(len(s) - 2):
            trigrams[s[i:i+3]] += 1
        
        # Most discriminative bigrams (based on analysis)
        important_bigrams = ['**', '.*', '*.', 'ww', 'uu', 'vv', 'xx', 'yy', 'zz',
                            'w*', '*w', 'u*', '*u', 'v*', '*v', 'x*', '*x', 'y*', '*y', 'z*', '*z']
        for bg in important_bigrams:
            feat[f'bigram_{bg}'] = bigrams.get(bg, 0) / (len(s) - 1)
        
        # Position-weighted features
        positions = np.arange(len(s)) / (len(s) - 1)  # 0 to 1
        for c in CHARS:
            char_positions = [positions[i] for i in range(len(s)) if s[i] == c]
            if char_positions:
                feat[f'mean_pos_{c}'] = np.mean(char_positions)
                feat[f'std_pos_{c}'] = np.std(char_positions)
            else:
                feat[f'mean_pos_{c}'] = 0.5
                feat[f'std_pos_{c}'] = 0
        
        # Special character patterns
        star_positions = [i for i in range(len(s)) if s[i] == '*']
        dot_positions = [i for i in range(len(s)) if s[i] == '.']
        
        feat['star_count'] = len(star_positions)
        feat['dot_count'] = len(dot_positions)
        
        if len(star_positions) > 1:
            feat['star_spacing_mean'] = np.mean(np.diff(star_positions))
            feat['star_spacing_std'] = np.std(np.diff(star_positions))
        else:
            feat['star_spacing_mean'] = 0
            feat['star_spacing_std'] = 0
        
        if len(dot_positions) > 1:
            feat['dot_spacing_mean'] = np.mean(np.diff(dot_positions))
            feat['dot_spacing_std'] = np.std(np.diff(dot_positions))
        else:
            feat['dot_spacing_mean'] = 0
            feat['dot_spacing_std'] = 0
        
        # Run-length encoding features
        runs = []
        current_char = s[0]
        current_run = 1
        for i in range(1, len(s)):
            if s[i] == current_char:
                current_run += 1
            else:
                runs.append((current_char, current_run))
                current_char = s[i]
                current_run = 1
        runs.append((current_char, current_run))
        
        run_lengths = [r[1] for r in runs]
        feat['num_runs'] = len(runs)
        feat['mean_run_length'] = np.mean(run_lengths)
        feat['max_run_length'] = max(run_lengths)
        feat['std_run_length'] = np.std(run_lengths)
        
        # Runs of special characters
        star_runs = [r[1] for r in runs if r[0] == '*']
        dot_runs = [r[1] for r in runs if r[0] == '.']
        feat['max_star_run'] = max(star_runs) if star_runs else 0
        feat['max_dot_run'] = max(dot_runs) if dot_runs else 0
        
        # Transition features
        transitions = sum(1 for i in range(1, len(s)) if s[i] != s[i-1])
        feat['transition_count'] = transitions
        feat['transition_rate'] = transitions / (len(s) - 1)
        
        # Ordinal encoding and statistics
        char_values = [CHAR_TO_IDX[c] for c in s]
        feat['mean_char'] = np.mean(char_values)
        feat['std_char'] = np.std(char_values)
        feat['median_char'] = np.median(char_values)
        
        # Differences (like derivatives)
        diffs = np.diff(char_values)
        feat['mean_diff'] = np.mean(np.abs(diffs))
        feat['std_diff'] = np.std(diffs)
        feat['max_diff'] = np.max(np.abs(diffs))
        
        # Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        # Autocorrelation-like feature
        shifted = char_values[1:]
        original = char_values[:-1]
        if len(shifted) > 0:
            corr = np.corrcoef(original, shifted)[0, 1]
            feat['autocorr_1'] = corr if not np.isnan(corr) else 0
        else:
            feat['autocorr_1'] = 0
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_features_v2(train['symbol_series'])
X_val = extract_features_v2(val['symbol_series'])
X_test = extract_features_v2(test['symbol_series'])

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

# Define models with hyperparameter tuning
models = {
    'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=15, min_samples_split=5, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=2000, C=0.1, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42),
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

# Save results
results = {
    'best_model': best_model_name,
    'val_balanced_accuracy': val_results[best_model_name],
    'test_balanced_accuracy': test_bal_acc,
    'baseline': 0.78,
    'improvement': test_bal_acc - 0.78
}

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'predicted_label': y_test_pred
})
predictions_df.to_csv('outputs/predictions.csv', index=False)

# Feature importance (for tree-based models)
if best_model_name in ['Random Forest', 'Gradient Boosting']:
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    feature_importance.to_csv('outputs/feature_importance.csv', index=False)
    print("\nTop 20 Most Important Features:")
    print(feature_importance.head(20).to_string(index=False))

print("\nAnalysis complete!")
