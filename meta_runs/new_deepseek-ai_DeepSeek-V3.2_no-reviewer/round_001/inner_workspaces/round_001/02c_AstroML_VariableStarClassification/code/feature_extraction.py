import pandas as pd
import numpy as np
from collections import Counter
import itertools

class SymbolSeriesFeatureExtractor:
    """Extract features from symbolic time series"""
    
    def __init__(self, symbols=None):
        if symbols is None:
            self.symbols = ['w', '.', '*', 'x', 'z', 'v', 'y', 'u']
        else:
            self.symbols = symbols
        
        # Create mapping for one-hot encoding
        self.symbol_to_idx = {s: i for i, s in enumerate(self.symbols)}
        
    def extract_features(self, symbol_series):
        """Extract all features for a single symbol series"""
        features = {}
        
        # Basic features
        features.update(self._extract_basic_features(symbol_series))
        
        # Symbol frequency features
        features.update(self._extract_frequency_features(symbol_series))
        
        # Transition features
        features.update(self._extract_transition_features(symbol_series))
        
        # N-gram features (bigrams)
        features.update(self._extract_ngram_features(symbol_series, n=2))
        
        # Information-theoretic features
        features.update(self._extract_information_features(symbol_series))
        
        # Pattern-based features
        features.update(self._extract_pattern_features(symbol_series))
        
        return features
    
    def _extract_basic_features(self, series):
        """Basic features"""
        features = {}
        features['length'] = len(series)
        return features
    
    def _extract_frequency_features(self, series):
        """Symbol frequency features"""
        features = {}
        total = len(series)
        
        # Individual symbol frequencies
        for symbol in self.symbols:
            count = series.count(symbol)
            features[f'freq_{symbol}'] = count / total if total > 0 else 0
            features[f'count_{symbol}'] = count
        
        # Most common symbol
        counter = Counter(series)
        most_common = counter.most_common(1)
        if most_common:
            features['most_common_symbol'] = self.symbol_to_idx[most_common[0][0]]
            features['most_common_freq'] = most_common[0][1] / total
        
        return features
    
    def _extract_transition_features(self, series):
        """Transition probability features"""
        features = {}
        
        # Count transitions
        transition_counts = np.zeros((len(self.symbols), len(self.symbols)))
        
        for i in range(len(series) - 1):
            from_sym = series[i]
            to_sym = series[i+1]
            if from_sym in self.symbol_to_idx and to_sym in self.symbol_to_idx:
                from_idx = self.symbol_to_idx[from_sym]
                to_idx = self.symbol_to_idx[to_sym]
                transition_counts[from_idx, to_idx] += 1
        
        # Flatten transition matrix as features
        flat_transitions = transition_counts.flatten()
        for i, val in enumerate(flat_transitions):
            features[f'trans_{i}'] = val
        
        # Normalized transition probabilities
        row_sums = transition_counts.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        transition_probs = transition_counts / row_sums
        
        flat_probs = transition_probs.flatten()
        for i, val in enumerate(flat_probs):
            features[f'trans_prob_{i}'] = val
        
        # Self-transition probability
        self_transitions = np.trace(transition_counts)
        total_transitions = len(series) - 1
        features['self_transition_prob'] = self_transitions / total_transitions if total_transitions > 0 else 0
        
        return features
    
    def _extract_ngram_features(self, series, n=2):
        """N-gram frequency features"""
        features = {}
        
        # Generate all possible n-grams
        all_ngrams = [''.join(p) for p in itertools.product(self.symbols, repeat=n)]
        
        # Count n-grams
        ngram_counts = {ngram: 0 for ngram in all_ngrams}
        for i in range(len(series) - n + 1):
            ngram = series[i:i+n]
            if ngram in ngram_counts:
                ngram_counts[ngram] += 1
        
        # Add n-gram features
        total_ngrams = len(series) - n + 1
        for ngram, count in ngram_counts.items():
            # Use a simplified name for the feature
            feature_name = f'ngram_{ngram}'
            features[feature_name] = count / total_ngrams if total_ngrams > 0 else 0
        
        return features
    
    def _extract_information_features(self, series):
        """Information-theoretic features"""
        features = {}
        
        # Symbol entropy
        symbol_counts = Counter(series)
        total = len(series)
        entropy = 0
        for count in symbol_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        features['entropy'] = entropy
        
        # Maximum possible entropy (log2 of number of symbols)
        max_entropy = np.log2(len(self.symbols))
        features['normalized_entropy'] = entropy / max_entropy if max_entropy > 0 else 0
        
        # Calculate complexity (Lempel-Ziv approximation)
        complexity = self._estimate_complexity(series)
        features['complexity'] = complexity
        
        return features
    
    def _estimate_complexity(self, series):
        """Estimate sequence complexity using Lempel-Ziv approximation"""
        # Simple implementation: count distinct substrings
        substrings = set()
        n = len(series)
        
        for i in range(n):
            for j in range(i + 1, n + 1):
                substrings.add(series[i:j])
        
        # Normalize by sequence length
        return len(substrings) / n if n > 0 else 0
    
    def _extract_pattern_features(self, series):
        """Pattern-based features"""
        features = {}
        
        # Count of pattern repetitions
        repetitions = 0
        for i in range(1, len(series)):
            if series[i] == series[i-1]:
                repetitions += 1
        features['repetitions'] = repetitions
        features['repetition_ratio'] = repetitions / (len(series) - 1) if len(series) > 1 else 0
        
        # Longest run of same symbol
        longest_run = 1
        current_run = 1
        for i in range(1, len(series)):
            if series[i] == series[i-1]:
                current_run += 1
                longest_run = max(longest_run, current_run)
            else:
                current_run = 1
        features['longest_run'] = longest_run
        
        # Number of unique symbols used
        features['unique_symbols'] = len(set(series))
        
        return features

def extract_features_from_dataframe(df, extractor):
    """Extract features for all rows in a dataframe"""
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
    
    extractor = SymbolSeriesFeatureExtractor()
    
    # Extract features for first few rows
    test_features = extractor.extract_features(train_df.iloc[0]['symbol_series'])
    print(f"Number of features extracted: {len(test_features)}")
    print("Feature names:", list(test_features.keys())[:20])  # First 20 features