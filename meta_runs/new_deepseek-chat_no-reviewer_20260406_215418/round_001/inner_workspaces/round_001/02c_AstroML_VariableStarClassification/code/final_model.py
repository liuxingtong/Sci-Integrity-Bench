import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import Pipeline
import os
import joblib

# Set up paths
data_dir = '../data'
output_dir = '../outputs'
report_img_dir = '../report/images'

# Load data
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
test_df = pd.read_csv(os.path.join(data_dir, 'test.csv'))

# Define symbols
symbols = ['*', 'v', 'w', 'z', 'y', 'u', '.', 'x']
symbol_to_idx = {sym: i for i, sym in enumerate(symbols)}

# Based on previous analysis, these positions showed largest differences
key_positions = [1, 5, 12, 17, 18, 24, 25]

# Create focused feature set
def create_focused_features(df):
    features_list = []
    
    for idx, row in df.iterrows():
        series = row['symbol_series']
        features = {}
        
        # Key positions (one-hot encoded)
        for pos in key_positions:
            if pos < len(series):
                sym = series[pos]
                for s in symbols:
                    features[f'pos{pos}_{s}'] = 1 if s == sym else 0
        
        # Overall statistics
        total_len = len(series)
        for sym in symbols:
            features[f'freq_{sym}'] = series.count(sym) / total_len
        
        # Run length features
        runs = []
        current_run = 1
        for i in range(1, len(series)):
            if series[i] == series[i-1]:
                current_run += 1
            else:
                runs.append(current_run)
                current_run = 1
        runs.append(current_run)
        
        features['max_run'] = max(runs) if runs else 0
        features['mean_run'] = np.mean(runs) if runs else 0
        features['run_std'] = np.std(runs) if runs else 0
        
        # Change rate
        changes = sum(1 for i in range(1, len(series)) if series[i] != series[i-1])
        features['change_rate'] = changes / (len(series) - 1)
        
        # Field_id
        features['field_id'] = int(row['field_id'][3:])
        
        # Label
        features['label'] = row['label']
        features['object_id'] = row['object_id']
        
        features_list.append(features)
    
    return pd.DataFrame(features_list)

print("Creating focused features...")
train_features = create_focused_features(train_df)
val_features = create_focused_features(val_df)
test_features = create_focused_features(test_df)

print(f"Training features shape: {train_features.shape}")
print(f"Validation features shape: {val_features.shape}")
print(f"Test features shape: {test_features.shape}")

# Prepare data
def prepare_data(df):
    feature_cols = [col for col in df.columns if col not in ['object_id', 'label']]
    X = df[feature_cols].values
    y = df['label'].values
    return X, y, feature_cols

X_train, y_train, feature_cols = prepare_data(train_features)
X_val, y_val, _ = prepare_data(val_features)
X_test, y_test, _ = prepare_data(test_features)

print(f"\nNumber of features: {len(feature_cols)}")
print(f"First 10 features: {feature_cols[:10]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Try different models with hyperparameter tuning
models = {
    'RF': RandomForestClassifier(n_estimators=200, max_depth=15, min_samples_split=5, 
                                 random_state=42, class_weight='balanced'),
    'GB': GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, 
                                     random_state=42, subsample=0.8),
    'SVM': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, 
               random_state=42, class_weight='balanced'),
    'LR': LogisticRegression(C=0.5, penalty='l2', solver='liblinear', 
                             random_state=42, class_weight='balanced', max_iter=1000)
}

results = {}
for name, model in models.items():
    print(f"\n=== Training {name} ===")
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='balanced_accuracy')
    
    # Train on full training set
    model.fit(X_train_scaled, y_train)
    
    # Validation
    y_val_pred = model.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, y_val_pred)
    
    # Validation probabilities for AUC
    if hasattr(model, 'predict_proba'):
        y_val_prob = model.predict_proba(X_val_scaled)[:, 1]
        val_auc = roc_auc_score(y_val, y_val_prob)
    else:
        val_auc = 0
    
    print(f"CV mean accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    print(f"Validation accuracy: {val_acc:.4f}")
    if val_auc > 0:
        print(f"Validation AUC: {val_auc:.4f}")
    
    results[name] = {
        'model': model,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'val_acc': val_acc,
        'val_auc': val_auc
    }

# Best model on validation
best_name = max(results, key=lambda x: results[x]['val_acc'])
best_model = results[best_name]['model']
print(f"\n=== Best Model: {best_name} ===")
print(f"Validation accuracy: {results[best_name]['val_acc']:.4f}")

# Test evaluation
y_test_pred = best_model.predict(X_test_scaled)
test_acc = balanced_accuracy_score(y_test, y_test_pred)

if hasattr(best_model, 'predict_proba'):
    y_test_prob = best_model.predict_proba(X_test_scaled)[:, 1]
    test_auc = roc_auc_score(y_test, y_test_prob)
else:
    test_auc = 0

print(f"\nTest accuracy: {test_acc:.4f}")
if test_auc > 0:
    print(f"Test AUC: {test_auc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_test_pred))

# Confusion matrix
cm = confusion_matrix(y_test, y_test_pred)
print("Confusion Matrix:")
print(cm)

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Non-variable', 'Variable'],
            yticklabels=['Non-variable', 'Variable'])
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title(f'Confusion Matrix - {best_name}\nTest Accuracy: {test_acc:.4f}')
plt.tight_layout()
plt.savefig(os.path.join(report_img_dir, 'final_confusion_matrix.png'), dpi=150)
plt.close()

# Plot model comparison
plt.figure(figsize=(10, 6))
model_names = list(results.keys())
val_accs = [results[name]['val_acc'] for name in model_names]
test_accs = [test_acc if name == best_name else 0 for name in model_names]  # Only show test for best model

x = np.arange(len(model_names))
width = 0.35

plt.bar(x - width/2, val_accs, width, label='Validation Accuracy', color='skyblue')
plt.bar(x + width/2, test_accs, width, label='Test Accuracy (best only)', color='lightcoral')

plt.xlabel('Model')
plt.ylabel('Balanced Accuracy')
plt.title('Model Performance Comparison')
plt.xticks(x, model_names)
plt.legend()
plt.ylim([0.4, 0.8])
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(report_img_dir, 'final_model_comparison.png'), dpi=150)
plt.close()

# Feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    print("\n=== Feature Importance ===")
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("Top 20 most important features:")
    for i in range(min(20, len(feature_cols))):
        print(f"{i+1:2d}. {feature_cols[indices[i]]}: {importances[indices[i]]:.4f}")
    
    # Plot feature importance
    plt.figure(figsize=(12, 8))
    top_n = min(15, len(feature_cols))
    plt.barh(range(top_n), importances[indices[:top_n]][::-1])
    plt.yticks(range(top_n), [feature_cols[indices[i]] for i in range(top_n-1, -1, -1)])
    plt.xlabel('Feature Importance')
    plt.title(f'Top {top_n} Features - {best_name}')
    plt.tight_layout()
    plt.savefig(os.path.join(report_img_dir, 'final_feature_importance.png'), dpi=150)
    plt.close()

# Save results
print("\n=== Saving Results ===")
results_df = pd.DataFrame({
    'Model': list(results.keys()),
    'CV Mean': [results[name]['cv_mean'] for name in results.keys()],
    'CV Std': [results[name]['cv_std'] for name in results.keys()],
    'Validation Acc': [results[name]['val_acc'] for name in results.keys()],
    'Validation AUC': [results[name]['val_auc'] for name in results.keys()]
})
results_df = results_df.sort_values('Validation Acc', ascending=False)
print(results_df)

results_df.to_csv(os.path.join(output_dir, 'final_model_results.csv'), index=False)
joblib.dump(best_model, os.path.join(output_dir, 'final_best_model.pkl'))
joblib.dump(scaler, os.path.join(output_dir, 'final_scaler.pkl'))

print("\nFinal modeling complete!")
