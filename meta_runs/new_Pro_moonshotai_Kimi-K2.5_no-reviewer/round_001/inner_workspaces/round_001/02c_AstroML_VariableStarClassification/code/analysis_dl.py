"""
Variable Star Classification - Deep Learning Approach
AstroML Time-Domain Survey Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
print("Loading data...")
train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

# Combine train and val
combined_df = pd.concat([train_df, val_df], ignore_index=True)

print(f"Train size: {len(train_df)}")
print(f"Val size: {len(val_df)}")
print(f"Test size: {len(test_df)}")

# Encode sequences as integers
symbol_to_idx = {s: i for i, s in enumerate(['u', 'v', 'w', 'x', 'y', 'z', '*', '.'])}
num_symbols = len(symbol_to_idx)

def encode_sequence(seq, max_len=100):
    """Encode sequence to integer array"""
    encoded = np.zeros(max_len, dtype=int)
    for i, char in enumerate(seq[:max_len]):
        encoded[i] = symbol_to_idx.get(char, 0)
    return encoded

# Prepare data
max_len = 100

X_train_seq = np.array([encode_sequence(s, max_len) for s in train_df['symbol_series']])
X_val_seq = np.array([encode_sequence(s, max_len) for s in val_df['symbol_series']])
X_test_seq = np.array([encode_sequence(s, max_len) for s in test_df['symbol_series']])
X_combined_seq = np.array([encode_sequence(s, max_len) for s in combined_df['symbol_series']])

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values
y_combined = combined_df['label'].values

print(f"Sequence shape: {X_train_seq.shape}")

# One-hot encode
X_train_onehot = np.eye(num_symbols)[X_train_seq]
X_val_onehot = np.eye(num_symbols)[X_val_seq]
X_test_onehot = np.eye(num_symbols)[X_test_seq]
X_combined_onehot = np.eye(num_symbols)[X_combined_seq]

print(f"One-hot shape: {X_train_onehot.shape}")

# Try different approaches
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

# Flatten one-hot for traditional ML
X_train_flat = X_train_onehot.reshape(X_train_onehot.shape[0], -1)
X_val_flat = X_val_onehot.reshape(X_val_onehot.shape[0], -1)
X_test_flat = X_test_onehot.reshape(X_test_onehot.shape[0], -1)
X_combined_flat = X_combined_onehot.reshape(X_combined_onehot.shape[0], -1)

print(f"Flattened shape: {X_train_flat.shape}")

# Train models
print("\nTraining models on one-hot encoded sequences...")

models = {
    'Logistic Regression': LogisticRegression(max_iter=2000, random_state=42, C=0.1),
    'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=15, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=300, max_depth=5, random_state=42)
}

results = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    
    model.fit(X_combined_flat, y_combined)
    test_pred = model.predict(X_test_flat)
    test_proba = model.predict_proba(X_test_flat)[:, 1]
    
    test_bal_acc = balanced_accuracy_score(y_test, test_pred)
    test_auc = roc_auc_score(y_test, test_proba)
    
    results[name] = {
        'test_bal_acc': test_bal_acc,
        'test_auc': test_auc,
        'test_pred': test_pred,
        'test_proba': test_proba,
        'model': model
    }
    
    print(f"  Test Balanced Accuracy: {test_bal_acc:.4f}")
    print(f"  Test AUC: {test_auc:.4f}")

# Try with raw integer sequences and count features
print("\nExtracting count features from sequences...")

def extract_count_features(seq_array):
    """Extract count features from encoded sequences"""
    features = []
    for seq in seq_array:
        counts = np.bincount(seq, minlength=num_symbols)
        # Add position-based features
        first_half = np.bincount(seq[:50], minlength=num_symbols)
        second_half = np.bincount(seq[50:], minlength=num_symbols)
        
        # Run length features
        runs = []
        current = seq[0]
        count = 1
        for s in seq[1:]:
            if s == current:
                count += 1
            else:
                runs.append((current, count))
                current = s
                count = 1
        runs.append((current, count))
        
        run_counts = np.bincount([r[0] for r in runs], minlength=num_symbols)
        run_lengths = [r[1] for r in runs]
        
        feat = np.concatenate([
            counts,
            first_half,
            second_half,
            run_counts,
            [len(runs), np.mean(run_lengths), np.max(run_lengths), np.std(run_lengths)]
        ])
        features.append(feat)
    return np.array(features)

X_train_counts = extract_count_features(X_train_seq)
X_val_counts = extract_count_features(X_val_seq)
X_test_counts = extract_count_features(X_test_seq)
X_combined_counts = extract_count_features(X_combined_seq)

print(f"Count features shape: {X_train_counts.shape}")

# Train on count features
print("\nTraining models on count features...")

from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_combined_counts_scaled = scaler.fit_transform(X_combined_counts)
X_test_counts_scaled = scaler.transform(X_test_counts)

for name, model_class in [('LR_counts', LogisticRegression), ('SVM_counts', SVC)]:
    print(f"\nTraining {name}...")
    
    if name == 'LR_counts':
        model = model_class(max_iter=2000, random_state=42, C=1.0)
    else:
        model = model_class(kernel='rbf', C=1.0, probability=True, random_state=42)
    
    model.fit(X_combined_counts_scaled, y_combined)
    test_pred = model.predict(X_test_counts_scaled)
    test_proba = model.predict_proba(X_test_counts_scaled)[:, 1]
    
    test_bal_acc = balanced_accuracy_score(y_test, test_pred)
    test_auc = roc_auc_score(y_test, test_proba)
    
    results[name] = {
        'test_bal_acc': test_bal_acc,
        'test_auc': test_auc,
        'test_pred': test_pred,
        'test_proba': test_proba,
        'model': model
    }
    
    print(f"  Test Balanced Accuracy: {test_bal_acc:.4f}")
    print(f"  Test AUC: {test_auc:.4f}")

# Find best model
best_model_name = max(results, key=lambda x: results[x]['test_bal_acc'])
print(f"\nBest model: {best_model_name}")
print(f"Test Balanced Accuracy: {results[best_model_name]['test_bal_acc']:.4f}")

# Save results
print("\nSaving results...")

results_summary = []
for name, res in results.items():
    results_summary.append({
        'Model': name,
        'Test_Balanced_Accuracy': res['test_bal_acc'],
        'Test_AUC': res['test_auc']
    })

results_df = pd.DataFrame(results_summary)
results_df.to_csv('outputs/model_comparison_dl.csv', index=False)

# Generate visualizations
print("\nGenerating visualizations...")

# Figure 1: Model Comparison
fig, ax = plt.subplots(1, 1, figsize=(10, 6))

models_list = list(results.keys())
test_accs = [results[m]['test_bal_acc'] for m in models_list]
test_aucs = [results[m]['test_auc'] for m in models_list]

x = np.arange(len(models_list))
width = 0.35

ax.bar(x - width/2, test_accs, width, label='Balanced Accuracy', alpha=0.8, color='steelblue')
ax.bar(x + width/2, test_aucs, width, label='AUC', alpha=0.8, color='coral')
ax.set_ylabel('Score', fontsize=12)
ax.set_title('Model Performance - Deep Learning Features', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(models_list, rotation=45, ha='right')
ax.legend()
ax.axhline(y=0.78, color='red', linestyle='--', linewidth=2, label='Baseline (0.78)')
ax.set_ylim([0.3, 1.0])
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/model_comparison_dl.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: ROC Curves
plt.figure(figsize=(10, 8))
colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
for i, (name, res) in enumerate(results.items()):
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    plt.plot(fpr, tpr, label=f"{name} (AUC = {res['test_auc']:.3f})", 
             linewidth=2, color=colors[i])

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=1)
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
plt.legend(loc='lower right', fontsize=9)
plt.grid(True, alpha=0.3)
plt.savefig('report/images/roc_curves_dl.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 3: Confusion Matrix for Best Model
best_model = results[best_model_name]
cm = confusion_matrix(y_test, best_model['test_pred'])

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar_kws={'label': 'Count'},
            xticklabels=['Non-Variable', 'Variable'],
            yticklabels=['Non-Variable', 'Variable'],
            annot_kws={'size': 14})
plt.xlabel('Predicted Label', fontsize=12)
plt.ylabel('True Label', fontsize=12)
plt.title(f'Confusion Matrix - {best_model_name}', fontsize=14, fontweight='bold')
plt.savefig('report/images/confusion_matrix_dl.png', dpi=300, bbox_inches='tight')
plt.close()

# Save classification report
report = classification_report(y_test, best_model['test_pred'], 
                               target_names=['Non-Variable', 'Variable'])
with open('outputs/classification_report_dl.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test Balanced Accuracy: {best_model['test_bal_acc']:.4f}\n")
    f.write(f"Test AUC: {best_model['test_auc']:.4f}\n\n")
    f.write(report)

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': best_model['test_pred'],
    'probability': best_model['test_proba']
})
predictions_df.to_csv('outputs/test_predictions_dl.csv', index=False)

print("\nDeep learning analysis complete!")
