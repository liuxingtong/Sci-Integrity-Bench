import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = sorted(list(set(''.join(train['symbol_series']))))
char_to_idx = {c: i for i, c in enumerate(chars)}

# Let's try to extract features based on the length of consecutive identical characters
def extract_run_lengths(s):
    runs = []
    current_char = s[0]
    current_len = 1
    for c in s[1:]:
        if c == current_char:
            current_len += 1
        else:
            runs.append((current_char, current_len))
            current_char = c
            current_len = 1
    runs.append((current_char, current_len))
    return runs

def extract_features(df):
    features = []
    for s in df['symbol_series']:
        row_features = []
        
        # 1. Character counts
        for c in chars:
            row_features.append(s.count(c))
            
        # 2. Transition counts (not normalized)
        mat = np.zeros((len(chars), len(chars)))
        for i in range(len(s) - 1):
            c1 = s[i]
            c2 = s[i+1]
            mat[char_to_idx[c1], char_to_idx[c2]] += 1
        row_features.extend(mat.flatten())
        
        # 3. Run lengths
        runs = extract_run_lengths(s)
        run_lengths = [r[1] for r in runs]
        row_features.extend([
            np.mean(run_lengths),
            np.max(run_lengths),
            np.std(run_lengths),
            len(runs) # Number of runs
        ])
        
        # 4. Specific character run lengths
        for c in chars:
            c_runs = [r[1] for r in runs if r[0] == c]
            if c_runs:
                row_features.extend([np.mean(c_runs), np.max(c_runs)])
            else:
                row_features.extend([0, 0])
                
        features.append(row_features)
    return np.array(features)

X_train = extract_features(train)
y_train = train['label']

X_val = extract_features(val)
y_val = val['label']

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)

clf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_val)
print(f'RF Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred):.4f}')

clf_lr = LogisticRegression(max_iter=1000, random_state=42, C=0.1)
clf_lr.fit(X_train_scaled, y_train)
y_pred_lr = clf_lr.predict(X_val_scaled)
print(f'LR Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred_lr):.4f}')

clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=3, learning_rate=0.1, n_estimators=100)
clf_xgb.fit(X_train, y_train)
y_pred_xgb = clf_xgb.predict(X_val)
print(f'XGB Val Balanced Acc: {balanced_accuracy_score(y_val, y_pred_xgb):.4f}')
