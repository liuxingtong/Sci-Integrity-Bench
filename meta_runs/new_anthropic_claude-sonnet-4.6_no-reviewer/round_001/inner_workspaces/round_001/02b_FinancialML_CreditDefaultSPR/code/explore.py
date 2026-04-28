import pandas as pd
import numpy as np
from collections import Counter
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

# Combine train+val for exploration
all_data = pd.concat([train, val, test], ignore_index=True)

CHARS = ['1', '2', 'A', 'B', 'C', 'D']
SEQ_LEN = 20

# Check if any single character position is predictive
print('=== Positional character predictiveness (train) ===')
for pos in range(SEQ_LEN):
    for c in CHARS:
        col = [1 if s[pos] == c else 0 for s in train['sym_seq']]
        if sum(col) > 5:
            corr = np.corrcoef(col, train['default_flag'])[0,1]
            if abs(corr) > 0.1:
                print(f'  pos={pos}, char={c}, corr={corr:.3f}, count={sum(col)}')

# Check character counts
print('\n=== Character count correlations with default ===')
for c in CHARS:
    cnt = [s.count(c) for s in train['sym_seq']]
    corr = np.corrcoef(cnt, train['default_flag'])[0,1]
    print(f'  char={c}, corr={corr:.4f}')

# Check if sequences are truly random or have structure
print('\n=== Are sequences random? ===')
print('Expected freq per char if uniform: 1/6 =', 1/6)
all_chars = ''.join(train['sym_seq'].tolist())
cnt = Counter(all_chars)
total = len(all_chars)
for c in CHARS:
    print(f'  {c}: {cnt[c]/total:.4f}')

# Check if default_flag correlates with any simple feature
print('\n=== Simple feature correlations ===')
for c in CHARS:
    freq = [s.count(c)/SEQ_LEN for s in train['sym_seq']]
    corr = np.corrcoef(freq, train['default_flag'])[0,1]
    print(f'  freq_{c}: corr={corr:.4f}')

# Check transitions
trans = [sum(1 for i in range(len(s)-1) if s[i] != s[i+1]) for s in train['sym_seq']]
corr = np.corrcoef(trans, train['default_flag'])[0,1]
print(f'  transitions: corr={corr:.4f}')

# Check if there are duplicate sequences
print('\n=== Duplicate sequences ===')
all_seqs = pd.concat([train, val, test])
print(f'Total sequences: {len(all_seqs)}')
print(f'Unique sequences: {all_seqs["sym_seq"].nunique()}')

# Check if same sequence appears with different labels
dup = all_seqs.groupby('sym_seq')['default_flag'].agg(['mean', 'count'])
print(f'Sequences appearing >1 time: {(dup["count"] > 1).sum()}')

# Try combining train+val for training
print('\n=== Try train+val combined ===')
train_full = pd.concat([train, val], ignore_index=True)

def extract_features_v2(df):
    seqs = df['sym_seq'].tolist()
    feats = {}
    # Positional one-hot
    for pos in range(SEQ_LEN):
        for c in CHARS:
            feats[f'pos{pos}_{c}'] = [1 if s[pos] == c else 0 for s in seqs]
    # Character counts
    for c in CHARS:
        feats[f'cnt_{c}'] = [s.count(c) for s in seqs]
    # Bigrams
    bigrams = [f'{a}{b}' for a in CHARS for b in CHARS]
    for bg in bigrams:
        feats[f'bg_{bg}'] = [sum(1 for i in range(len(s)-1) if s[i:i+2] == bg) for s in seqs]
    return pd.DataFrame(feats)

X_tr = extract_features_v2(train_full)
X_te = extract_features_v2(test)
y_tr = train_full['default_flag'].values
y_te = test['default_flag'].values

for name, model in [
    ('LR', LogisticRegression(max_iter=2000, C=0.01, random_state=42)),
    ('LR C=0.1', LogisticRegression(max_iter=2000, C=0.1, random_state=42)),
    ('LR C=1', LogisticRegression(max_iter=2000, C=1.0, random_state=42)),
    ('RF 100', RandomForestClassifier(n_estimators=100, random_state=42)),
    ('RF 500', RandomForestClassifier(n_estimators=500, random_state=42)),
    ('GB', GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=3, random_state=42)),
]:
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, proba)
    print(f'  {name:15s}: Test AUC={auc:.4f}')

# Check if the data might have a time/sequence ordering signal
print('\n=== Check ID ordering ===')
print('Train IDs range:', train['id'].min(), '-', train['id'].max())
print('Val IDs range:', val['id'].min(), '-', val['id'].max())
print('Test IDs range:', test['id'].min(), '-', test['id'].max())

# Check if ID correlates with default
corr_id = np.corrcoef(train['id'], train['default_flag'])[0,1]
print(f'ID vs default_flag corr (train): {corr_id:.4f}')
