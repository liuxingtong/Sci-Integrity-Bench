import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the problem from a different angle.
# Variable stars have periodic variations in brightness.
# The symbols u, v, w, x, y, z might represent brightness levels.
# Let's try to find periods.

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def get_period_features(s):
    # Convert to numeric, interpolate missing values (. and *)
    num_s = []
    for c in s:
        if c in char_map:
            num_s.append(char_map[c])
        else:
            num_s.append(np.nan)
            
    num_s = pd.Series(num_s).interpolate(limit_direction='both').values
    
    if np.isnan(num_s).all():
        return [0] * 20
        
    # Calculate autocorrelation for lags 1 to 20
    autocorrs = []
    for lag in range(1, 21):
        if len(num_s) > lag:
            corr = np.corrcoef(num_s[:-lag], num_s[lag:])[0, 1]
            if np.isnan(corr):
                corr = 0
            autocorrs.append(corr)
        else:
            autocorrs.append(0)
            
    return autocorrs

X_train = np.array([get_period_features(s) for s in train['symbol_series']])
X_val = np.array([get_period_features(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Autocorr RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
