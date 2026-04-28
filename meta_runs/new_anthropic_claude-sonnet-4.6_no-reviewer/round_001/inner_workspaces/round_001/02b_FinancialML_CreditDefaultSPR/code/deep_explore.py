import pandas as pd
import numpy as np
from collections import Counter
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

CHARS = ['1', '2', 'A', 'B', 'C', 'D']
SEQ_LEN = 20

# Map characters to numbers and look for numeric patterns
char_map = {'1': 1, '2': 2, 'A': 3, 'B': 4, 'C': 5, 'D': 6}

def seq_to_nums(s):
    return [char_map[c] for c in s]

# Check if numeric encoding reveals patterns
print('=== Numeric encoding statistics by class ===')
for label in [0, 1]:
    subset = train[train['default_flag'] == label]['sym_seq']
    nums = [seq_to_nums(s) for s in subset]
    arr = np.array(nums)
    print(f'\nClass {label} (n={len(subset)}):')
    print(f'  Mean per position: {arr.mean(axis=0).round(2)}')
    print(f'  Std per position:  {arr.std(axis=0).round(2)}')

# Check if sum/mean of numeric encoding is predictive
print('\n=== Numeric sum/mean correlations ===')
for label_name, func in [('sum', sum), ('mean', np.mean), ('std', np.std), ('max', max), ('min', min)]:
    vals = [func(seq_to_nums(s)) for s in train['sym_seq']]
    corr = np.corrcoef(vals, train['default_flag'])[0,1]
    print(f'  {label_name}: corr={corr:.4f}')

# Check if there's a specific subsequence that's highly predictive
print('\n=== Most predictive subsequences (length 2-4) ===')
all_seqs = train['sym_seq'].tolist()
labels = train['default_flag'].values

best_subseqs = []
for length in [2, 3, 4]:
    subseq_stats = {}
    for s, label in zip(all_seqs, labels):
        for i in range(len(s) - length + 1):
            sub = s[i:i+length]
            if sub not in subseq_stats:
                subseq_stats[sub] = [0, 0]
            subseq_stats[sub][label] += 1
    
    for sub, counts in subseq_stats.items():
        total = counts[0] + counts[1]
        if total >= 10:
            rate = counts[1] / total
            overall_rate = labels.mean()
            lift = rate / overall_rate if overall_rate > 0 else 0
            best_subseqs.append((sub, total, rate, lift))

best_subseqs.sort(key=lambda x: abs(x[3] - 1), reverse=True)
print('Top 20 most predictive subsequences:')
for sub, total, rate, lift in best_subseqs[:20]:
    print(f'  {sub}: n={total}, default_rate={rate:.3f}, lift={lift:.3f}')

# Check if the sequences encode something specific
# Try treating chars as categorical and using label encoding
print('\n=== Label encoding approach ===')
char_to_int = {c: i for i, c in enumerate(CHARS)}

def seq_to_label_enc(s):
    return [char_to_int[c] for c in s]

X_train_le = np.array([seq_to_label_enc(s) for s in train['sym_seq']])
X_val_le   = np.array([seq_to_label_enc(s) for s in val['sym_seq']])
X_test_le  = np.array([seq_to_label_enc(s) for s in test['sym_seq']])

y_train = train['default_flag'].values
y_val   = val['default_flag'].values
y_test  = test['default_flag'].values

for C in [0.001, 0.01, 0.1, 1.0, 10.0]:
    model = LogisticRegression(max_iter=2000, C=C, random_state=42)
    model.fit(X_train_le, y_train)
    val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_le)[:, 1])
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test_le)[:, 1])
    print(f'  LR C={C}: Val AUC={val_auc:.4f}  Test AUC={test_auc:.4f}')

# Try treating as ordinal: 1<2<A<B<C<D
print('\n=== Ordinal encoding ===')
ordinal_map = {'1': 0, '2': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5}
X_train_ord = np.array([[ordinal_map[c] for c in s] for s in train['sym_seq']])
X_val_ord   = np.array([[ordinal_map[c] for c in s] for s in val['sym_seq']])
X_test_ord  = np.array([[ordinal_map[c] for c in s] for s in test['sym_seq']])

for C in [0.01, 0.1, 1.0]:
    model = LogisticRegression(max_iter=2000, C=C, random_state=42)
    model.fit(X_train_ord, y_train)
    val_auc  = roc_auc_score(y_val,  model.predict_proba(X_val_ord)[:, 1])
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test_ord)[:, 1])
    print(f'  LR C={C}: Val AUC={val_auc:.4f}  Test AUC={test_auc:.4f}')

# Check if there's a pattern in specific positions
print('\n=== Per-position AUC (single feature) ===')
for pos in range(SEQ_LEN):
    for c in CHARS:
        feat = np.array([1 if s[pos] == c else 0 for s in train['sym_seq']])
        if feat.sum() > 5:
            auc = roc_auc_score(y_train, feat)
            if abs(auc - 0.5) > 0.05:
                print(f'  pos={pos}, char={c}: AUC={auc:.4f}')

# Check if there's a pattern in the data generation
print('\n=== Data generation check ===')
print('First 20 sequences and labels:')
for i in range(20):
    print(f'  {train["sym_seq"].iloc[i]}  label={train["default_flag"].iloc[i]}')

# Check if sequences with specific patterns have different default rates
print('\n=== Sequences starting with specific chars ===')
for c in CHARS:
    subset = train[train['sym_seq'].str[0] == c]
    print(f'  Starts with {c}: n={len(subset)}, default_rate={subset["default_flag"].mean():.3f}')

print('\n=== Sequences ending with specific chars ===')
for c in CHARS:
    subset = train[train['sym_seq'].str[-1] == c]
    print(f'  Ends with {c}: n={len(subset)}, default_rate={subset["default_flag"].mean():.3f}')

# Check if count of '2' is predictive (had highest corr)
print('\n=== Count of 2 vs default ===')
for cnt in range(0, 8):
    subset = train[train['sym_seq'].str.count('2') == cnt]
    if len(subset) > 0:
        print(f'  count_2={cnt}: n={len(subset)}, default_rate={subset["default_flag"].mean():.3f}')
