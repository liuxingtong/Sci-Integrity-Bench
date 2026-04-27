import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Let's reconsider the task name: "LabelNoiseCeiling"
# This strongly implies that the labels are noisy, and the SOTA of 70% is the *ceiling* because of the noise.
# If the noise is 30%, then the true rule should have exactly 70% accuracy on the training set.
# But we haven't found any rule with >54% accuracy.
# This means the true rule is more complex than what we've tried.

# Let's try to use a more powerful model, but with very strong regularization to prevent overfitting the noise.
# We tried this with SVM and Random Forest, but maybe we need to tune the hyperparameters more carefully.

from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(train[feature_cols])
y_train = train['label']

# Let's try a grid search over SVM hyperparameters
param_grid = {
    'C': [0.001, 0.01, 0.1, 1, 10],
    'kernel': ['linear', 'poly', 'rbf', 'sigmoid'],
    'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1]
}

print("Running Grid Search for SVM...")
svm = SVC(random_state=42)
grid_search = GridSearchCV(svm, param_grid, cv=5, scoring='accuracy', n_jobs=-1, verbose=1)
grid_search.fit(X_train, y_train)

print(f"Best parameters: {grid_search.best_params_}")
print(f"Best cross-validation accuracy: {grid_search.best_score_:.4f}")

# Let's evaluate the best model on the validation set
val = pd.read_csv('data/spr_bench_val.csv')
X_val = encoder.transform(val[feature_cols])
y_val = val['label']

best_svm = grid_search.best_estimator_
val_acc = accuracy_score(y_val, best_svm.predict(X_val))
print(f"Validation accuracy: {val_acc:.4f}")
