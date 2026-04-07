import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, roc_curve
import pickle
import os
import matplotlib.pyplot as plt

# Load all data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

# Combine train and val
combined = pd.concat([train, val], ignore_index=True)
print(f"Combined data: {len(combined)} samples")
print(f"Test data: {len(test)} samples")

# Create simple but effective features based on pattern analysis
chars = ['1', '2', 'A', 'B', 'C', 'D']

def create_simple_features(df):
    """Create features based on strongest patterns from analysis"""
    features_list = []
    
    for seq in df['sym_seq']:
        features = {}
        
        # 1. Key position features from pattern analysis
        key_positions = {
            9: 'D',  # Strong negative association with default
            7: 'B',  # Strong negative association
            5: 'C',  # Strong positive association
            1: 'B',  # Strong positive association
            19: '1', # Strong positive association
            18: 'D', # Strong negative association
            13: 'D', # Strong negative association
            14: 'C', # Strong negative association
            4: '1',  # Strong negative association
            11: 'D', # Strong negative association
        }
        
        for pos, char in key_positions.items():
            features[f'pos{pos}_{char}'] = 1 if seq[pos] == char else 0
        
        # 2. Character frequencies
        for char in chars:
            features[f'freq_{char}'] = seq.count(char) / len(seq)
        
        # 3. Important bigrams from analysis
        important_bigrams = ['21', '11', 'DC', 'BD', 'CD', '1C', '22']
        for bigram in important_bigrams:
            features[f'bigram_{bigram}'] = seq.count(bigram)
        
        # 4. First and last character
        features['first_is_digit'] = 1 if seq[0] in ['1', '2'] else 0
        features['last_is_digit'] = 1 if seq[-1] in ['1', '2'] else 0
        
        # 5. Run statistics
        max_run = 1
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        features['max_run'] = max_run
        
        features_list.append(features)
    
    return pd.DataFrame(features_list)

print("\nCreating features...")
X_combined = create_simple_features(combined)
y_combined = combined['default_flag'].values

X_test = create_simple_features(test)
y_test = test['default_flag'].values

print(f"Feature shape: {X_combined.shape}")
print(f"Number of features: {X_combined.shape[1]}")

# Standardize
scaler = StandardScaler()
X_combined_scaled = scaler.fit_transform(X_combined)
X_test_scaled = scaler.transform(X_test)

# Try different models
models = {
    'Logistic Regression (L1)': LogisticRegression(
        C=0.1, penalty='l1', solver='liblinear', max_iter=1000, random_state=42, class_weight='balanced'
    ),
    'Logistic Regression (L2)': LogisticRegression(
        C=0.1, penalty='l2', max_iter=1000, random_state=42, class_weight='balanced'
    ),
    'Random Forest': RandomForestClassifier(
        n_estimators=200, max_depth=10, random_state=42, class_weight='balanced'
    ),
    'Gradient Boosting': GradientBoostingClassifier(
        n_estimators=200, max_depth=3, learning_rate=0.1, random_state=42
    )
}

print("\nTraining models on combined data...")
results = []

for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_combined_scaled, y_combined)
    
    y_test_prob = model.predict_proba(X_test_scaled)[:, 1]
    y_test_pred = model.predict(X_test_scaled)
    
    auc = roc_auc_score(y_test, y_test_prob)
    accuracy = accuracy_score(y_test, y_test_pred)
    f1 = f1_score(y_test, y_test_pred)
    
    print(f"  Test AUC: {auc:.4f}")
    print(f"  Test Accuracy: {accuracy:.4f}")
    print(f"  Test F1: {f1:.4f}")
    
    results.append({
        'Model': name,
        'AUC': auc,
        'Accuracy': accuracy,
        'F1': f1
    })
    
    # Save the best model
    if name == 'Logistic Regression (L1)':
        with open('../outputs/final_combined_model.pkl', 'wb') as f:
            pickle.dump(model, f)
        with open('../outputs/final_combined_scaler.pkl', 'wb') as f:
            pickle.dump(scaler, f)

# Show results
results_df = pd.DataFrame(results)
print("\n" + "="*60)
print("Test Set Performance (trained on combined train+val):")
print("="*60)
print(results_df.to_string(index=False))

# Compare with baseline
baseline_auc = 0.72
best_auc = results_df['AUC'].max()
print(f"\nBaseline AUC: {baseline_auc:.4f}")
print(f"Best model AUC: {best_auc:.4f}")
print(f"Difference: {best_auc - baseline_auc:.4f}")

# Create visualization
os.makedirs('../report/images', exist_ok=True)

# Plot model comparison
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(results_df))
width = 0.25

ax.bar(x - width, results_df['AUC'], width, label='AUC', color='skyblue')
ax.bar(x, results_df['Accuracy'], width, label='Accuracy', color='lightgreen')
ax.bar(x + width, results_df['F1'], width, label='F1', color='salmon')

ax.set_xlabel('Model')
ax.set_ylabel('Score')
ax.set_title('Model Performance on Test Set')
ax.set_xticks(x)
ax.set_xticklabels(results_df['Model'], rotation=45, ha='right')
ax.legend()
ax.grid(True, alpha=0.3)

# Add value labels
for i, (auc, acc, f1) in enumerate(zip(results_df['AUC'], results_df['Accuracy'], results_df['F1'])):
    ax.text(i - width, auc + 0.01, f'{auc:.3f}', ha='center', va='bottom', fontsize=8)
    ax.text(i, acc + 0.01, f'{acc:.3f}', ha='center', va='bottom', fontsize=8)
    ax.text(i + width, f1 + 0.01, f'{f1:.3f}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('../report/images/combined_training_results.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to report/images/combined_training_results.png")
