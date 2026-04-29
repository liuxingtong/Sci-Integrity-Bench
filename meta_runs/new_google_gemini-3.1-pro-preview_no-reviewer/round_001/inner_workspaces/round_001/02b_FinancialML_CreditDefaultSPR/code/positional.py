import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

def get_positional_features(df):
    features = []
    for seq in df['sym_seq']:
        row = {}
        for i, char in enumerate(seq):
            row[f'pos_{i}_{char}'] = 1
        features.append(row)
    return pd.DataFrame(features).fillna(0)

X_train = get_positional_features(train)
y_train = train['default_flag']

X_val = get_positional_features(val)
for col in X_train.columns:
    if col not in X_val.columns:
        X_val[col] = 0
X_val = X_val[X_train.columns]
y_val = val['default_flag']

print('Train shape:', X_train.shape)

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'XGBoost': xgb.XGBClassifier(eval_metric='logloss', random_state=42)
}

for name, model in models.items():
    model.fit(X_train, y_train)
    y_val_pred = model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, y_val_pred)
    print(f'{name} Val AUC: {auc:.4f}')
