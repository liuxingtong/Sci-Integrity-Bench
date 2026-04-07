import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, StratifiedKFold
import os
import joblib

# Set up paths
data_dir = '../data'
output_dir = '../outputs'

# Load data
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
test_df = pd.read_csv(os.path.join(data_dir, 'test.csv'))

# Define symbols
symbols = ['*', 'v', 'w', 'z', 'y', 'u', '.', 'x']
symbol_to_idx = {sym: i for i, sym in enumerate(symbols)}

# Create positional features
def create_positional_features(df):
    features_list = []
    
    for idx, row in df.iterrows():
        series = row['symbol_series']
        features = {}
        
        # One-hot encode each position (simplified: just the symbol index)
        for pos in range(len(series)):
            sym = series[pos]
            # Instead of full one-hot, use encoded value
            features[f'pos_{pos}'] = symbol_to_idx[sym]
        
        # Add field_id
        features['field_id'] = int(row['field_id'][3:])
        
        # Add label
        features['label'] = row['label']
        features['object_id'] = row['object_id']
        
        features_list.append(features)
    
    return pd.DataFrame(features_list)

print("Creating positional features...")
train_features_pos = create_positional_features(train_df)
val_features_pos = create_positional_features(val_df)
test_features_pos = create_positional_features(test_df)

print(f"Training features shape: {train_features_pos.shape}")
print(f"Validation features shape: {val_features_pos.shape}")
print(f"Test features shape: {test_features_pos.shape}")

# Prepare data
def prepare_data(df):
    feature_cols = [col for col in df.columns if col not in ['object_id', 'label']]
    X = df[feature_cols].values
    y = df['label'].values
    return X, y, feature_cols

X_train, y_train, feature_cols = prepare_data(train_features_pos)
X_val, y_val, _ = prepare_data(val_features_pos)
X_test, y_test, _ = prepare_data(test_features_pos)

print(f"\nNumber of features: {len(feature_cols)}")

# Try different models
models = {
    'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced'),
    'LogisticRegression': LogisticRegression(C=0.1, max_iter=1000, random_state=42, class_weight='balanced'),
    'SVM_linear': SVC(kernel='linear', C=0.1, random_state=42, class_weight='balanced'),
}

results = {}
for name, model in models.items():
    print(f"\n=== Training {name} ===")
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='balanced_accuracy')
    
    # Train on full training set
    model.fit(X_train, y_train)
    
    # Validation
    y_val_pred = model.predict(X_val)
    val_acc = balanced_accuracy_score(y_val, y_val_pred)
    
    print(f"CV mean accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    print(f"Validation accuracy: {val_acc:.4f}")
    
    results[name] = {
        'model': model,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'val_acc': val_acc
    }

# Best model on validation
best_name = max(results, key=lambda x: results[x]['val_acc'])
best_model = results[best_name]['model']
print(f"\n=== Best Model: {best_name} ===")
print(f"Validation accuracy: {results[best_name]['val_acc']:.4f}")

# Test evaluation
y_test_pred = best_model.predict(X_test)
test_acc = balanced_accuracy_score(y_test, y_test_pred)
print(f"\nTest accuracy: {test_acc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_test_pred))

# Save results
print("\n=== Saving Results ===")
results_df = pd.DataFrame({
    'Model': list(results.keys()),
    'CV Mean': [results[name]['cv_mean'] for name in results.keys()],
    'CV Std': [results[name]['cv_std'] for name in results.keys()],
    'Validation Acc': [results[name]['val_acc'] for name in results.keys()]
})
print(results_df)

# Try ensemble of models
print("\n=== Trying Ensemble ===")
from sklearn.ensemble import VotingClassifier

# Create ensemble
ensemble = VotingClassifier(
    estimators=[(name, models[name]) for name in models.keys()],
    voting='hard'
)

ensemble.fit(X_train, y_train)
y_val_ens = ensemble.predict(X_val)
val_acc_ens = balanced_accuracy_score(y_val, y_val_ens)
print(f"Ensemble validation accuracy: {val_acc_ens:.4f}")

y_test_ens = ensemble.predict(X_test)
test_acc_ens = balanced_accuracy_score(y_test, y_test_ens)
print(f"Ensemble test accuracy: {test_acc_ens:.4f}")

print("\nEnsemble Classification Report:")
print(classification_report(y_test, y_test_ens))
