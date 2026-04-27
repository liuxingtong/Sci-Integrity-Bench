import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

# One-hot encoding
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(train[feature_cols])
X_val = encoder.transform(val[feature_cols])
X_test = encoder.transform(test[feature_cols])

y_train = train['label']
y_val = val['label']
y_test = test['label']

print("--- Position-dependent features ---")
# Logistic Regression with strong regularization
for C in [0.001, 0.01, 0.1, 1.0]:
    lr = LogisticRegression(C=C, penalty='l2', random_state=42)
    lr.fit(X_train, y_train)
    print(f"LR (C={C}) - Train: {accuracy_score(y_train, lr.predict(X_train)):.4f}, Val: {accuracy_score(y_val, lr.predict(X_val)):.4f}")

# Decision Tree with low depth
for depth in [1, 2, 3, 4, 5]:
    dt = DecisionTreeClassifier(max_depth=depth, random_state=42)
    dt.fit(X_train, y_train)
    print(f"DT (depth={depth}) - Train: {accuracy_score(y_train, dt.predict(X_train)):.4f}, Val: {accuracy_score(y_val, dt.predict(X_val)):.4f}")

# Count features
def get_counts(df):
    X = pd.DataFrame()
    shapes = ['T', 'S', 'C', 'D']
    colors = ['r', 'g', 'b', 'y']
    for i, row in df.iterrows():
        tokens = [row[col] for col in feature_cols]
        for s in shapes:
            X.loc[i, f'count_shape_{s}'] = sum(1 for t in tokens if t[0] == s)
        for c in colors:
            X.loc[i, f'count_color_{c}'] = sum(1 for t in tokens if t[1] == c)
        for s in shapes:
            for c in colors:
                X.loc[i, f'count_token_{s}{c}'] = sum(1 for t in tokens if t == f'{s}{c}')
    return X

print("\n--- Count features ---")
X_train_counts = get_counts(train)
X_val_counts = get_counts(val)
X_test_counts = get_counts(test)

for C in [0.001, 0.01, 0.1, 1.0]:
    lr = LogisticRegression(C=C, penalty='l2', random_state=42, max_iter=1000)
    lr.fit(X_train_counts, y_train)
    print(f"LR (C={C}) - Train: {accuracy_score(y_train, lr.predict(X_train_counts)):.4f}, Val: {accuracy_score(y_val, lr.predict(X_val_counts)):.4f}")

for depth in [1, 2, 3, 4, 5]:
    dt = DecisionTreeClassifier(max_depth=depth, random_state=42)
    dt.fit(X_train_counts, y_train)
    print(f"DT (depth={depth}) - Train: {accuracy_score(y_train, dt.predict(X_train_counts)):.4f}, Val: {accuracy_score(y_val, dt.predict(X_val_counts)):.4f}")
