import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '.': np.nan, '*': np.nan}

def extract_features(df):
    features = []
    for s in df['symbol_series']:
        # Convert to numeric
        num_s = [char_map.get(c, np.nan) for c in s]
        num_s = np.array(num_s, dtype=float)
        
        # Basic stats
        valid_s = num_s[~np.isnan(num_s)]
        if len(valid_s) > 0:
            mean = np.mean(valid_s)
            std = np.std(valid_s)
            median = np.median(valid_s)
            min_val = np.min(valid_s)
            max_val = np.max(valid_s)
            ptp = np.ptp(valid_s)
            q25 = np.percentile(valid_s, 25)
            q75 = np.percentile(valid_s, 75)
            iqr = q75 - q25
        else:
            mean = std = median = min_val = max_val = ptp = q25 = q75 = iqr = 0
            
        # Missing stats
        n_missing = np.isnan(num_s).sum()
        n_dot = s.count('.')
        n_star = s.count('*')
        
        # Transitions
        if len(valid_s) > 1:
            diffs = np.diff(valid_s)
            mean_diff = np.mean(np.abs(diffs))
            max_diff = np.max(np.abs(diffs))
            std_diff = np.std(diffs)
        else:
            mean_diff = max_diff = std_diff = 0
            
        features.append({
            'mean': mean, 'std': std, 'median': median, 'min': min_val, 'max': max_val,
            'ptp': ptp, 'q25': q25, 'q75': q75, 'iqr': iqr,
            'n_missing': n_missing, 'n_dot': n_dot, 'n_star': n_star,
            'mean_diff': mean_diff, 'max_diff': max_diff, 'std_diff': std_diff
        })
    return pd.DataFrame(features)

X_train = extract_features(train)
X_val = extract_features(val)
X_test = extract_features(test)

y_train = train['label']
y_val = val['label']
y_test = test['label']

model = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=10)
model.fit(X_train, y_train)

val_pred = model.predict(X_val)
print('Val Acc:', balanced_accuracy_score(y_val, val_pred))

test_pred = model.predict(X_test)
print('Test Acc:', balanced_accuracy_score(y_test, test_pred))

# Try XGBoost
xgb_model = xgb.XGBClassifier(n_estimators=200, random_state=42, max_depth=6, learning_rate=0.05)
xgb_model.fit(X_train, y_train)

val_pred_xgb = xgb_model.predict(X_val)
print('XGB Val Acc:', balanced_accuracy_score(y_val, val_pred_xgb))

test_pred_xgb = xgb_model.predict(X_test)
print('XGB Test Acc:', balanced_accuracy_score(y_test, test_pred_xgb))
