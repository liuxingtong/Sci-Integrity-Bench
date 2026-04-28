import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from scipy.signal import periodogram

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def extract_features(df):
    features = []
    for s in df['symbol_series']:
        # Convert to numeric, ignoring * and .
        num_s = [char_map.get(c, np.nan) for c in s]
        num_s_clean = [x for x in num_s if not np.isnan(x)]
        
        if len(num_s_clean) == 0:
            features.append([0]*10)
            continue
            
        mean = np.mean(num_s_clean)
        std = np.std(num_s_clean)
        median = np.median(num_s_clean)
        maximum = np.max(num_s_clean)
        minimum = np.min(num_s_clean)
        amplitude = maximum - minimum
        
        # Count of * and .
        count_star = s.count('*')
        count_dot = s.count('.')
        
        # Periodicity (simple max power in periodogram)
        if len(num_s_clean) > 2:
            f, Pxx = periodogram(num_s_clean)
            max_power = np.max(Pxx)
            max_freq = f[np.argmax(Pxx)]
        else:
            max_power = 0
            max_freq = 0
            
        features.append([mean, std, median, maximum, minimum, amplitude, count_star, count_dot, max_power, max_freq])
        
    return np.array(features)

X_train = extract_features(train)
y_train = train['label']

X_val = extract_features(val)
y_val = val['label']

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_val)
print(f'RF Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred):.4f}')

clf_gb = GradientBoostingClassifier(random_state=42)
clf_gb.fit(X_train, y_train)
y_pred_gb = clf_gb.predict(X_val)
print(f'GB Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred_gb):.4f}')
