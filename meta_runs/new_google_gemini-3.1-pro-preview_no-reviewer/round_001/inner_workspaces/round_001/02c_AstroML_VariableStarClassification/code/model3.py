import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

# Try mapping characters to integers
char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def extract_ts_features(df):
    features = []
    for s in df['symbol_series']:
        seq = [char_map[c] for c in s]
        features.append([
            np.mean(seq),
            np.std(seq),
            np.max(seq),
            np.min(seq),
            np.median(seq),
            np.percentile(seq, 25),
            np.percentile(seq, 75),
            np.sum(np.abs(np.diff(seq))), # total variation
            np.max(np.abs(np.diff(seq))), # max diff
            np.var(seq)
        ])
    return np.array(features)

X_train = extract_ts_features(train_df)
X_val = extract_ts_features(val_df)

y_train = train_df['label']
y_val = val_df['label']

model = GradientBoostingClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'TS Features Val Balanced Accuracy: {acc:.4f}')
