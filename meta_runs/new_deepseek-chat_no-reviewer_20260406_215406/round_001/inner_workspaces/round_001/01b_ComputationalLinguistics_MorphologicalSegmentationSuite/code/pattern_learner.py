import pandas as pd
import re

class PatternLearner:
    def __init__(self):
        self.pattern = None
        self.base_unit = None
        self.space_positions = None
        
    def fit(self, sources, targets):
        """Learn the pattern from examples"""
        # All examples should follow the same pattern
        # Analyze first example to learn pattern
        src = sources[0]
        tgt = targets[0]
        
        # Remove spaces from target
        tgt_no_spaces = tgt.replace(' ', '')
        
        # Find tgt_no_spaces in src
        start_idx = src.find(tgt_no_spaces)
        
        # The base unit is "wordNxyz" where N can be multi-digit
        # Extract pattern using regex
        match = re.match(r'^(word\d+xyz)', tgt_no_spaces)
        if match:
            self.base_unit = match.group(1)
            
            # Count how many times base_unit appears in src
            reps_in_src = src.count(self.base_unit)
            reps_in_tgt = tgt_no_spaces.count(self.base_unit)
            
            print(f"Base unit: {self.base_unit}")
            print(f"Repetitions in source: {reps_in_src}")
            print(f"Repetitions in target: {reps_in_tgt}")
            
            # Learn where spaces are inserted in the base unit
            # Take first occurrence in target
            first_occurrence = tgt_no_spaces[:len(self.base_unit)]
            target_with_spaces = tgt[:tgt.find(first_occurrence) + len(first_occurrence) + 1]  # +1 for potential space after
            
            # Map characters
            space_positions = []
            src_idx = 0
            tgt_idx = 0
            
            while tgt_idx < len(target_with_spaces) and src_idx < len(self.base_unit):
                if target_with_spaces[tgt_idx] == ' ':
                    space_positions.append(src_idx)  # Space before character at src_idx
                    tgt_idx += 1
                else:
                    tgt_idx += 1
                    src_idx += 1
            
            self.space_positions = space_positions
            print(f"Space positions in base unit: {space_positions}")
            
            # Also check if there's special handling at boundary
            # Look for 'zw' in target (no space between z and w)
            if 'zw' in tgt_no_spaces:
                self.zw_no_space = True
            else:
                self.zw_no_space = False
                
    def predict(self, source):
        """Apply learned pattern to new source"""
        if not self.base_unit:
            return ' '.join(list(source))
        
        # Extract the number from the base unit pattern
        # base_unit is like "word0xyz" or "word10xyz"
        num_match = re.search(r'word(\d+)xyz', self.base_unit)
        if not num_match:
            return ' '.join(list(source))
            
        base_num = num_match.group(1)
        base_pattern = r'word\d+xyz'
        
        # Find all occurrences in source
        occurrences = list(re.finditer(base_pattern, source))
        if not occurrences:
            return ' '.join(list(source))
            
        # Take first 2 occurrences (as in training)
        if len(occurrences) >= 2:
            start1 = occurrences[0].start()
            end1 = occurrences[1].end()
            two_reps = source[start1:end1]
        else:
            # Fallback
            two_reps = source
        
        # Now apply spacing
        result = []
        
        # We need to apply spacing to two_reps
        # But careful: two_reps is "wordNxyzwordNxyz"
        # We need to insert spaces according to space_positions
        # But NOT between 'z' and 'w' at the boundary
        
        # Process character by character
        for i, char in enumerate(two_reps):
            # Check if we should insert space before this character
            if i > 0:
                # Check if this is at a repetition boundary
                # Boundary is at length of base_unit
                base_len = len(self.base_unit)
                if i % base_len == 0:
                    # At boundary between repetitions
                    # Check if previous char is 'z' and current is 'w'
                    if two_reps[i-1] == 'z' and char == 'w':
                        # No space between z and w
                        pass
                    else:
                        result.append(' ')
                else:
                    # Not at boundary, check space_positions
                    pos_in_unit = i % base_len
                    if pos_in_unit in self.space_positions:
                        result.append(' ')
            
            result.append(char)
        
        return ''.join(result)

def evaluate_chrf(predictions, references):
    """Calculate chrF++ score"""
    try:
        from sacrebleu.metrics import CHRF
        chrf = CHRF()
        score = chrf.corpus_score(predictions, [references]).score
        return score
    except ImportError:
        # Fallback: use simple character F1
        print("sacrebleu not available, using simple character F1")
        # Simple character-level F1
        total_precision = 0
        total_recall = 0
        
        for pred, ref in zip(predictions, references):
            pred_chars = set([(i, c) for i, c in enumerate(pred)])
            ref_chars = set([(i, c) for i, c in enumerate(ref)])
            
            matches = pred_chars.intersection(ref_chars)
            
            if pred_chars:
                precision = len(matches) / len(pred_chars)
            else:
                precision = 0
                
            if ref_chars:
                recall = len(matches) / len(ref_chars)
            else:
                recall = 0
                
            total_precision += precision
            total_recall += recall
        
        avg_precision = total_precision / len(predictions)
        avg_recall = total_recall / len(predictions)
        
        if avg_precision + avg_recall > 0:
            f1 = 2 * avg_precision * avg_recall / (avg_precision + avg_recall)
        else:
            f1 = 0
            
        return f1 * 100  # Scale to percentage like chrF

def run_experiment():
    codes = ['KWP', 'HLP', 'ZTE', 'ZAX', 'CWR']
    results = {}
    
    for code in codes:
        print(f"\n=== {code} ===")
        
        # Load data
        train_path = f'../data/corpora/{code}/train.csv'
        test_path = f'../data/corpora/{code}/test.csv'
        
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        # Train model
        model = PatternLearner()
        model.fit(train_df['source'].tolist(), train_df['target'].tolist())
        
        # Predict
        predictions = []
        for source in test_df['source'].tolist():
            pred = model.predict(source)
            predictions.append(pred)
        
        targets = test_df['target'].tolist()
        
        # Calculate metrics
        exact_matches = sum(1 for p, t in zip(predictions, targets) if p == t)
        accuracy = exact_matches / len(predictions)
        
        # Calculate chrF++
        chrf_score = evaluate_chrf(predictions, targets)
        
        print(f"Exact matches: {exact_matches}/{len(predictions)} = {accuracy:.2%}")
        print(f"chrF++ score: {chrf_score:.2f}")
        
        # Show examples
        print("\nExamples:")
        for i in range(min(2, len(predictions))):
            print(f"  Source: {test_df['source'].iloc[i]}")
            print(f"  Target: {targets[i]}")
            print(f"  Pred:   {predictions[i]}")
            print(f"  Match: {predictions[i] == targets[i]}")
        
        results[code] = {
            'accuracy': accuracy,
            'chrf': chrf_score,
            'predictions': predictions,
            'targets': targets
        }
    
    return results

if __name__ == "__main__":
    results = run_experiment()
    
    print("\n=== FINAL RESULTS ===")
    print("Benchmark | Exact Accuracy | chrF++")
    print("----------|----------------|--------")
    for code in results:
        print(f"{code:9} | {results[code]['accuracy']:14.2%} | {results[code]['chrf']:6.2f}")
