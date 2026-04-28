import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# The task is "AstroML VariableStarClassification"
# In AstroML, variable stars are often classified using features from their light curves.
# The symbol_series might be a discretized light curve.
# Let's try to map the symbols to numbers based on their ASCII values or a specific order.
# Let's assume the order is *, ., u, v, w, x, y, z
# Or maybe u, v, w, x, y, z are magnitudes and *, . are missing values or outliers?

char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def extract_features(df):
    features = []
    for s in df['symbol_series']:
        num_s = [char_map[c] for c in s]
        
        # Basic stats
        mean = np.mean(num_s)
        std = np.std(num_s)
        skew = pd.Series(num_s).skew()
        kurt = pd.Series(num_s).kurt()
        
        # Percentiles
        p25 = np.percentile(num_s, 25)
        p50 = np.percentile(num_s, 50)
        p75 = np.percentile(num_s, 75)
        iqr = p75 - p25
        
        # Median absolute deviation
        mad = np.median(np.abs(num_s - p50))
        
        # Amplitude
        amp = (np.max(num_s) - np.min(num_s)) / 2.0
        
        # Beyond 1 std
        beyond_1std = np.sum(np.abs(num_s - mean) > std) / len(num_s)
        
        # Stetson J and K indices (simplified)
        n = len(num_s)
        delta = (num_s - mean) / std
        # J is related to correlation of adjacent points
        J = np.sum(delta[:-1] * delta[1:]) / (n - 1)
        # K is related to kurtosis
        K = np.sum(np.abs(delta)) / np.sqrt(n * np.sum(delta**2))
        
        features.append([mean, std, skew, kurt, p25, p50, p75, iqr, mad, amp, beyond_1std, J, K])
        
    return np.array(features)

X_train = extract_features(train)
y_train = train['label']

X_val = extract_features(val)
y_val = val['label']

# Fill NaNs
X_train = np.nan_to_num(X_train)
X_val = np.nan_to_num(X_val)

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_val)
print(f'RF Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred):.4f}')

import xgboost as xgb
clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=4, learning_rate=0.05, n_estimators=200)
clf_xgb.fit(X_train, y_train)
y_pred_xgb = clf_xgb.predict(X_val)
print(f'XGB Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred_xgb):.4f}')
