import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's try to use the Levenshtein distance to the nearest neighbor in the training set.
import Levenshtein

def get_knn_features(df_train, df_test):
    features = []
    for s_test in df_test['symbol_series']:
        dists_0 = []
        dists_1 = []
        for _, row in df_train.iterrows():
            d = Levenshtein.distance(s_test, row['symbol_series'])
            if row['label'] == 0:
                dists_0.append(d)
            else:
                dists_1.append(d)
        
        dists_0.sort()
        dists_1.sort()
        
        features.append([
            np.mean(dists_0[:5]), np.mean(dists_1[:5]),
            np.min(dists_0), np.min(dists_1),
            np.median(dists_0), np.median(dists_1)
        ])
    return np.array(features)

X_train = get_knn_features(train, train)
X_val = get_knn_features(train, val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'KNN RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=3, n_estimators=100)
clf_xgb.fit(X_train, train['label'])
y_pred_xgb = clf_xgb.predict(X_val)
print(f'KNN XGB Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_xgb):.4f}')
