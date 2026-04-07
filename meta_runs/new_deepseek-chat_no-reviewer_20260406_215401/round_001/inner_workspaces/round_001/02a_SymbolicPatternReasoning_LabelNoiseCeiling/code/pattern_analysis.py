import pandas as pd
import numpy as np
from itertools import product
import matplotlib.pyplot as plt

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

print("Analyzing patterns in the data...\n")

# Function to extract patterns
def extract_patterns(sequence):
    """Extract various patterns from a sequence."""
    patterns = {}
    
    # Shape and color sequences
    shapes = [token[0] for token in sequence]
    colors = [token[1] for token in sequence]
    
    # Pattern 1: Specific token at specific position
    for i, token in enumerate(sequence):
        patterns[f'token_{i}={token}'] = 1
    
    # Pattern 2: Shape at position
    for i, shape in enumerate(shapes):
        patterns[f'shape_{i}={shape}'] = 1
    
    # Pattern 3: Color at position
    for i, color in enumerate(colors):
        patterns[f'color_{i}={color}'] = 1
    
    # Pattern 4: Adjacent pairs
    for i in range(7):
        patterns[f'pair_{i}={sequence[i]}{sequence[i+1]}'] = 1
    
    # Pattern 5: Shape transitions
    for i in range(7):
        patterns[f'shape_trans_{i}={shapes[i]}{shapes[i+1]}'] = 1
    
    # Pattern 6: Color transitions
    for i in range(7):
        patterns[f'color_trans_{i}={colors[i]}{colors[i+1]}'] = 1
    
    # Pattern 7: Token appears at least once
    for token in set(sequence):
        patterns[f'has_{token}'] = 1
    
    # Pattern 8: Shape appears at least once
    for shape in set(shapes):
        patterns[f'has_shape_{shape}'] = 1
    
    # Pattern 9: Color appears at least once
    for color in set(colors):
        patterns[f'has_color_{color}'] = 1
    
    return patterns

# Analyze training data to find predictive patterns
print("Finding predictive patterns in training data...")

# Collect all patterns and their label associations
pattern_counts = {}
pattern_label_sums = {}

for idx, row in train.iterrows():
    sequence = [row[col] for col in feature_cols]
    label = row['label']
    patterns = extract_patterns(sequence)
    
    for pattern in patterns:
        if pattern not in pattern_counts:
            pattern_counts[pattern] = 0
            pattern_label_sums[pattern] = 0
        pattern_counts[pattern] += 1
        pattern_label_sums[pattern] += label

# Calculate pattern predictive power
pattern_scores = []
for pattern in pattern_counts:
    count = pattern_counts[pattern]
    label_sum = pattern_label_sums[pattern]
    p_label1 = label_sum / count
    # Score based on deviation from overall label distribution
    overall_p = train['label'].mean()
    score = abs(p_label1 - overall_p)
    pattern_scores.append((pattern, count, p_label1, score))

# Sort by predictive power
pattern_scores.sort(key=lambda x: x[3], reverse=True)

print("\nTop 20 most predictive patterns:")
print("Pattern | Count | P(Label=1) | Score")
print("-" * 50)
for pattern, count, p_label1, score in pattern_scores[:20]:
    print(f"{pattern:30} {count:5} {p_label1:.3f}      {score:.3f}")

# Try a simple rule-based classifier using top patterns
def rule_based_predict(sequence, top_patterns, thresholds):
    """Predict label based on presence of predictive patterns."""
    patterns = extract_patterns(sequence)
    score = 0
    
    for pattern, weight in top_patterns.items():
        if pattern in patterns:
            score += weight
    
    return 1 if score > thresholds else 0

# Create a simple classifier using top 10 patterns
top_patterns = {}
for pattern, count, p_label1, score in pattern_scores[:10]:
    # Weight by how predictive it is (positive if p_label1 > 0.5, negative otherwise)
    weight = (p_label1 - 0.5) * 2  # Scale to [-1, 1]
    top_patterns[pattern] = weight

print(f"\nCreated rule-based classifier with {len(top_patterns)} patterns")

# Evaluate on training data
train_correct = 0
for idx, row in train.iterrows():
    sequence = [row[col] for col in feature_cols]
    label = row['label']
    pred = rule_based_predict(sequence, top_patterns, 0)
    if pred == label:
        train_correct += 1

train_acc = train_correct / len(train)
print(f"Training accuracy: {train_acc:.4f}")

# Try to optimize threshold on validation data
print("\nOptimizing threshold on validation data...")
best_acc = 0
best_threshold = 0

for threshold in np.arange(-1, 1, 0.1):
    val_correct = 0
    for idx, row in val.iterrows():
        sequence = [row[col] for col in feature_cols]
        label = row['label']
        pred = rule_based_predict(sequence, top_patterns, threshold)
        if pred == label:
            val_correct += 1
    
    val_acc = val_correct / len(val)
    if val_acc > best_acc:
        best_acc = val_acc
        best_threshold = threshold
    
    print(f"Threshold {threshold:.1f}: Val accuracy = {val_acc:.4f}")

print(f"\nBest threshold: {best_threshold:.1f}, Best val accuracy: {best_acc:.4f}")

# Test with best threshold
test_correct = 0
for idx, row in test.iterrows():
    sequence = [row[col] for col in feature_cols]
    label = row['label']
    pred = rule_based_predict(sequence, top_patterns, best_threshold)
    if pred == label:
        test_correct += 1

test_acc = test_correct / len(test)
print(f"Test accuracy: {test_acc:.4f}")

# Compare with SOTA
sota_acc = 0.70
print(f"\nSOTA: {sota_acc:.2%}")
print(f"Rule-based classifier: {test_acc:.2%}")
print(f"Difference: {test_acc - sota_acc:+.2%}")

# Save results
results = pd.DataFrame({
    'Model': ['RuleBased'],
    'Train Accuracy': [train_acc],
    'Validation Accuracy': [best_acc],
    'Test Accuracy': [test_acc]
})
results.to_csv('../outputs/rule_based_results.csv', index=False)
print("\nResults saved to outputs/rule_based_results.csv")

# Create visualization of pattern predictive power
plt.figure(figsize=(12, 6))
top_n = 30
patterns = [p[0] for p in pattern_scores[:top_n]]
scores = [p[3] for p in pattern_scores[:top_n]]

plt.barh(range(top_n), scores)
plt.yticks(range(top_n), patterns)
plt.xlabel('Predictive Power (deviation from expected)')
plt.title(f'Top {top_n} Most Predictive Patterns')
plt.tight_layout()
plt.savefig('../report/images/predictive_patterns.png', dpi=300)
print("\nPattern analysis saved to report/images/predictive_patterns.png")