import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def get_period_features(df):
    features = []
    for s in df['symbol_series']:
        num_s = np.array([char_map[c] for c in s])
        
        # Try different periods
        best_var = float('inf')
        best_p = 1
        
        vars_p = []
        for p in range(2, 20):
            # Fold the light curve
            folded = [[] for _ in range(p)]
            for i, val in enumerate(num_s):
                folded[i % p].append(val)
            
            # Calculate variance of the folded light curve
            # A good period will have low variance in each bin
            var = np.mean([np.var(bin) if len(bin) > 1 else 0 for bin in folded])
            vars_p.append(var)
            
            if var < best_var:
                best_var = var
                best_p = p
                
        features.append([best_p, best_var] + vars_p)
    return np.array(features)

X_train = get_period_features(train)
X_val = get_period_features(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Period RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')
