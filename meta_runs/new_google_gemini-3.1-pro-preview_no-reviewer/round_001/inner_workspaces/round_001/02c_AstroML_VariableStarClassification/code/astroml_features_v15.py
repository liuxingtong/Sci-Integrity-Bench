import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's think about the problem again. Variable vs non-variable stars.
# Variable stars have periodic changes in brightness.
# Non-variable stars have constant brightness.
# If the characters represent brightness, then variable stars should have a periodic pattern.
# We tried periodogram and it didn't work well.
# What if the characters are NOT brightness, but something else?
# What if the characters are a sequence of observations, and * and . are missing data?
# If * and . are missing data, then variable stars might have more missing data? No, we checked that.
# What if the sequence of u, v, w, x, y, z is the actual data?
# Let's try to extract features only from the non-missing data.

def get_non_missing_features(df):
    features = []
    for s in df['symbol_series']:
        clean_s = s.replace('*', '').replace('.', '')
        if len(clean_s) == 0:
            features.append([0]*10)
            continue
            
        num_s = [{'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}[c] for c in clean_s]
        
        features.append([
            np.mean(num_s),
            np.std(num_s),
            np.max(num_s) - np.min(num_s),
            np.median(num_s),
            pd.Series(num_s).skew(),
            pd.Series(num_s).kurt(),
            len(num_s),
            np.sum(np.abs(np.diff(num_s))),
            np.var(np.diff(num_s)) if len(num_s) > 1 else 0,
            np.max(np.abs(np.diff(num_s))) if len(num_s) > 1 else 0
        ])
    return np.array(features)

X_train = get_non_missing_features(train)
X_val = get_non_missing_features(val)

X_train = np.nan_to_num(X_train)
X_val = np.nan_to_num(X_val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Non-missing RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=3, n_estimators=100)
clf_xgb.fit(X_train, train['label'])
y_pred_xgb = clf_xgb.predict(X_val)
print(f'Non-missing XGB Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_xgb):.4f}')
