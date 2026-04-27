import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Let's try to extract features based on the "shape" of the series
# The characters u, v, w, x, y, z might represent magnitudes or fluxes
# . and * might represent missing data or outliers

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def extract_advanced_features(df):
    features = []
    for s in df['symbol_series']:
        # Convert to numeric, ignoring . and *
        num_s = [char_map[c] for c in s if c in char_map]
        
        if len(num_s) == 0:
            features.append({k: 0 for k in ['mean', 'std', 'skew', 'kurtosis', 'amplitude', 'periodicity']})
            continue
            
        num_s = np.array(num_s)
        
        # Basic stats
        mean = np.mean(num_s)
        std = np.std(num_s)
        amplitude = (np.max(num_s) - np.min(num_s)) / 2
        
        # Skewness and kurtosis (approximate)
        if std > 0:
            skew = np.mean(((num_s - mean) / std) ** 3)
            kurtosis = np.mean(((num_s - mean) / std) ** 4) - 3
        else:
            skew = 0
            kurtosis = 0
            
        # Periodicity (autocorrelation at lag 1, 2, 3)
        autocorr_1 = np.corrcoef(num_s[:-1], num_s[1:])[0, 1] if len(num_s) > 1 and np.std(num_s[:-1]) > 0 and np.std(num_s[1:]) > 0 else 0
        autocorr_2 = np.corrcoef(num_s[:-2], num_s[2:])[0, 1] if len(num_s) > 2 and np.std(num_s[:-2]) > 0 and np.std(num_s[2:]) > 0 else 0
        autocorr_3 = np.corrcoef(num_s[:-3], num_s[3:])[0, 1] if len(num_s) > 3 and np.std(num_s[:-3]) > 0 and np.std(num_s[3:]) > 0 else 0
        
        # Number of peaks
        peaks = np.sum((num_s[1:-1] > num_s[:-2]) & (num_s[1:-1] > num_s[2:]))
        
        # Missing data patterns
        n_dots = s.count('.')
        n_stars = s.count('*')
        
        features.append({
            'mean': mean, 'std': std, 'skew': skew, 'kurtosis': kurtosis,
            'amplitude': amplitude, 'autocorr_1': autocorr_1, 'autocorr_2': autocorr_2,
            'autocorr_3': autocorr_3, 'peaks': peaks, 'n_dots': n_dots, 'n_stars': n_stars
        })
        
    return pd.DataFrame(features)

X_train = extract_advanced_features(train)
X_val = extract_advanced_features(val)
X_test = extract_advanced_features(test)

y_train = train['label']
y_val = val['label']
y_test = test['label']

model = xgb.XGBClassifier(n_estimators=200, random_state=42, max_depth=6, learning_rate=0.05)
model.fit(X_train, y_train)

val_pred = model.predict(X_val)
print('Val Acc:', balanced_accuracy_score(y_val, val_pred))

test_pred = model.predict(X_test)
print('Test Acc:', balanced_accuracy_score(y_test, test_pred))
