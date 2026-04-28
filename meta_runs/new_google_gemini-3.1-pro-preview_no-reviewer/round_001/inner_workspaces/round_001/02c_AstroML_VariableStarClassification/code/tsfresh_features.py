import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb
from tsfresh import extract_features
from tsfresh.utilities.dataframe_functions import impute

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def get_tsfresh_df(df):
    data = []
    for i, row in df.iterrows():
        for j, c in enumerate(row['symbol_series']):
            data.append([i, j, char_map[c]])
    return pd.DataFrame(data, columns=['id', 'time', 'value'])

df_train = get_tsfresh_df(train)
df_val = get_tsfresh_df(val)

# Extract features
print("Extracting features for train...")
X_train = extract_features(df_train, column_id='id', column_sort='time', n_jobs=4)
print("Extracting features for val...")
X_val = extract_features(df_val, column_id='id', column_sort='time', n_jobs=4)

# Impute missing values
impute(X_train)
impute(X_val)

# Make sure columns are the same
X_val = X_val[X_train.columns]

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'tsfresh RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=4, n_estimators=200)
clf_xgb.fit(X_train, train['label'])
y_pred_xgb = clf_xgb.predict(X_val)
print(f'tsfresh XGB Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_xgb):.4f}')
