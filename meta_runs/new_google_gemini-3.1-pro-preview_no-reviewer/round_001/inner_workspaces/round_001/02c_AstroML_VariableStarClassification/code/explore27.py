import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. This is a huge gap.
# Let's rethink the problem. "Variable star classification"
# In AstroML, there is a dataset for variable star classification.
# It uses features like: amplitude, period, skew, kurtosis, etc.
# But we only have `symbol_series`.
# What if the `symbol_series` is a string representation of a light curve?
# Maybe the characters represent the magnitude at different phases.
# Let's try to extract features that are commonly used for light curves.

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def extract_light_curve_features(s):
    # Convert to numeric, ignoring . and *
    num_s = [char_map[c] for c in s if c in char_map]
    
    if len(num_s) == 0:
        return [0] * 15
        
    num_s = np.array(num_s)
    
    # Basic stats
    mean = np.mean(num_s)
    std = np.std(num_s)
    median = np.median(num_s)
    min_val = np.min(num_s)
    max_val = np.max(num_s)
    amplitude = (max_val - min_val) / 2
    
    # Percentiles
    p25 = np.percentile(num_s, 25)
    p75 = np.percentile(num_s, 75)
    iqr = p75 - p25
    
    # Skewness and kurtosis
    if std > 0:
        skew = np.mean(((num_s - mean) / std) ** 3)
        kurtosis = np.mean(((num_s - mean) / std) ** 4) - 3
    else:
        skew = 0
        kurtosis = 0
        
    # Median absolute deviation
    mad = np.median(np.abs(num_s - median))
    
    # Beyond 1 std
    beyond_1std = np.sum(np.abs(num_s - mean) > std) / len(num_s)
    
    # Slopes (differences)
    diffs = np.diff(num_s)
    mean_slope = np.mean(diffs) if len(diffs) > 0 else 0
    max_slope = np.max(np.abs(diffs)) if len(diffs) > 0 else 0
    
    return [mean, std, median, min_val, max_val, amplitude, p25, p75, iqr, skew, kurtosis, mad, beyond_1std, mean_slope, max_slope]

X_train = np.array([extract_light_curve_features(s) for s in train['symbol_series']])
X_val = np.array([extract_light_curve_features(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Light Curve Features RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
