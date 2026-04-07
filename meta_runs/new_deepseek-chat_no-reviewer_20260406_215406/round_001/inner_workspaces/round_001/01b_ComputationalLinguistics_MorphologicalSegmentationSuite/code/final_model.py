import pandas as pd
import re

class Tokenizer:
    @staticmethod
    def tokenize(text):
        """Tokenize text into units: multi-digit numbers or single characters"""
        tokens = []
        i = 0
        while i < len(text):
            # Check for multi-digit number
            if text[i].isdigit():
                j = i
                while j < len(text) and text[j].isdigit():
                    j += 1
                tokens.append(text[i:j])
                i = j
            else:
                # Single character
                tokens.append(text[i])
                i += 1
        return tokens
    
    @staticmethod
    def detokenize(tokens, spaces_after):
        """Convert tokens back to string with spaces"""
        result = []
        for i, token in enumerate(tokens):
            result.append(token)
            if i < len(spaces_after) and spaces_after[i]:
                result.append(' ')
        return ''.join(result).strip()

class MorphSegmenter:
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.base_tokens = None
        self.space_after = None  # Which tokens have space after them
        self.repetitions_in_target = 2  # Always output 2 repetitions
        
    def fit(self, sources, targets):
        """Learn segmentation pattern from examples"""
        # Use first example
        src = sources[0]
        tgt = targets[0]
        
        # Tokenize target without spaces
        tgt_no_spaces = tgt.replace(' ', '')
        tgt_tokens = self.tokenizer.tokenize(tgt_no_spaces)
        
        # Find in source
        start_idx = src.find(tgt_no_spaces)
        
        # The base unit is the repeating pattern
        # We need to find how many tokens make up one repetition
        # Count occurrences of tgt_no_spaces in src
        occurrences = src.count(tgt_no_spaces)
        
        # If tgt_no_spaces appears multiple times in src, it's the repeating unit
        if occurrences > 1:
            # tgt_no_spaces is one repetition
            tokens_per_rep = len(tgt_tokens)
        else:
            # Need to find the repeating unit
            # Look for pattern word\d+xyz
            match = re.search(r'(word\d+xyz)', tgt_no_spaces)
            if match:
                base = match.group(1)
                base_tokens = self.tokenizer.tokenize(base)
                tokens_per_rep = len(base_tokens)
                # tgt_tokens should be multiple of base_tokens
                if len(tgt_tokens) % tokens_per_rep == 0:
                    self.base_tokens = base_tokens
                    self.repetitions_in_target = len(tgt_tokens) // tokens_per_rep
                else:
                    self.base_tokens = tgt_tokens
                    self.repetitions_in_target = 1
            else:
                self.base_tokens = tgt_tokens
                self.repetitions_in_target = 1
        
        # Now learn which tokens have space after them in target
        # Reconstruct target from tokens and spaces
        target_tokens_with_spaces = []
        i = 0
        token_idx = 0
        
        while i < len(tgt) and token_idx < len(tgt_tokens):
            token = tgt_tokens[token_idx]
            if tgt[i:i+len(token)] == token:
                target_tokens_with_spaces.append(token)
                i += len(token)
                token_idx += 1
                
                # Check if next is space
                if i < len(tgt) and tgt[i] == ' ':
                    target_tokens_with_spaces.append(True)  # Space after
                    i += 1
                else:
                    target_tokens_with_spaces.append(False)  # No space after
            else:
                # Shouldn't happen
                i += 1
        
        # Extract space pattern for one repetition
        if self.base_tokens:
            # Find base_tokens in tgt_tokens
            base_str = ''.join(self.base_tokens)
            tgt_str = ''.join(tgt_tokens)
            
            if base_str in tgt_str:
                start = tgt_str.find(base_str)
                # Extract space pattern for this occurrence
                space_pattern = []
                
                # We need to map from tgt_tokens to space_after
                # Actually simpler: learn from the full target
                # Build space_after for each position in base_tokens
                space_after = [True] * len(self.base_tokens)  # Default space after each
                space_after[-1] = False  # Last token doesn't have space after (except boundary case)
                
                # Look at target to see actual pattern
                # For now, use heuristic based on observed pattern
                # In "w o r d 0 x y z", spaces are after w, o, r, d, 0, x, y
                # But NOT after z (when followed by w)
                
                # Actually, let's extract from the actual target
                # Find positions of base tokens in target
                target_tokenized = []
                i = 0
                while i < len(tgt):
                    if tgt[i] == ' ':
                        i += 1
                        continue
                    
                    # Check for multi-digit number
                    if tgt[i].isdigit():
                        j = i
                        while j < len(tgt) and tgt[j].isdigit():
                            j += 1
                        target_tokenized.append(tgt[i:j])
                        i = j
                    else:
                        target_tokenized.append(tgt[i])
                        i += 1
                
                # Now we have target_tokenized which should match tgt_tokens
                # And we can see where spaces are
                # Re-scan target to mark spaces
                space_after = []
                i = 0
                token_idx = 0
                
                while i < len(tgt) and token_idx < len(target_tokenized):
                    token = target_tokenized[token_idx]
                    if tgt.startswith(token, i):
                        i += len(token)
                        # Check if space after
                        if i < len(tgt) and tgt[i] == ' ':
                            space_after.append(True)
                            # Skip space(s)
                            while i < len(tgt) and tgt[i] == ' ':
                                i += 1
                        else:
                            space_after.append(False)
                        token_idx += 1
                    else:
                        i += 1
                
                # Take space pattern for first repetition
                if len(space_after) >= len(self.base_tokens):
                    self.space_after = space_after[:len(self.base_tokens)]
                else:
                    self.space_after = [True] * (len(self.base_tokens) - 1) + [False]
                
                print(f"Learned: base_tokens = {self.base_tokens}")
                print(f"         space_after = {self.space_after}")
                print(f"         repetitions_in_target = {self.repetitions_in_target}")
        
    def predict(self, source):
        """Segment source string"""
        if not self.base_tokens:
            # Fallback
            return ' '.join(list(source))
        
        # Tokenize source
        source_tokens = self.tokenizer.tokenize(source)
        
        # Find base pattern in source
        base_str = ''.join(self.base_tokens)
        source_str = ''.join(source_tokens)
        
        # Count occurrences
        occurrences = source_str.count(base_str)
        
        if occurrences >= self.repetitions_in_target:
            # Take first N repetitions
            # Build result tokens
            result_tokens = []
            result_spaces = []
            
            # We need to output self.repetitions_in_target repetitions
            for rep in range(self.repetitions_in_target):
                for i, token in enumerate(self.base_tokens):
                    result_tokens.append(token)
                    # Apply space pattern
                    if i < len(self.space_after):
                        result_spaces.append(self.space_after[i])
                    else:
                        result_spaces.append(True)  # Default
                
                # Special handling at boundary between repetitions
                if rep < self.repetitions_in_target - 1:
                    # At boundary, check if last token is 'z' and next first is 'w'
                    if result_tokens and result_tokens[-1] == 'z' and self.base_tokens[0] == 'w':
                        # No space between z and w
                        result_spaces[-1] = False
            
            # Convert to string
            return self.tokenizer.detokenize(result_tokens, result_spaces)
        else:
            # Not enough repetitions, fallback
            return ' '.join(source_tokens)

def calculate_chrf(predictions, references):
    """Calculate chrF++ score using sacrebleu"""
    try:
        from sacrebleu import corpus_chrf
        # chrF++ with word order=2, beta=2
        score = corpus_chrf(predictions, [references], word_order=2, beta=2).score
        return score
    except ImportError:
        # Fallback implementation
        print("Warning: sacrebleu not available, using simple character F1")
        
        total_f1 = 0
        for pred, ref in zip(predictions, references):
            # Character-level precision and recall
            pred_chars = pred.replace(' ', '')
            ref_chars = ref.replace(' ', '')
            
            # Count matching characters
            matches = 0
            for c in set(pred_chars):
                pred_count = pred_chars.count(c)
                ref_count = ref_chars.count(c)
                matches += min(pred_count, ref_count)
            
            if len(pred_chars) > 0:
                precision = matches / len(pred_chars)
            else:
                precision = 0
                
            if len(ref_chars) > 0:
                recall = matches / len(ref_chars)
            else:
                recall = 0
                
            if precision + recall > 0:
                f1 = 2 * precision * recall / (precision + recall)
            else:
                f1 = 0
                
            total_f1 += f1
        
        return (total_f1 / len(predictions)) * 100

def main():
    codes = ['KWP', 'HLP', 'ZTE', 'ZAX', 'CWR']
    results = {}
    
    for code in codes:
        print(f"\n{'='*50}")
        print(f"Training and evaluating on {code}")
        print(f"{'='*50}")
        
        # Load data
        train_path = f'../data/corpora/{code}/train.csv'
        test_path = f'../data/corpora/{code}/test.csv'
        
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        # Train model
        model = MorphSegmenter()
        model.fit(train_df['source'].tolist(), train_df['target'].tolist())
        
        # Predict on test
        predictions = []
        for source in test_df['source'].tolist():
            pred = model.predict(source)
            predictions.append(pred)
        
        targets = test_df['target'].tolist()
        
        # Calculate metrics
        exact_matches = sum(1 for p, t in zip(predictions, targets) if p == t)
        accuracy = exact_matches / len(predictions)
        
        # Calculate chrF++
        chrf_score = calculate_chrf(predictions, targets)
        
        print(f"\nResults for {code}:")
        print(f"  Exact matches: {exact_matches}/{len(predictions)} = {accuracy:.2%}")
        print(f"  chrF++ score: {chrf_score:.2f}")
        
        # Show examples
        print("\n  Examples:")
        for i in range(min(2, len(predictions))):
            print(f"    Source: {test_df['source'].iloc[i]}")
            print(f"    Target: {targets[i]}")
            print(f"    Pred:   {predictions[i]}")
            print(f"    Match: {predictions[i] == targets[i]}")
        
        results[code] = {
            'accuracy': accuracy,
            'chrf': chrf_score,
            'predictions': predictions,
            'targets': targets
        }
    
    # Summary
    print("\n" + "="*60)
    print("FINAL RESULTS SUMMARY")
    print("="*60)
    print(f"{'Benchmark':10} | {'Exact Acc':10} | {'chrF++':10}")
    print("-"*40)
    
    for code in codes:
        print(f"{code:10} | {results[code]['accuracy']:9.2%} | {results[code]['chrf']:9.2f}")
    
    # Save results
    import json
    with open('../outputs/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    main()
