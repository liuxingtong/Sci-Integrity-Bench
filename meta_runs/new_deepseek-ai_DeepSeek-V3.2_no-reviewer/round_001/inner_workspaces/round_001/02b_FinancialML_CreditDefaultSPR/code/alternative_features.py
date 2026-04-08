import pandas as pd
import numpy as np
from collections import Counter
import math

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

symbols = ['1', '2', 'A', 'B', 'C', 'D']

# Alternative feature extraction
def extract_alternative_features(df):
    features = pd.DataFrame(index=df.index)
    sequences = df['sym_seq']
    
    # 1. Symbol frequencies (already done)
    for sym in symbols:
        features[f'freq_{sym}'] = sequences.apply(lambda x: x.count(sym))
    
    # 2. Position-weighted features (early vs late occurrences)
    seq_length = 20
    for sym in symbols:
        # Average position of symbol
        def avg_position(seq):
            positions = [i for i, c in enumerate(seq) if c == sym]
            return np.mean(positions) if positions else -1
        features[f'avg_pos_{sym}'] = sequences.apply(avg_position)
        
        # Position of first occurrence
        features[f'first_pos_{sym}'] = sequences.apply(lambda x: x.find(sym))
        
        # Position of last occurrence
        features[f'last_pos_{sym}'] = sequences.apply(lambda x: x.rfind(sym))
    
    # 3. Pattern-based features
    # Count of specific patterns that might be meaningful
    patterns = ['11', '22', 'AA', 'BB', 'CC', 'DD', '12', '21', 'AB', 'BA', 'CD', 'DC']
    for pattern in patterns:
        features[f'pattern_{pattern}'] = sequences.apply(lambda x: x.count(pattern))
    
    # 4. Alternation patterns (changes between digit/letter)
    def count_alternations(seq):
        digits = set(['1', '2'])
        letters = set(['A', 'B', 'C', 'D'])
        alternations = 0
        for i in range(1, len(seq)):
            prev_digit = seq[i-1] in digits
            curr_digit = seq[i] in digits
            if prev_digit != curr_digit:
                alternations += 1
        return alternations
    
    features['alternations'] = sequences.apply(count_alternations)
    
    # 5. Run length statistics
    def run_length_stats(seq):
        runs = []
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
            else:
                runs.append(current_run)
                current_run = 1
        runs.append(current_run)
        return pd.Series({
            'mean_run': np.mean(runs),
            'max_run': np.max(runs),
            'min_run': np.min(runs),
            'std_run': np.std(runs)
        })
    
    run_stats = sequences.apply(run_length_stats)
    features = pd.concat([features, run_stats], axis=1)
    
    # 6. Symbol transitions (Markov-like features)
    # Probability of transitioning from one symbol type to another
    def transition_matrix_features(seq):
        digits = set(['1', '2'])
        letters = set(['A', 'B', 'C', 'D'])
        
        dd = dl = ld = ll = 0
        for i in range(1, len(seq)):
            prev_is_digit = seq[i-1] in digits
            curr_is_digit = seq[i] in digits
            
            if prev_is_digit and curr_is_digit:
                dd += 1
            elif prev_is_digit and not curr_is_digit:
                dl += 1
            elif not prev_is_digit and curr_is_digit:
                ld += 1
            else:
                ll += 1
        
        total = len(seq) - 1
        return pd.Series({
            'p_dd': dd/total if total > 0 else 0,
            'p_dl': dl/total if total > 0 else 0,
            'p_ld': ld/total if total > 0 else 0,
            'p_ll': ll/total if total > 0 else 0
        })
    
    trans_features = sequences.apply(transition_matrix_features)
    features = pd.concat([features, trans_features], axis=1)
    
    # 7. Symbol balance features
    features['digit_minus_letter'] = features['freq_1'] + features['freq_2'] - \
                                     (features['freq_A'] + features['freq_B'] + \
                                      features['freq_C'] + features['freq_D'])
    
    # 8. Sequence complexity (Lempel-Ziv approximation)
    def lempel_ziv_complexity(seq):
        i, k, l = 0, 1, 1
        k_max = 1
        n = len(seq)
        
        while True:
            if seq[i + k - 1] == seq[l + k - 1]:
                k += 1
                if l + k > n:
                    return k_max
            else:
                if k > k_max:
                    k_max = k
                i += 1
                if i == l:
                    l += k_max
                    if l + 1 > n:
                        return k_max
                    i = 0
                    k = 1
                    k_max = 1
                else:
                    k = 1
    
    features['lz_complexity'] = sequences.apply(lempel_ziv_complexity)
    
    return features

# Extract features
print("Extracting alternative features...")
train_features_alt = extract_alternative_features(train)
val_features_alt = extract_alternative_features(val)
test_features_alt = extract_alternative_features(test)

print(f"Train features shape: {train_features_alt.shape}")
print(f"Number of features: {train_features_alt.shape[1]}")

# Save features
train_features_alt.to_csv('../outputs/train_features_alt.csv', index=False)
val_features_alt.to_csv('../outputs/val_features_alt.csv', index=False)
test_features_alt.to_csv('../outputs/test_features_alt.csv', index=False)

print("\nFirst few features:")
print(train_features_alt.head())

print("\nFeature names:")
print(list(train_features_alt.columns))