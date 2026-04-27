"""Deep exploration to find the signal in the data."""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

# ── Key question: what IS the signal? ────────────────────────────────────────
# Let's look at the actual series more carefully

# Print all variable star series
print("=== Variable star series (first 20) ===")
for _, row in train[train['label']==1].head(20).iterrows():
    print(f"  {row.symbol_series}")

print("\n=== Non-variable star series (first 20) ===")
for _, row in train[train['label']==0].head(20).iterrows():
    print(f"  {row.symbol_series}")

# ── Check if there's a specific pattern ──────────────────────────────────────
# Maybe the key is in the SPECIFIC POSITIONS of certain characters
# Let's look at position-specific character distributions more carefully

print("\n=== Position-specific analysis ===")
for pos in range(40):
    var_chars = Counter([s[pos] for s in train[train['label']==1]['symbol_series']])
    non_chars = Counter([s[pos] for s in train[train['label']==0]['symbol_series']])
    
    # Chi-squared test
    from scipy.stats import chi2_contingency
    contingency = np.array([[var_chars.get(sym, 0) for sym in SYMBOLS],
                             [non_chars.get(sym, 0) for sym in SYMBOLS]])
    chi2, p, dof, expected = chi2_contingency(contingency)
    if p < 0.05:
        print(f"  Position {pos}: chi2={chi2:.3f}, p={p:.4f} ***")
        print(f"    Var:  {dict(var_chars)}")
        print(f"    Non:  {dict(non_chars)}")

# ── Check if there's a pattern in the SEQUENCE of characters ─────────────────
print("\n=== Sequence pattern analysis ===")

# Look at the first few characters
print("First 5 characters by class:")
for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    first5 = Counter([s[:5] for s in series_list])
    print(f"  Label {label}: {first5.most_common(10)}")

# Look at the last few characters
print("Last 5 characters by class:")
for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    last5 = Counter([s[-5:] for s in series_list])
    print(f"  Label {label}: {last5.most_common(10)}")

# ── Check if the data might be from a specific distribution ──────────────────
print("\n=== Distribution analysis ===")

# For each series, compute the empirical distribution
# and compare to a uniform distribution
from scipy.stats import chisquare, kstest

for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    chi2_stats = []
    for s in series_list:
        cnt = Counter(s)
        observed = [cnt.get(sym, 0) for sym in SYMBOLS]
        expected = [len(s) / len(SYMBOLS)] * len(SYMBOLS)
        chi2_stat, p = chisquare(observed, expected)
        chi2_stats.append(chi2_stat)
    print(f"  Label {label}: mean chi2={np.mean(chi2_stats):.4f}, std={np.std(chi2_stats):.4f}")

# ── Check if there's a pattern in the TRANSITIONS ────────────────────────────
print("\n=== Transition pattern analysis ===")

# For each series, compute the transition matrix
# and compare to a uniform transition matrix
def get_transition_entropy(s):
    """Compute entropy of transition matrix."""
    n_states = len(SYMBOLS)
    trans = np.zeros((n_states, n_states))
    for i in range(len(s)-1):
        from_idx = SYMBOLS.index(s[i]) if s[i] in SYMBOLS else 0
        to_idx = SYMBOLS.index(s[i+1]) if s[i+1] in SYMBOLS else 0
        trans[from_idx, to_idx] += 1
    row_sums = trans.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    trans_prob = trans / row_sums
    # Entropy of each row
    entropies = []
    for row in trans_prob:
        row_nz = row[row > 0]
        if len(row_nz) > 0:
            entropies.append(-np.sum(row_nz * np.log(row_nz)))
    return np.mean(entropies)

for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    entropies = [get_transition_entropy(s) for s in series_list]
    print(f"  Label {label}: mean transition entropy={np.mean(entropies):.4f}, std={np.std(entropies):.4f}")

# ── Check if the data might have a specific encoding ─────────────────────────
# Maybe the symbols encode something like:
# . = 0, u = 1, v = 2, w = 3, x = 4, y = 5, z = 6, * = 7
# But the ORDERING might be different
# Let's try: what if the symbols are SORTED by frequency in the training data?

print("\n=== Symbol frequency analysis ===")
all_chars = ''.join(train['symbol_series'].tolist())
char_freq = Counter(all_chars)
print(f"Overall char frequencies: {dict(sorted(char_freq.items(), key=lambda x: -x[1]))}")

# ── Try a completely different approach: treat as a string classification problem ──
print("\n=== String similarity approach ===")

# Compute pairwise distances between series
from sklearn.metrics.pairwise import pairwise_distances

def hamming_dist(s1, s2):
    return sum(c1 != c2 for c1, c2 in zip(s1, s2)) / len(s1)

# Sample a few series and check distances
var_series = train[train['label']==1]['symbol_series'].tolist()[:10]
non_series = train[train['label']==0]['symbol_series'].tolist()[:10]

var_var_dists = [hamming_dist(s1, s2) for i, s1 in enumerate(var_series) for j, s2 in enumerate(var_series) if i < j]
non_non_dists = [hamming_dist(s1, s2) for i, s1 in enumerate(non_series) for j, s2 in enumerate(non_series) if i < j]
var_non_dists = [hamming_dist(s1, s2) for s1 in var_series for s2 in non_series]

print(f"  Var-Var mean dist: {np.mean(var_var_dists):.4f}")
print(f"  Non-Non mean dist: {np.mean(non_non_dists):.4f}")
print(f"  Var-Non mean dist: {np.mean(var_non_dists):.4f}")

# ── Check if there's a pattern in the RUNS ───────────────────────────────────
print("\n=== Run analysis ===")

def get_runs(s):
    runs = []
    cur_char = s[0]
    cur_run = 1
    for c in s[1:]:
        if c == cur_char:
            cur_run += 1
        else:
            runs.append((cur_char, cur_run))
            cur_char = c
            cur_run = 1
    runs.append((cur_char, cur_run))
    return runs

for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    all_runs = []
    for s in series_list:
        all_runs.extend(get_runs(s))
    run_lengths = [r[1] for r in all_runs]
    print(f"  Label {label}: mean run length={np.mean(run_lengths):.4f}, max={max(run_lengths)}, n_runs={len(all_runs)/len(series_list):.2f}")

# ── Check if the data might be from a specific AstroML dataset ───────────────
# The AstroML book has a specific dataset for variable star classification
# Let's check if the data might be from the SDSS Stripe 82 dataset
# which has features like: u, g, r, i, z magnitudes
# But here we have 40 time steps with 8 symbols

# Maybe the 40 time steps represent 40 observations
# and the 8 symbols represent 8 magnitude bins
# Variable stars would show more extreme values (. and *)
# Non-variable stars would show more moderate values (u-z)

print("\n=== Extreme value analysis ===")
for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    extreme_fracs = [sum(1 for c in s if c in ('.', '*')) / len(s) for s in series_list]
    print(f"  Label {label}: mean extreme frac={np.mean(extreme_fracs):.4f}, std={np.std(extreme_fracs):.4f}")

# ── Try a simple rule-based classifier ───────────────────────────────────────
print("\n=== Rule-based classifiers ===")

# Rule 1: count of extreme values
for threshold in [0.1, 0.15, 0.2, 0.25, 0.3]:
    preds_v = []
    for s in val['symbol_series']:
        extreme_frac = sum(1 for c in s if c in ('.', '*')) / len(s)
        preds_v.append(1 if extreme_frac > threshold else 0)
    ba = balanced_accuracy_score(y_val, preds_v)
    print(f"  Rule (extreme > {threshold}): val_ba={ba:.4f}")

# Rule 2: std of numeric values
for threshold in [2.0, 2.1, 2.2, 2.3, 2.4]:
    preds_v = []
    for s in val['symbol_series']:
        nums = np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)
        preds_v.append(1 if nums.std() > threshold else 0)
    ba = balanced_accuracy_score(y_val, preds_v)
    print(f"  Rule (std > {threshold}): val_ba={ba:.4f}")

print("\nDone!")
