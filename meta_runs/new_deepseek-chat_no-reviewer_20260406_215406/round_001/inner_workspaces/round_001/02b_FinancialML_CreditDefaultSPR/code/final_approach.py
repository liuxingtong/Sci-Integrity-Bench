import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, roc_curve, confusion_matrix
import pickle
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

# Create one-hot encoding for each position
chars = ['1', '2', 'A', 'B', 'C', 'D']

print("Creating position-specific one-hot features...")

def create_position_features(df):
    """Create one-hot encoding for each position in the sequence"""
    features_list = []
    
    for seq in df['sym_seq']:
        features = {}
        # For each position, create one-hot encoding
        for i, char in enumerate(seq):
            for c in chars:
                features[f'pos{i}_{c}'] = 1 if char == c else 0
        features_list.append(features)
    
    return pd.DataFrame(features_list)

# Create features
train_features = create_position_features(train)
val_features = create_position_features(val)
test_features = create_position_features(test)

print(f"Train features shape: {train_features.shape}")
print(f"Val features shape: {val_features.shape}")
print(f"Test features shape: {test_features.shape}")

# Get target variables
y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

# Try Logistic Regression with strong regularization
print("\nTraining Logistic Regression with L1 regularization...")

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(train_features)
X_val_scaled = scaler.transform(val_features)
X_test_scaled = scaler.transform(test_features)

# Try different regularization strengths
best_auc = 0
best_model = None
best_c = None

for C in [0.001, 0.01, 0.1, 1, 10, 100]:
    model = LogisticRegression(
        C=C,
        penalty='l1',
        solver='liblinear',
        max_iter=1000,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train_scaled, y_train)
    
    y_val_prob = model.predict_proba(X_val_scaled)[:, 1]
    auc = roc_auc_score(y_val, y_val_prob)
    
    print(f"  C={C:.3f}, Validation AUC: {auc:.4f}")
    
    if auc > best_auc:
        best_auc = auc
        best_model = model
        best_c = C

print(f"\nBest C: {best_c}, Best Validation AUC: {best_auc:.4f}")

# Evaluate on test set
y_test_prob = best_model.predict_proba(X_test_scaled)[:, 1]
y_test_pred = best_model.predict(X_test_scaled)

test_auc = roc_auc_score(y_test, y_test_prob)
test_accuracy = accuracy_score(y_test, y_test_pred)
test_precision = precision_score(y_test, y_test_pred)
test_recall = recall_score(y_test, y_test_pred)
test_f1 = f1_score(y_test, y_test_pred)

print("\n" + "="*60)
print("Test Set Performance (Logistic Regression with L1):")
print("="*60)
print(f"AUC: {test_auc:.4f}")
print(f"Accuracy: {test_accuracy:.4f}")
print(f"Precision: {test_precision:.4f}")
print(f"Recall: {test_recall:.4f}")
print(f"F1 Score: {test_f1:.4f}")

# Compare with baseline
baseline_auc = 0.72
print(f"\nBaseline AUC: {baseline_auc:.4f}")
print(f"Our model AUC: {test_auc:.4f}")
print(f"Difference: {test_auc - baseline_auc:.4f}")

# Check feature coefficients to understand what matters
coef = best_model.coef_[0]
feature_names = train_features.columns

# Get top positive and negative coefficients
coef_df = pd.DataFrame({
    'feature': feature_names,
    'coefficient': coef,
    'abs_coef': np.abs(coef)
})
coef_df = coef_df.sort_values('abs_coef', ascending=False)

print("\nTop 10 most important features (by absolute coefficient):")
for i, row in coef_df.head(10).iterrows():
    print(f"  {row['feature']}: {row['coefficient']:.4f}")

# Save model
os.makedirs('../outputs', exist_ok=True)
with open('../outputs/final_lr_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)
with open('../outputs/final_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("\nModel saved to outputs/final_lr_model.pkl")

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# Plot 1: ROC curve
fig, ax = plt.subplots(figsize=(8, 6))

fpr, tpr, thresholds = roc_curve(y_test, y_test_prob)

ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {test_auc:.3f})')
ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('ROC Curve - Logistic Regression with L1 Regularization')
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/final_roc_curve.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Top feature coefficients
fig, ax = plt.subplots(figsize=(12, 8))

top_n = 20
top_features = coef_df.head(top_n)

# Create horizontal bar chart
colors = ['red' if coef < 0 else 'blue' for coef in top_features['coefficient']]
y_pos = np.arange(top_n)
ax.barh(y_pos, top_features['coefficient'], align='center', color=colors)
ax.set_yticks(y_pos)
ax.set_yticklabels(top_features['feature'])
ax.invert_yaxis()  # Most important on top
ax.set_xlabel('Coefficient Value')
ax.set_title(f'Top {top_n} Feature Coefficients (Red=Negative, Blue=Positive)')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/feature_coefficients.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualizations saved to report/images/")
