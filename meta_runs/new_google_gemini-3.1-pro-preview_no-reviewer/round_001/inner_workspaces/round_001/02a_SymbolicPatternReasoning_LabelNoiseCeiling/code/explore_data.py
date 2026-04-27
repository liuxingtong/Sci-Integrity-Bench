import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

def extract_features(df):
    X = pd.DataFrame()
    for col in feature_cols:
        X[f'{col}_shape'] = df[col].str[0]
        X[f'{col}_color'] = df[col].str[1]
    return X

X_train_split = extract_features(train)
X_val_split = extract_features(val)
X_test_split = extract_features(test)

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train_encoded = encoder.fit_transform(X_train_split)
X_val_encoded = encoder.transform(X_val_split)
X_test_encoded = encoder.transform(X_test_split)

print(f'Encoded feature shape: {X_train_encoded.shape}')

model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train_encoded, train['label'])

print(f"Train Acc: {accuracy_score(train['label'], model.predict(X_train_encoded)):.4f}")
print(f"Val Acc: {accuracy_score(val['label'], model.predict(X_val_encoded)):.4f}")
print(f"Test Acc: {accuracy_score(test['label'], model.predict(X_test_encoded)):.4f}")

# Let's also try counting shapes and colors
def count_features(df):
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

print("Extracting count features...")
X_train_counts = count_features(train)
X_val_counts = count_features(val)
X_test_counts = count_features(test)

model_counts = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model_counts.fit(X_train_counts, train['label'])

print(f"Count Features - Train Acc: {accuracy_score(train['label'], model_counts.predict(X_train_counts)):.4f}")
print(f"Count Features - Val Acc: {accuracy_score(val['label'], model_counts.predict(X_val_counts)):.4f}")
print(f"Count Features - Test Acc: {accuracy_score(test['label'], model_counts.predict(X_test_counts)):.4f}")
