import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import itertools
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

class AdvancedSymbolicFeatureExtractor:
    """Extract advanced features from symbolic time series for variable star classification"""
    
    def __init__(self, symbols=None):
        if symbols is None:
            self.symbols = ['w', '.', '*', 'x', 'z', 'v', 'y', 'u']
        else:
            self.symbols = symbols
        
        self.symbol_to_idx = {s: i for i, s in enumerate(self.symbols)}
        self.n_symbols = len(self.symbols)
        
    def extract_features(self, symbol_series):
        """Extract all advanced features"""
        features = {}
        
        # 1. Basic statistical features
        features.update(self._extract_statistical_features(symbol_series))
        
        # 2. Transition matrix features
        features.update(self._extract_transition_matrix_features(symbol_series))
        
        # 3. Recurrence features
        features.update(self._extract_recurrence_features(symbol_series))
        
        # 4. Pattern and motif features
        features.update(self._extract_pattern_features(symbol_series))
        
        # 5. Entropy and complexity features
        features.update(self._extract_complexity_features(symbol_series))
        
        # 6. Symbolic dynamics features
        features.update(self._extract_symbolic_dynamics_features(symbol_series))
        
        return features
    
    def _extract_statistical_features(self, series):
        """Basic statistical features"""
        features = {}
        
        # Convert symbols to numerical values for statistical analysis
        numeric_series = [self.symbol_to_idx[s] for s in series]
        
        # Basic statistics
        features['mean_symbol'] = np.mean(numeric_series)
        features['std_symbol'] = np.std(numeric_series)
        features['var_symbol'] = np.var(numeric_series)
        features['min_symbol'] = np.min(numeric_series)
        features['max_symbol'] = np.max(numeric_series)
        features['range_symbol'] = features['max_symbol'] - features['min_symbol']
        
        # Percentiles
        for p in [25, 50, 75]:
            features[f'percentile_{p}'] = np.percentile(numeric_series, p)
        
        # Skewness and kurtosis
        features['skewness'] = stats.skew(numeric_series)
        features['kurtosis'] = stats.kurtosis(numeric_series)
        
        # Autocorrelation at lag 1
        if len(numeric_series) > 1:
            autocorr = np.corrcoef(numeric_series[:-1], numeric_series[1:])[0, 1]
            features['autocorr_lag1'] = autocorr if not np.isnan(autocorr) else 0
        else:
            features['autocorr_lag1'] = 0
        
        return features
    
    def _extract_transition_matrix_features(self, series):
        """Features from transition probability matrix"""
        features = {}
        
        # Build transition matrix
        trans_matrix = np.zeros((self.n_symbols, self.n_symbols))
        
        for i in range(len(series) - 1):
            from_idx = self.symbol_to_idx[series[i]]
            to_idx = self.symbol_to_idx[series[i+1]]
            trans_matrix[from_idx, to_idx] += 1
        
        # Normalize rows to get probabilities
        row_sums = trans_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        trans_probs = trans_matrix / row_sums
        
        # Extract features from transition matrix
        features['trans_entropy'] = self._matrix_entropy(trans_probs)
        features['trans_symmetry'] = self._matrix_symmetry(trans_probs)
        
        # Self-transition probability
        self_trans = np.trace(trans_matrix) / (len(series) - 1) if len(series) > 1 else 0
        features['self_transition_prob'] = self_trans
        
        # Most probable transition
        if trans_matrix.sum() > 0:
            max_idx = np.unravel_index(np.argmax(trans_matrix), trans_matrix.shape)
            features['max_trans_from'] = max_idx[0]
            features['max_trans_to'] = max_idx[1]
            features['max_trans_prob'] = trans_matrix[max_idx] / trans_matrix.sum()
        else:
            features['max_trans_from'] = 0
            features['max_trans_to'] = 0
            features['max_trans_prob'] = 0
        
        return features
    
    def _matrix_entropy(self, matrix):
        """Calculate entropy of a probability matrix"""
        entropy = 0
        flat_matrix = matrix.flatten()
        for p in flat_matrix:
            if p > 0:
                entropy -= p * np.log2(p)
        return entropy
    
    def _matrix_symmetry(self, matrix):
        """Measure symmetry of transition matrix"""
        if matrix.shape[0] != matrix.shape[1]:
            return 0
        diff = matrix - matrix.T
        symmetry = 1.0 / (1.0 + np.abs(diff).sum())
        return symmetry
    
    def _extract_recurrence_features(self, series):
        """Recurrence quantification features"""
        features = {}
        
        # Build recurrence matrix (simplified)
        n = len(series)
        recurrence = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if series[i] == series[j]:
                    recurrence[i, j] = 1
        
        # Recurrence rate
        features['recurrence_rate'] = recurrence.sum() / (n * n) if n > 0 else 0
        
        # Diagonal line features (simplified)
        diag_lines = []
        current_line = 0
        
        # Check main diagonal
        for i in range(n):
            if recurrence[i, i] == 1:
                current_line += 1
            else:
                if current_line > 1:  # Only count lines of length > 1
                    diag_lines.append(current_line)
                current_line = 0
        
        if current_line > 1:
            diag_lines.append(current_line)
        
        if diag_lines:
            features['avg_diag_line'] = np.mean(diag_lines)
            features['max_diag_line'] = np.max(diag_lines)
            features['diag_entropy'] = stats.entropy(diag_lines) if len(diag_lines) > 1 else 0
        else:
            features['avg_diag_line'] = 0
            features['max_diag_line'] = 0
            features['diag_entropy'] = 0
        
        return features
    
    def _extract_pattern_features(self, series):
        """Pattern and motif discovery features"""
        features = {}
        
        # Find repeated patterns of length 2-4
        for pattern_len in [2, 3, 4]:
            pattern_counts = {}
            for i in range(len(series) - pattern_len + 1):
                pattern = series[i:i+pattern_len]
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Most frequent pattern
            if pattern_counts:
                most_common = max(pattern_counts.items(), key=lambda x: x[1])
                features[f'most_common_pattern_{pattern_len}'] = self._pattern_to_number(most_common[0])
                features[f'most_common_pattern_freq_{pattern_len}'] = most_common[1] / (len(series) - pattern_len + 1)
                
                # Pattern diversity
                features[f'pattern_diversity_{pattern_len}'] = len(pattern_counts) / (self.n_symbols ** pattern_len)
            else:
                features[f'most_common_pattern_{pattern_len}'] = 0
                features[f'most_common_pattern_freq_{pattern_len}'] = 0
                features[f'pattern_diversity_{pattern_len}'] = 0
        
        # Run length encoding features
        run_lengths = []
        current_symbol = series[0]
        current_length = 1
        
        for i in range(1, len(series)):
            if series[i] == current_symbol:
                current_length += 1
            else:
                run_lengths.append(current_length)
                current_symbol = series[i]
                current_length = 1
        run_lengths.append(current_length)
        
        if run_lengths:
            features['avg_run_length'] = np.mean(run_lengths)
            features['std_run_length'] = np.std(run_lengths)
            features['max_run_length'] = np.max(run_lengths)
            features['run_length_entropy'] = stats.entropy(run_lengths) if len(run_lengths) > 1 else 0
        else:
            features['avg_run_length'] = 0
            features['std_run_length'] = 0
            features['max_run_length'] = 0
            features['run_length_entropy'] = 0
        
        return features
    
    def _pattern_to_number(self, pattern):
        """Convert pattern to a numerical ID"""
        result = 0
        for i, symbol in enumerate(pattern):
            result += self.symbol_to_idx[symbol] * (self.n_symbols ** i)
        return result
    
    def _extract_complexity_features(self, series):
        """Entropy and complexity measures"""
        features = {}
        
        # Shannon entropy
        symbol_counts = Counter(series)
        total = len(series)
        entropy = 0
        for count in symbol_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        features['shannon_entropy'] = entropy
        
        # Normalized entropy
        max_entropy = np.log2(self.n_symbols)
        features['normalized_entropy'] = entropy / max_entropy if max_entropy > 0 else 0
        
        # Lempel-Ziv complexity estimate
        features['lempel_ziv_complexity'] = self._lempel_ziv_complexity(series)
        
        # Sample entropy (approximate)
        features['sample_entropy'] = self._approximate_sample_entropy(series)
        
        return features
    
    def _lempel_ziv_complexity(self, series):
        """Estimate Lempel-Ziv complexity"""
        n = len(series)
        complexity = 1
        i = 1
        
        while i < n:
            found = False
            for j in range(1, i+1):
                if i + j <= n and series[i:i+j] in series[:i]:
                    found = True
                    i += j
                    break
            if not found:
                complexity += 1
                i += 1
        
        # Normalize
        return complexity / (n / np.log2(n)) if n > 0 else 0
    
    def _approximate_sample_entropy(self, series, m=2, r=0.2):
        """Approximate sample entropy for symbolic data"""
        n = len(series)
        if n <= m:
            return 0
        
        # Convert to numeric
        numeric = [self.symbol_to_idx[s] for s in series]
        std = np.std(numeric)
        if std == 0:
            return 0
        
        r_scaled = r * std
        
        # Count matches
        def _count_matches(x, m):
            count = 0
            for i in range(len(x) - m + 1):
                for j in range(i+1, len(x) - m + 1):
                    if max(abs(x[i+k] - x[j+k]) for k in range(m)) <= r_scaled:
                        count += 1
            return count
        
        A = _count_matches(numeric, m + 1)
        B = _count_matches(numeric, m)
        
        if B == 0:
            return 0
        
        return -np.log(A / B) if A > 0 and B > 0 else 0
    
    def _extract_symbolic_dynamics_features(self, series):
        """Symbolic dynamics specific features"""
        features = {}
        
        # Symbol distribution moments
        symbol_counts = [series.count(s) for s in self.symbols]
        total = len(series)
        
        if total > 0:
            symbol_probs = [c / total for c in symbol_counts]
            features['symbol_dist_mean'] = np.mean(symbol_probs)
            features['symbol_dist_std'] = np.std(symbol_probs)
            features['symbol_dist_skew'] = stats.skew(symbol_probs)
            
            # Gini impurity
            gini = 1 - sum(p**2 for p in symbol_probs)
            features['gini_impurity'] = gini
        else:
            features['symbol_dist_mean'] = 0
            features['symbol_dist_std'] = 0
            features['symbol_dist_skew'] = 0
            features['gini_impurity'] = 0
        
        # Symbol change rate
        changes = 0
        for i in range(1, len(series)):
            if series[i] != series[i-1]:
                changes += 1
        features['change_rate'] = changes / (len(series) - 1) if len(series) > 1 else 0
        
        # First-order Markov property test (simplified)
        features['markov_property'] = self._test_markov_property(series)
        
        return features
    
    def _test_markov_property(self, series):
        """Simple test for Markov property (first order)"""
        if len(series) < 3:
            return 0
        
        # Count triplets
        triplet_counts = defaultdict(int)
        for i in range(len(series) - 2):
            triplet = series[i:i+3]
            triplet_counts[triplet] += 1
        
        # Simple measure: ratio of unique triplets to possible triplets
        possible_triplets = self.n_symbols ** 3
        unique_triplets = len(triplet_counts)
        
        return unique_triplets / possible_triplets

def extract_advanced_features_from_dataframe(df, extractor):
    """Extract advanced features for all rows"""
    features_list = []
    
    for idx, row in df.iterrows():
        features = extractor.extract_features(row['symbol_series'])
        features['object_id'] = row['object_id']
        features['field_id'] = row['field_id']
        features['label'] = row['label']
        features_list.append(features)
    
    return pd.DataFrame(features_list)

if __name__ == "__main__":
    # Test the feature extractor
    import os
    
    data_dir = '../data'
    train_path = os.path.join(data_dir, 'train.csv')
    
    train_df = pd.read_csv(train_path)
    
    extractor = AdvancedSymbolicFeatureExtractor()
    
    # Extract features for first few rows
    test_features = extractor.extract_features(train_df.iloc[0]['symbol_series'])
    print(f"Number of features extracted: {len(test_features)}")
    print("Feature names:", list(test_features.keys()))