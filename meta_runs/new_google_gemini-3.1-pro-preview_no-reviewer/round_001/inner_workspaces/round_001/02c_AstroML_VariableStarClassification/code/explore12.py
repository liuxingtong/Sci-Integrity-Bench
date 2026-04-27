import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# The baseline is 0.78. This is very high compared to what we are getting (~0.55).
# This means we are missing a very strong feature.
# Let's look at the problem description again: "Classify variable vs non-variable sources using symbol_series features."
# What if the symbols represent a time series of magnitudes, and the letters are just bins?
# u, v, w, x, y, z -> 1, 2, 3, 4, 5, 6
# . and * might be missing data or outliers.

# Let's try to extract features from the continuous segments of data
char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def extract_segment_features(df):
    features = []
    for s in df['symbol_series']:
        # Split by . and *
        import re
        segments = re.split(r'[\.\*]+', s)
        segments = [seg for seg in segments if len(seg) > 0]
        
        if len(segments) == 0:
            features.append({k: 0 for k in ['max_seg_len', 'mean_seg_len', 'n_segments', 'max_seg_var', 'mean_seg_var']})
            continue
            
        seg_lens = [len(seg) for seg in segments]
        seg_vars = [np.var([char_map[c] for c in seg]) if len(seg) > 1 else 0 for seg in segments]
        
        features.append({
            'max_seg_len': np.max(seg_lens),
            'mean_seg_len': np.mean(seg_lens),
            'n_segments': len(segments),
            'max_seg_var': np.max(seg_vars),
            'mean_seg_var': np.mean(seg_vars)
        })
        
    return pd.DataFrame(features)

X_train = extract_segment_features(train)
X_val = extract_segment_features(val)

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

val_pred = model.predict(X_val)
print('Val Acc:', balanced_accuracy_score(y_val, val_pred))
