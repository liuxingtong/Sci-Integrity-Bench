import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from scipy.fft import fft

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

# Try mapping characters to integers
# Assuming SAX-like encoding, let's try a few orderings
char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def extract_ts_features(df):
    features = []
    for s in df['symbol_series']:
        seq = np.array([char_map[c] for c in s], dtype=float)
        
        # Basic stats
        mean = np.mean(seq)
        std = np.std(seq)
        
        # Autocorrelation
        autocorr = [pd.Series(seq).autocorr(lag=i) for i in range(1, 10)]
        autocorr = [0 if np.isnan(x) else x for x in autocorr]
        
        # FFT
        fft_vals = np.abs(fft(seq))[1:20] # Ignore DC component, take first half
        
        row = [mean, std] + autocorr + list(fft_vals)
        features.append(row)
    return np.array(features)

X_train = extract_ts_features(train_df)
X_val = extract_ts_features(val_df)

y_train = train_df['label']
y_val = val_df['label']

model = GradientBoostingClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'TS Features (Autocorr + FFT) Val Balanced Accuracy: {acc:.4f}')
