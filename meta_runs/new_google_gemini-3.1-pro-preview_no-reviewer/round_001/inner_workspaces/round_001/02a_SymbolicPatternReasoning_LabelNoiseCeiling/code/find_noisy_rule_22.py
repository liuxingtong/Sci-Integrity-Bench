import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Let's try to find the rule by looking at the SOTA reference again.
# "The current state-of-the-art accuracy on SPR_BENCH is 70%."
# If the SOTA is 70%, and we can't find any rule that gets >55% accuracy, then maybe the rule is NOT a simple logical rule.
# Maybe the rule is a linear combination of features, and the noise is 30%.
# But we already tried Logistic Regression and SVM, and they couldn't get >55% validation accuracy.
# Wait, we got 61% train accuracy with Logistic Regression, but only 52% val accuracy.
# This means the model is overfitting the noise.
# If the noise is 30%, the maximum possible validation accuracy is 70%.
# But our validation accuracy is 52%, which is basically random guessing.
# This means our models are NOT learning the true rule AT ALL.

# Why are our models not learning the true rule?
# Because the true rule is not linearly separable in the feature space we provided.
# We provided one-hot encoded tokens, and abstract features like counts.
# What if the rule is based on the *interaction* of tokens at specific positions?
# For example, "token_0 is Tr AND token_1 is Sg".
# We tried this with a Decision Tree, but it failed.
# Let's try to train a model with ALL pairwise interactions of tokens.

from sklearn.preprocessing import PolynomialFeatures, OneHotEncoder
from sklearn.linear_model import LogisticRegression

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train_encoded = encoder.fit_transform(train[feature_cols])

poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
X_train_poly = poly.fit_transform(X_train_encoded)

y_train = train['label']

print(f"Number of features: {X_train_poly.shape[1]}")

# Train Logistic Regression with strong L1 regularization to select features
lr = LogisticRegression(C=0.01, penalty='l1', solver='liblinear', random_state=42)
lr.fit(X_train_poly, y_train)

print(f"Train Acc: {accuracy_score(y_train, lr.predict(X_train_poly)):.4f}")

# Evaluate on validation set
val = pd.read_csv('data/spr_bench_val.csv')
X_val_encoded = encoder.transform(val[feature_cols])
X_val_poly = poly.transform(X_val_encoded)
y_val = val['label']

print(f"Val Acc: {accuracy_score(y_val, lr.predict(X_val_poly)):.4f}")

# Let's try different C values
for C in [0.001, 0.01, 0.1, 1.0]:
    lr = LogisticRegression(C=C, penalty='l1', solver='liblinear', random_state=42)
    lr.fit(X_train_poly, y_train)
    print(f"LR (C={C}) - Train: {accuracy_score(y_train, lr.predict(X_train_poly)):.4f}, Val: {accuracy_score(y_val, lr.predict(X_val_poly)):.4f}")
