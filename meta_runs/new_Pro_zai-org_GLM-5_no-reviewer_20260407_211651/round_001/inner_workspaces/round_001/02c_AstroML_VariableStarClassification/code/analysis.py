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
print(f"Label distribution - Train: {train['label'].value_counts().to_dict()}")

# Define the character set
CHARS = ['x', 'w', 'z', 'u', '*', 'y', 'v', '.']
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}

def extract_features(symbol_series):
    """Extract features from symbol series"""
    features = []
    
    for s in symbol_series:
        feat = {}
        
        # Character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # Position-based features (first 10, middle 20, last 10)
        first10 = s[:10]
        middle20 = s[10:30]
        last10 = s[30:]
        
        for c in CHARS:
            feat[f'freq_first10_{c}'] = first10.count(c) / 10
            feat[f'freq_middle20_{c}'] = middle20.count(c) / 20
            feat[f'freq_last10_{c}'] = last10.count(c) / 10
        
        # Transition features (bigrams)
        transitions = Counter()
        for i in range(len(s) - 1):
            trans = s[i:i+2]
            transitions[trans] += 1
        
        # Most common transitions
        for c1 in CHARS:
            for c2 in CHARS:
                trans = c1 + c2
                feat[f'trans_{c1}{c2}'] = transitions.get(trans, 0) / (len(s) - 1)
        
        # Special character features
        feat['star_count'] = s.count('*')
        feat['dot_count'] = s.count('.')
        feat['star_dot_ratio'] = (s.count('*') + 1) / (s.count('.') + 1)
        
        # Run-length features
        max_run = 1
        current_run = 1
        for i in range(1, len(s)):
            if s[i] == s[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        feat['max_run_length'] = max_run
        
        # Variability features (treating chars as ordinal)
        char_values = [CHAR_TO_IDX[c] for c in s]
        feat['mean_char'] = np.mean(char_values)
        feat['std_char'] = np.std(char_values)
        feat['range_char'] = max(char_values) - min(char_values)
        
        # Number of transitions between different character types
        transitions_count = sum(1 for i in range(1, len(s)) if s[i] != s[i-1])
        feat['transition_count'] = transitions_count
        
        # Entropy of character distribution
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_features(train['symbol_series'])
X_val = extract_features(val['symbol_series'])
X_test = extract_features(test['symbol_series'])

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
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', probability=True, random_state=42),
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
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))

print("\nAnalysis complete!")
