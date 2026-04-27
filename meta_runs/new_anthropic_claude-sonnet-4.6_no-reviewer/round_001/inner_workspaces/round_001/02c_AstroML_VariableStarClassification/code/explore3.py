import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def to_nums(s):
    return np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)

# Compute autocorrelation for each series
def autocorr_at_lag(s, lag):
    nums = to_nums(s)
    if len(nums) <= lag:
        return 0
    corr = np.corrcoef(nums[:-lag], nums[lag:])[0,1]
    return corr if not np.isnan(corr) else 0

print('Autocorrelation by lag and class:')
for lag in [1, 2, 3, 4, 5, 10, 20]:
    var_ac = [autocorr_at_lag(s, lag) for s in train[train['label']==1]['symbol_series']]
    non_ac = [autocorr_at_lag(s, lag) for s in train[train['label']==0]['symbol_series']]
    print(f'  Lag {lag}: var_mean={np.mean(var_ac):.4f}, non_mean={np.mean(non_ac):.4f}, diff={np.mean(var_ac)-np.mean(non_ac):.4f}')

# Check if the series might encode a specific type of variability
# Variable stars often show periodic behavior
# Let's check for periodicity using FFT
print('\nFFT power spectrum analysis:')
for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    all_powers = []
    for s in series_list:
        nums = to_nums(s)
        fft = np.fft.rfft(nums - nums.mean())
        power = np.abs(fft)**2
        all_powers.append(power)
    mean_power = np.mean(all_powers, axis=0)
    print(f'  Label {label}: top freq powers = {mean_power[1:6].round(3)}')

# Check if there's a specific pattern in the data generation
# Maybe the symbols encode something like: . = missing, u-z = brightness levels, * = outlier
print('\nChecking if * (asterisk) is special:')
for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    star_counts = [s.count('*') for s in series_list]
    dot_counts = [s.count('.') for s in series_list]
    print(f'  Label {label}: mean_stars={np.mean(star_counts):.3f}, mean_dots={np.mean(dot_counts):.3f}')

# Check if the data might be from a specific AstroML dataset
# The symbols might be from a specific encoding
print('\nChecking symbol ordering hypothesis:')
# Maybe the order is: . < u < v < w < x < y < z < * (brightness)
# Or maybe: * = missing/bad, . = faint, u-z = brightness levels
# Let's check if treating * as 0 (missing) changes things
SYM2IDX_ALT = {'.': 0, 'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '*': 7}
SYM2IDX_ALT2 = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
SYM2IDX_ALT3 = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

for name, mapping in [('original', SYM2IDX), ('alt1', SYM2IDX_ALT), ('alt2', SYM2IDX_ALT2), ('alt3', SYM2IDX_ALT3)]:
    var_stds = [np.std([mapping.get(c, 0) for c in s]) for s in train[train['label']==1]['symbol_series']]
    non_stds = [np.std([mapping.get(c, 0) for c in s]) for s in train[train['label']==0]['symbol_series']]
    print(f'  {name}: var_std={np.mean(var_stds):.4f}, non_std={np.mean(non_stds):.4f}, diff={np.mean(var_stds)-np.mean(non_stds):.4f}')

# Check if the data has any structure at all - try permutation test
print('\nPermutation test (shuffling labels):')
from sklearn.metrics import balanced_accuracy_score
from sklearn.ensemble import RandomForestClassifier

def pos_features(df, mapping=SYM2IDX):
    return np.array([[mapping.get(c, 0) for c in s] for s in df['symbol_series']])

X_tr = pos_features(train)
X_v = pos_features(val)
y_tr = train['label'].values
y_v = val['label'].values

# Real performance
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_tr, y_tr)
yp = clf.predict(X_v)
print(f'  Real val_ba: {balanced_accuracy_score(y_v, yp):.4f}')

# Permuted performance
perms = []
for seed in range(20):
    rng = np.random.RandomState(seed)
    y_perm = rng.permutation(y_tr)
    clf2 = RandomForestClassifier(n_estimators=100, random_state=42)
    clf2.fit(X_tr, y_perm)
    yp2 = clf2.predict(X_v)
    perms.append(balanced_accuracy_score(y_v, yp2))
print(f'  Permuted val_ba: mean={np.mean(perms):.4f}, std={np.std(perms):.4f}')
print(f'  p-value approx: {np.mean(np.array(perms) >= balanced_accuracy_score(y_v, yp)):.3f}')

# Check if there's any signal in the data at all
print('\nChecking for any signal - correlation between features and label:')
X_all = pos_features(train)
for pos in range(40):
    corr = np.corrcoef(X_all[:, pos], y_tr)[0, 1]
    if abs(corr) > 0.1:
        print(f'  Position {pos}: corr={corr:.4f}')

print('\nMax correlation across all positions:')
corrs = [abs(np.corrcoef(X_all[:, pos], y_tr)[0, 1]) for pos in range(40)]
print(f'  Max: {max(corrs):.4f} at pos {np.argmax(corrs)}')
print(f'  Mean: {np.mean(corrs):.4f}')
