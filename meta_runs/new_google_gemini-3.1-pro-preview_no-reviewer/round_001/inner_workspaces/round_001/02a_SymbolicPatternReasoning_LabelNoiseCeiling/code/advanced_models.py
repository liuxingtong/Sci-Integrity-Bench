import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

# Try n-grams
def extract_ngrams(df, n=2):
    X = pd.DataFrame()
    for i, row in df.iterrows():
        tokens = [row[col] for col in feature_cols]
        ngrams = [tuple(tokens[j:j+n]) for j in range(len(tokens)-n+1)]
        for ngram in ngrams:
            col_name = f'ngram_{"_".join(ngram)}'
            if col_name not in X.columns:
                X.loc[i, col_name] = 1
            else:
                X.loc[i, col_name] += 1
    return X.fillna(0)

print("Extracting bigrams...")
# This might be too slow or create too many features, let's just use a simpler approach first

# Let's try a CNN or RNN if simple models fail, but first let's try SVM with RBF kernel
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train_encoded = encoder.fit_transform(train[feature_cols])
X_val_encoded = encoder.transform(val[feature_cols])
X_test_encoded = encoder.transform(test[feature_cols])

print("Training SVM...")
svm = SVC(kernel='rbf', C=1.0, random_state=42)
svm.fit(X_train_encoded, train['label'])

print(f"SVM - Train Acc: {accuracy_score(train['label'], svm.predict(X_train_encoded)):.4f}")
print(f"SVM - Val Acc: {accuracy_score(val['label'], svm.predict(X_val_encoded)):.4f}")
print(f"SVM - Test Acc: {accuracy_score(test['label'], svm.predict(X_test_encoded)):.4f}")

print("Training MLP with regularization...")
mlp = MLPClassifier(hidden_layer_sizes=(256, 128), alpha=0.01, max_iter=1000, random_state=42)
mlp.fit(X_train_encoded, train['label'])

print(f"MLP - Train Acc: {accuracy_score(train['label'], mlp.predict(X_train_encoded)):.4f}")
print(f"MLP - Val Acc: {accuracy_score(val['label'], mlp.predict(X_val_encoded)):.4f}")
print(f"MLP - Test Acc: {accuracy_score(test['label'], mlp.predict(X_test_encoded)):.4f}")
