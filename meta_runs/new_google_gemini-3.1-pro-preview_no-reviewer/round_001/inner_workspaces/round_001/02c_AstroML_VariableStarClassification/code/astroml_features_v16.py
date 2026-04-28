import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the baseline again. 0.78.
# This is a very specific dataset. "AstroML VariableStarClassification"
# In AstroML, there is a dataset of RR Lyrae stars.
# RR Lyrae stars have a very specific light curve shape (steep rise, slow fall).
# If the characters represent magnitudes, then we should look for this shape.
# Let's map the characters to numbers and look for the maximum positive difference (steep rise) and maximum negative difference (slow fall).

char_map = {'*': np.nan, '.': np.nan, 'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def get_shape_features(df):
    features = []
    for s in df['symbol_series']:
        num_s = [char_map[c] for c in s]
        # Interpolate missing values
        s_series = pd.Series(num_s).interpolate(limit_direction='both')
        if s_series.isna().any():
            s_series = s_series.fillna(0)
            
        diffs = s_series.diff().dropna()
        if len(diffs) == 0:
            features.append([0]*5)
            continue
            
        max_rise = diffs.max()
        max_fall = diffs.min()
        mean_rise = diffs[diffs > 0].mean() if len(diffs[diffs > 0]) > 0 else 0
        mean_fall = diffs[diffs < 0].mean() if len(diffs[diffs < 0]) > 0 else 0
        ratio = abs(max_rise / max_fall) if max_fall != 0 else 0
        
        features.append([max_rise, max_fall, mean_rise, mean_fall, ratio])
    return np.array(features)

X_train = get_shape_features(train)
X_val = get_shape_features(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Shape RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

# What if the mapping is different?
char_map2 = {'*': np.nan, '.': np.nan, 'z': 1, 'y': 2, 'x': 3, 'w': 4, 'v': 5, 'u': 6}

def get_shape_features2(df):
    features = []
    for s in df['symbol_series']:
        num_s = [char_map2[c] for c in s]
        s_series = pd.Series(num_s).interpolate(limit_direction='both')
        if s_series.isna().any():
            s_series = s_series.fillna(0)
            
        diffs = s_series.diff().dropna()
        if len(diffs) == 0:
            features.append([0]*5)
            continue
            
        max_rise = diffs.max()
        max_fall = diffs.min()
        mean_rise = diffs[diffs > 0].mean() if len(diffs[diffs > 0]) > 0 else 0
        mean_fall = diffs[diffs < 0].mean() if len(diffs[diffs < 0]) > 0 else 0
        ratio = abs(max_rise / max_fall) if max_fall != 0 else 0
        
        features.append([max_rise, max_fall, mean_rise, mean_fall, ratio])
    return np.array(features)

X_train2 = get_shape_features2(train)
X_val2 = get_shape_features2(val)

clf2 = RandomForestClassifier(n_estimators=100, random_state=42)
clf2.fit(X_train2, train['label'])
y_pred2 = clf2.predict(X_val2)
print(f'Shape2 RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred2):.4f}')
