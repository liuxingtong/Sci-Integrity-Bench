import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(train[feature_cols])
X_val = encoder.transform(val[feature_cols])

y_train = train['label']
y_val = val['label']

print("--- Logistic Regression ---")
for C in [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0]:
    lr = LogisticRegression(C=C, penalty='l1', solver='liblinear', random_state=42)
    lr.fit(X_train, y_train)
    print(f"L1 LR (C={C}) - Train: {accuracy_score(y_train, lr.predict(X_train)):.4f}, Val: {accuracy_score(y_val, lr.predict(X_val)):.4f}")

print("\n--- SVM ---")
for C in [0.01, 0.1, 1.0, 10.0]:
    for kernel in ['linear', 'poly', 'rbf']:
        svm = SVC(C=C, kernel=kernel, degree=2, random_state=42)
        svm.fit(X_train, y_train)
        print(f"SVM (C={C}, kernel={kernel}) - Train: {accuracy_score(y_train, svm.predict(X_train)):.4f}, Val: {accuracy_score(y_val, svm.predict(X_val)):.4f}")

print("\n--- Random Forest ---")
for depth in [2, 4, 6, 8, 10]:
    for min_samples_leaf in [1, 5, 10, 20]:
        rf = RandomForestClassifier(max_depth=depth, min_samples_leaf=min_samples_leaf, random_state=42)
        rf.fit(X_train, y_train)
        print(f"RF (depth={depth}, min_leaf={min_samples_leaf}) - Train: {accuracy_score(y_train, rf.predict(X_train)):.4f}, Val: {accuracy_score(y_val, rf.predict(X_val)):.4f}")

print("\n--- MLP ---")
for alpha in [0.001, 0.01, 0.1, 1.0, 10.0]:
    mlp = MLPClassifier(hidden_layer_sizes=(64,), alpha=alpha, max_iter=1000, random_state=42)
    mlp.fit(X_train, y_train)
    print(f"MLP (alpha={alpha}) - Train: {accuracy_score(y_train, mlp.predict(X_train)):.4f}, Val: {accuracy_score(y_val, mlp.predict(X_val)):.4f}")
