import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's try to use the raw string as a categorical feature for a tree model.
# We can use CatBoost or just ordinal encoding.

from sklearn.preprocessing import OrdinalEncoder

enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)

def get_ordinal_features(df):
    features = []
    for s in df['symbol_series']:
        features.append(list(s))
    return np.array(features)

X_train = get_ordinal_features(train)
X_val = get_ordinal_features(val)

X_train_enc = enc.fit_transform(X_train)
X_val_enc = enc.transform(X_val)

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train_enc, train['label'])
y_pred = clf.predict(X_val_enc)
print(f'Ordinal RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=4, n_estimators=200)
clf_xgb.fit(X_train_enc, train['label'])
y_pred_xgb = clf_xgb.predict(X_val_enc)
print(f'Ordinal XGB Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_xgb):.4f}')
