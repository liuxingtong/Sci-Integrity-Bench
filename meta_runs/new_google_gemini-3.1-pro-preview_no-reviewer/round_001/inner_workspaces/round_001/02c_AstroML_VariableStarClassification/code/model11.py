import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import xgboost as xgb
from sklearn.linear_model import LogisticRegression

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

# Let's try to extract features based on the position of characters
# But one-hot encode them
def extract_pos_ohe_features(df):
    features = []
    chars = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']
    char_to_idx = {c: i for i, c in enumerate(chars)}
    for s in df['symbol_series']:
        row = []
        for c in s:
            ohe = [0] * 8
            ohe[char_to_idx[c]] = 1
            row.extend(ohe)
        features.append(row)
    return np.array(features)

X_train = extract_pos_ohe_features(train_df)
X_val = extract_pos_ohe_features(val_df)

y_train = train_df['label']
y_val = val_df['label']

model = xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'XGBoost Positional OHE Val Balanced Accuracy: {acc:.4f}')

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'LR Positional OHE Val Balanced Accuracy: {acc:.4f}')
