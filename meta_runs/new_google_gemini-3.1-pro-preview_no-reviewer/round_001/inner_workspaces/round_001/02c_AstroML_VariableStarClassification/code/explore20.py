import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's try to use the raw string as categorical features for each position
# Since the length is always 40, we have 40 categorical features.

X_train = pd.DataFrame([list(s) for s in train['symbol_series']])
X_val = pd.DataFrame([list(s) for s in val['symbol_series']])

# One-hot encode
X_train_ohe = pd.get_dummies(X_train)
X_val_ohe = pd.get_dummies(X_val)

# Align columns
X_train_ohe, X_val_ohe = X_train_ohe.align(X_val_ohe, join='left', axis=1, fill_value=0)

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train_ohe, y_train)
val_pred = model.predict(X_val_ohe)
print('Position OHE RF Val Acc:', balanced_accuracy_score(y_val, val_pred))

# Let's try XGBoost
import xgboost as xgb
model = xgb.XGBClassifier(n_estimators=500, random_state=42, max_depth=6, learning_rate=0.05)
model.fit(X_train_ohe, y_train)
val_pred = model.predict(X_val_ohe)
print('Position OHE XGB Val Acc:', balanced_accuracy_score(y_val, val_pred))
