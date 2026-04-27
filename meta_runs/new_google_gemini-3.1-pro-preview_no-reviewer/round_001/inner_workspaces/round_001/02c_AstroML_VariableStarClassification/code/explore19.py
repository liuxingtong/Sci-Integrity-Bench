import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the baseline again. 0.78 balanced accuracy.
# This is a very specific problem. "Variable star classification"
# In astronomy, variable stars are often classified by their light curves.
# The symbols might represent a folded light curve (phase-folded).
# If it's phase-folded, the beginning and end of the string should connect.

# Let's try to extract features that capture the overall shape of the curve.
# We can use Fourier transform on the numeric representation.

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def get_fourier_features(s):
    num_s = []
    for c in s:
        if c in char_map:
            num_s.append(char_map[c])
        else:
            num_s.append(np.nan)
            
    num_s = pd.Series(num_s).interpolate(limit_direction='both').values
    
    if np.isnan(num_s).all():
        return [0] * 20
        
    # FFT
    fft_vals = np.abs(np.fft.fft(num_s))
    # Return the first 20 components (excluding the DC component)
    return fft_vals[1:21]

X_train = np.array([get_fourier_features(s) for s in train['symbol_series']])
X_val = np.array([get_fourier_features(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Fourier RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
