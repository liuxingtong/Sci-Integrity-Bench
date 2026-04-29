import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb
from scipy.stats import skew, kurtosis

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

# Assume ASCII ordering for now
char_map = {c: ord(c) for c in ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']}
# Or maybe rank ordering
char_map_rank = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def extract_features(df, cmap):
    features = []
    for s in df['symbol_series']:
        seq = np.array([cmap[c] for c in s], dtype=float)
        
        mean = np.mean(seq)
        std = np.std(seq)
        var = np.var(seq)
        ptp = np.ptp(seq)
        
        # von Neumann ratio
        vn_ratio = np.sum(np.diff(seq)**2) / (var * (len(seq) - 1)) if var > 0 else 0
        
        # Stetson K (robust kurtosis)
        # simplified
        
        skewness = skew(seq)
        kurt = kurtosis(seq)
        
        # Median absolute deviation
        mad = np.median(np.abs(seq - np.median(seq)))
        
        # Autocorrelation at lag 1, 2, 3
        ac1 = pd.Series(seq).autocorr(lag=1)
        ac2 = pd.Series(seq).autocorr(lag=2)
        ac3 = pd.Series(seq).autocorr(lag=3)
        
        # Number of peaks/valleys
        diffs = np.diff(seq)
        peaks = np.sum((diffs[:-1] > 0) & (diffs[1:] < 0))
        valleys = np.sum((diffs[:-1] < 0) & (diffs[1:] > 0))
        
        row = [mean, std, var, ptp, vn_ratio, skewness, kurt, mad, ac1, ac2, ac3, peaks, valleys]
        features.append(row)
    return np.array(features)

for name, cmap in [('ASCII', char_map), ('Rank', char_map_rank)]:
    X_train = extract_features(train_df, cmap)
    X_val = extract_features(val_df, cmap)
    
    # Replace NaNs with 0
    X_train = np.nan_to_num(X_train)
    X_val = np.nan_to_num(X_val)
    
    y_train = train_df['label']
    y_val = val_df['label']
    
    model = xgb.XGBClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_val_pred)
    print(f'{name} Features XGB Val Balanced Accuracy: {acc:.4f}')
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_val_pred)
    print(f'{name} Features RF Val Balanced Accuracy: {acc:.4f}')
