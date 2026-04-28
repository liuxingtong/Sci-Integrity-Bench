import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb
from scipy.signal import periodogram

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Try different mappings
mappings = [
    {'.': 0, 'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '*': 7},
    {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7},
    {'u': 0, 'v': 1, 'w': 2, 'x': 3, 'y': 4, 'z': 5, '.': 6, '*': 7},
]

def extract_ts_features(df, char_map):
    features = []
    for s in df['symbol_series']:
        num_s = [char_map[c] for c in s]
        
        mean = np.mean(num_s)
        std = np.std(num_s)
        median = np.median(num_s)
        maximum = np.max(num_s)
        minimum = np.min(num_s)
        amplitude = maximum - minimum
        
        # Periodicity
        f, Pxx = periodogram(num_s)
        max_power = np.max(Pxx)
        max_freq = f[np.argmax(Pxx)]
        
        # Autocorrelation
        autocorr_1 = pd.Series(num_s).autocorr(lag=1)
        autocorr_2 = pd.Series(num_s).autocorr(lag=2)
        
        # Differences
        diffs = np.diff(num_s)
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        max_diff = np.max(np.abs(diffs))
        
        features.append([
            mean, std, median, maximum, minimum, amplitude, 
            max_power, max_freq, 
            autocorr_1, autocorr_2,
            mean_diff, std_diff, max_diff
        ])
        
    return np.array(features)

for i, char_map in enumerate(mappings):
    print(f'\n--- Mapping {i} ---')
    X_train = extract_ts_features(train, char_map)
    y_train = train['label']
    
    X_val = extract_ts_features(val, char_map)
    y_val = val['label']
    
    # Fill NaNs (autocorr might be NaN if variance is 0)
    X_train = np.nan_to_num(X_train)
    X_val = np.nan_to_num(X_val)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_val)
    print(f'RF Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred):.4f}')
    
    clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=3, learning_rate=0.1, n_estimators=100)
    clf_xgb.fit(X_train, y_train)
    y_pred_xgb = clf_xgb.predict(X_val)
    print(f'XGB Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred_xgb):.4f}')
