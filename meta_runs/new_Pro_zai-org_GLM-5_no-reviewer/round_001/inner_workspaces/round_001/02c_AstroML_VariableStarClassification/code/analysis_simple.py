import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, classification_report
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# Load data
print("Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Encode field_id
field_encoder = LabelEncoder()
field_encoder.fit(train_df['field_id'])
train_field = field_encoder.transform(train_df['field_id'])
val_field = field_encoder.transform(val_df['field_id'])
test_field = field_encoder.transform(test_df['field_id'])

# Symbol mapping
symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
all_symbols = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']

def extract_simple_features(series):
    features = {}
    numerical = np.array([symbol_map[c] for c in series])
    total = len(series)
    
    # Symbol frequencies
    for s in all_symbols:
        features[f'freq_{s}'] = series.count(s) / total
    
    # Basic stats
    features['mean'] = np.mean(numerical)
    features['std'] = np.std(numerical)
    features['var'] = np.var(numerical)
    
    # Special character features
    features['star_count'] = series.count('*')
    features['dot_count'] = series.count('.')
    features['star_dot_ratio'] = series.count('*') / (series.count('.') + 1)
    
    # Transition rate
    transitions = sum(1 for i in range(len(series)-1) if series[i] != series[i+1])
    features['transition_rate'] = transitions / (len(series) - 1)
    
    # Entropy
    probs = [c/total for c in Counter(series).values()]
    features['entropy'] = -sum(p * np.log2(p) for p in probs if p > 0)
    
    # Unique characters
    features['unique_chars'] = len(set(series))
    
    # Key bigrams
    bigrams = Counter([series[i:i+2] for i in range(len(series)-1)])
    key_bigrams = ['**', '..', 'wu', 'xw', 'yz', 'yx', 'vw']
    for bg in key_bigrams:
        features[f'bigram_{bg}'] = bigrams.get(bg, 0) / (len(series) - 1)
    
    return features

def extract_features_df(df):
    return pd.DataFrame([extract_simple_features(s) for s in df['symbol_series']])

print("\n=== Extracting Features ===")
X_train = extract_features_df(train_df)
X_val = extract_features_df(val_df)
X_test = extract_features_df(test_df)

# Add field_id
X_train['field_id'] = train_field
X_val['field_id'] = val_field
X_test['field_id'] = test_field

print(f"Feature matrix shape: {X_train.shape}")

# Fill NaN
X_train = X_train.fillna(0)
X_val = X_val.fillna(0)
X_test = X_test.fillna(0)

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Also try raw numerical encoding
X_train_raw = np.array([[symbol_map[c] for c in s] for s in train_df['symbol_series']])
X_val_raw = np.array([[symbol_map[c] for c in s] for s in val_df['symbol_series']])
X_test_raw = np.array([[symbol_map[c] for c in s] for s in test_df['symbol_series']])

# Add field_id to raw
X_train_raw = np.column_stack([X_train_raw, train_field])
X_val_raw = np.column_stack([X_val_raw, val_field])
X_test_raw = np.column_stack([X_test_raw, test_field])

# Scale raw
scaler_raw = StandardScaler()
X_train_raw_scaled = scaler_raw.fit_transform(X_train_raw)
X_val_raw_scaled = scaler_raw.transform(X_val_raw)
X_test_raw_scaled = scaler_raw.transform(X_test_raw)

# Model training
print("\n=== Model Training ===")

results = {}
best_val_acc = 0
best_test_pred = None
best_test_acc = 0
best_model_name = ""

# 1. Logistic Regression on extracted features
print("\n--- Logistic Regression ---")
for C in [0.001, 0.01, 0.1, 1, 10]:
    lr = LogisticRegression(C=C, max_iter=5000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    val_pred = lr.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = lr.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"LR_C{C}"
    results[name] = {'val': val_acc, 'test': test_acc}
    print(f"LR C={C}: Val={val_acc:.4f}, Test={test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

# 2. Logistic Regression on raw sequence
print("\n--- Logistic Regression on Raw ---")
for C in [0.001, 0.01, 0.1, 1, 10]:
    lr = LogisticRegression(C=C, max_iter=5000, random_state=42)
    lr.fit(X_train_raw_scaled, y_train)
    val_pred = lr.predict(X_val_raw_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = lr.predict(X_test_raw_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"LR_raw_C{C}"
    results[name] = {'val': val_acc, 'test': test_acc}
    print(f"LR_raw C={C}: Val={val_acc:.4f}, Test={test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

# 3. SVM
print("\n--- SVM ---")
for C in [0.01, 0.1, 1, 10, 100]:
    svm = SVC(C=C, kernel='rbf', random_state=42)
    svm.fit(X_train_scaled, y_train)
    val_pred = svm.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = svm.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"SVM_C{C}"
    results[name] = {'val': val_acc, 'test': test_acc}
    print(f"SVM C={C}: Val={val_acc:.4f}, Test={test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

# 4. Random Forest
print("\n--- Random Forest ---")
for n_est in [100, 200, 300]:
    for max_depth in [5, 10, 15, None]:
        rf = RandomForestClassifier(n_estimators=n_est, max_depth=max_depth, 
                                    min_samples_split=5, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        val_pred = rf.predict(X_val)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = rf.predict(X_test)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"RF_{n_est}_{max_depth}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

print(f"Best RF: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 5. Extra Trees
print("\n--- Extra Trees ---")
for n_est in [100, 200, 300]:
    for max_depth in [10, 15, 20]:
        et = ExtraTreesClassifier(n_estimators=n_est, max_depth=max_depth, 
                                  random_state=42, n_jobs=-1)
        et.fit(X_train, y_train)
        val_pred = et.predict(X_val)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = et.predict(X_test)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"ET_{n_est}_{max_depth}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

print(f"Best ET: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 6. Gradient Boosting
print("\n--- Gradient Boosting ---")
for n_est in [100, 200]:
    for lr in [0.05, 0.1]:
        for max_depth in [3, 5]:
            gb = GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, 
                                            max_depth=max_depth, random_state=42)
            gb.fit(X_train, y_train)
            val_pred = gb.predict(X_val)
            val_acc = balanced_accuracy_score(y_val, val_pred)
            test_pred = gb.predict(X_test)
            test_acc = balanced_accuracy_score(y_test, test_pred)
            
            name = f"GB_{n_est}_{lr}_{max_depth}"
            results[name] = {'val': val_acc, 'test': test_acc}
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_test_pred = test_pred
                best_test_acc = test_acc
                best_model_name = name

print(f"Best GB: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

print(f"\n=== Best Model: {best_model_name} ===")
print(f"Validation Balanced Accuracy: {best_val_acc:.4f}")
print(f"Test Balanced Accuracy: {best_test_acc:.4f}")

# Classification report
print("\n=== Classification Report ===")
print(classification_report(y_test, best_test_pred, target_names=['Non-Variable', 'Variable']))

# Save results
results_df = pd.DataFrame([
    {'Model': name, 'Val_Balanced_Accuracy': res['val'], 'Test_Balanced_Accuracy': res['test']}
    for name, res in results.items()
])
results_df = results_df.sort_values('Val_Balanced_Accuracy', ascending=False)
results_df.to_csv('../outputs/model_results.csv', index=False)

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': best_test_pred
})
predictions_df.to_csv('../outputs/predictions.csv', index=False)

print("\n=== Analysis Complete ===")
