import pandas as pd
from sacrebleu.metrics import CHRF

# Load test data for one benchmark
benchmark_code = "KWP"
test_df = pd.read_csv(f'../data/corpora/{benchmark_code}/test.csv')

# What if we had perfect predictions?
perfect_predictions = test_df['target'].tolist()
references = test_df['target'].tolist()

chrf = CHRF(word_order=2)
perfect_score = chrf.corpus_score(perfect_predictions, [references])
print(f"Perfect chrF++ score (predictions = references): {perfect_score.score:.4f}")

# What if we predict character-level segmentation (all chars separated)?
char_predictions = []
for source in test_df['source']:
    # Character-level segmentation
    char_segmented = ' '.join(list(source))
    char_predictions.append(char_segmented)

char_score = chrf.corpus_score(char_predictions, [references])
print(f"Character-level segmentation chrF++: {char_score.score:.4f}")

# What if we predict the pattern from training (with '1' instead of actual number)?
pattern_predictions = []
for source in test_df['source']:
    # Extract number from source (e.g., 'word200xyz' -> 200)
    # Actually source is 'word200xyzword200xyzword200xyz'
    # The pattern is triple repetition
    # For perfect pattern prediction, we need to extract the number
    # and apply the segmentation rule
    
    # Try to match training pattern
    # Training has numbers 0-11, test has 200+
    # If we use '1' for all numbers:
    pattern = 'w o r d 1 x y zw o r d 1 x y z'
    pattern_predictions.append(pattern)

pattern_score = chrf.corpus_score(pattern_predictions, [references])
print(f"Pattern prediction (with '1') chrF++: {pattern_score.score:.4f}")

# Show examples
print("\nExamples:")
for i in range(min(2, len(test_df))):
    print(f"Source: {test_df.iloc[i]['source']}")
    print(f"Reference: {test_df.iloc[i]['target']}")
    print(f"Char-level: {char_predictions[i]}")
    print(f"Pattern: {pattern_predictions[i]}")
    print()
