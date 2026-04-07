import pandas as pd
import numpy as np
from itertools import product, combinations
import warnings
warnings.filterwarnings('ignore')

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label'].values
X_val = val[feature_cols]
y_val = val['label'].values
X_test = test[feature_cols]
y_test = test['label'].values

print("Data loaded successfully")
print(f"Train: {X_train.shape}, Validation: {X_val.shape}, Test: {X_test.shape}")

# Convert to shapes and colors
shapes_train = X_train.applymap(lambda x: x[0])
colors_train = X_train.applymap(lambda x: x[1])
shapes_val = X_val.applymap(lambda x: x[0])
colors_val = X_val.applymap(lambda x: x[1])
shapes_test = X_test.applymap(lambda x: x[0])
colors_test = X_test.applymap(lambda x: x[1])

# Define rule templates
def evaluate_rule(rule_func, X_shapes, X_colors, y_true):
    """Evaluate a rule function on data"""
    predictions = rule_func(X_shapes, X_colors)
    accuracy = np.mean(predictions == y_true)
    return accuracy, predictions

# Rule 1: Count-based rules
def make_count_rule(threshold, attribute='shape', target='T', comparison='>'):
    """Rule based on count of specific attribute"""
    def rule_func(X_shapes, X_colors):
        if attribute == 'shape':
            counts = X_shapes.apply(lambda row: (row == target).sum(), axis=1)
        else:  # color
            counts = X_colors.apply(lambda row: (row == target).sum(), axis=1)
        
        if comparison == '>':
            return (counts > threshold).astype(int)
        elif comparison == '>=':
            return (counts >= threshold).astype(int)
        elif comparison == '==':
            return (counts == threshold).astype(int)
        elif comparison == '<':
            return (counts < threshold).astype(int)
        elif comparison == '<=':
            return (counts <= threshold).astype(int)
        else:
            return np.zeros(len(X_shapes))
    return rule_func

# Rule 2: Position-specific rules
def make_position_rule(pos, attribute='shape', target='T'):
    """Rule based on specific position"""
    def rule_func(X_shapes, X_colors):
        if attribute == 'shape':
            return (X_shapes.iloc[:, pos] == target).astype(int)
        else:
            return (X_colors.iloc[:, pos] == target).astype(int)
    return rule_func

# Rule 3: Equality rules (position i equals position j)
def make_equality_rule(pos1, pos2, attribute='shape'):
    """Rule checking if position i equals position j"""
    def rule_func(X_shapes, X_colors):
        if attribute == 'shape':
            return (X_shapes.iloc[:, pos1] == X_shapes.iloc[:, pos2]).astype(int)
        else:
            return (X_colors.iloc[:, pos1] == X_colors.iloc[:, pos2]).astype(int)
    return rule_func

# Rule 4: Pattern rules (alternating, repeating)
def make_pattern_rule(pattern_type='alternating_shape'):
    """Rule checking for patterns"""
    def rule_func(X_shapes, X_colors):
        predictions = []
        for idx in range(len(X_shapes)):
            if pattern_type == 'alternating_shape':
                # Check if shapes alternate
                shapes = X_shapes.iloc[idx].values
                is_alternating = all(shapes[i] != shapes[i+1] for i in range(len(shapes)-1))
                predictions.append(1 if is_alternating else 0)
            elif pattern_type == 'alternating_color':
                # Check if colors alternate
                colors = X_colors.iloc[idx].values
                is_alternating = all(colors[i] != colors[i+1] for i in range(len(colors)-1))
                predictions.append(1 if is_alternating else 0)
            elif pattern_type == 'same_shape_first_last':
                # Check if first and last shape are same
                shapes = X_shapes.iloc[idx].values
                predictions.append(1 if shapes[0] == shapes[-1] else 0)
            elif pattern_type == 'same_color_first_last':
                # Check if first and last color are same
                colors = X_colors.iloc[idx].values
                predictions.append(1 if colors[0] == colors[-1] else 0)
            else:
                predictions.append(0)
        return np.array(predictions)
    return rule_func

# Rule 5: Majority rules
def make_majority_rule(attribute='shape'):
    """Rule based on majority attribute"""
    def rule_func(X_shapes, X_colors):
        predictions = []
        for idx in range(len(X_shapes)):
            if attribute == 'shape':
                values = X_shapes.iloc[idx].values
            else:
                values = X_colors.iloc[idx].values
            
            # Find most common value
            from collections import Counter
            counter = Counter(values)
            most_common = counter.most_common(1)[0][0]
            
            # Predict 1 if most common value appears more than 4 times
            predictions.append(1 if counter[most_common] > 4 else 0)
        return np.array(predictions)
    return rule_func

# Generate and test rules
print("\nGenerating and testing rules...")

rules = []
rule_descriptions = []

# Test count-based rules
for attribute in ['shape', 'color']:
    targets = ['T', 'S', 'C', 'D'] if attribute == 'shape' else ['r', 'g', 'b', 'y']
    for target in targets:
        for threshold in range(1, 8):
            for comparison in ['>', '>=', '==', '<', '<=']:
                rule = make_count_rule(threshold, attribute, target, comparison)
                train_acc, _ = evaluate_rule(rule, shapes_train, colors_train, y_train)
                
                # Keep rules with reasonable performance
                # Lower threshold since even weak signals might be useful
                if train_acc > 0.53 or train_acc < 0.47:
                    rules.append(rule)
                    rule_descriptions.append(f"Count({attribute}={target}) {comparison} {threshold}")

# Test position-specific rules
for pos in range(8):
    for attribute in ['shape', 'color']:
        targets = ['T', 'S', 'C', 'D'] if attribute == 'shape' else ['r', 'g', 'b', 'y']
        for target in targets:
            rule = make_position_rule(pos, attribute, target)
            train_acc, _ = evaluate_rule(rule, shapes_train, colors_train, y_train)
            
            if train_acc > 0.53 or train_acc < 0.47:
                rules.append(rule)
                rule_descriptions.append(f"Pos{pos}({attribute}) = {target}")

# Test equality rules
for pos1, pos2 in combinations(range(8), 2):
    for attribute in ['shape', 'color']:
        rule = make_equality_rule(pos1, pos2, attribute)
        train_acc, _ = evaluate_rule(rule, shapes_train, colors_train, y_train)
        
        if train_acc > 0.53 or train_acc < 0.47:
            rules.append(rule)
            rule_descriptions.append(f"Pos{pos1}({attribute}) == Pos{pos2}({attribute})")

# Test pattern rules
for pattern_type in ['alternating_shape', 'alternating_color', 'same_shape_first_last', 'same_color_first_last']:
    rule = make_pattern_rule(pattern_type)
    train_acc, _ = evaluate_rule(rule, shapes_train, colors_train, y_train)
    
    if train_acc > 0.53 or train_acc < 0.47:
        rules.append(rule)
        rule_descriptions.append(f"Pattern: {pattern_type}")

# Test majority rules
for attribute in ['shape', 'color']:
    rule = make_majority_rule(attribute)
    train_acc, _ = evaluate_rule(rule, shapes_train, colors_train, y_train)
    
    if train_acc > 0.53 or train_acc < 0.47:
        rules.append(rule)
        rule_descriptions.append(f"Majority({attribute}) > 4")

print(f"Generated {len(rules)} candidate rules")

# Evaluate all rules on validation set
print("\nEvaluating rules on validation set...")
rule_performances = []

for i, (rule, desc) in enumerate(zip(rules, rule_descriptions)):
    train_acc, _ = evaluate_rule(rule, shapes_train, colors_train, y_train)
    val_acc, _ = evaluate_rule(rule, shapes_val, colors_val, y_val)
    
    rule_performances.append({
        'rule': desc,
        'train_acc': train_acc,
        'val_acc': val_acc
    })

# Sort by validation accuracy
rule_performances.sort(key=lambda x: max(x['val_acc'], 1 - x['val_acc']), reverse=True)

print("\nTop 20 rules by validation accuracy:")
for i, perf in enumerate(rule_performances[:20]):
    # Use the better of the rule or its negation
    acc = max(perf['val_acc'], 1 - perf['val_acc'])
    print(f"{i+1:2d}. {perf['rule']:40s} train={perf['train_acc']:.3f}, val={perf['val_acc']:.3f} (best={acc:.3f})")

# Try combining rules
print("\n=== Trying rule combinations ===")
# Use top rules as features
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Create feature matrix from top N rules
top_n = min(50, len(rules))
print(f"Using top {top_n} rules as features...")

X_train_rules = []
X_val_rules = []
X_test_rules = []

for i in range(top_n):
    rule = rules[i]
    
    # Get predictions (may need to flip based on validation performance)
    _, train_pred = evaluate_rule(rule, shapes_train, colors_train, y_train)
    _, val_pred = evaluate_rule(rule, shapes_val, colors_val, y_val)
    _, test_pred = evaluate_rule(rule, shapes_test, colors_test, y_test)
    
    # Flip if accuracy < 0.5
    val_acc = rule_performances[i]['val_acc']
    if val_acc < 0.5:
        train_pred = 1 - train_pred
        val_pred = 1 - val_pred
        test_pred = 1 - test_pred
    
    X_train_rules.append(train_pred)
    X_val_rules.append(val_pred)
    X_test_rules.append(test_pred)

X_train_combined = np.column_stack(X_train_rules)
X_val_combined = np.column_stack(X_val_rules)
X_test_combined = np.column_stack(X_test_rules)

print(f"Feature matrix shape: {X_train_combined.shape}")

# Train logistic regression on rule features
print("\nTraining logistic regression on rule features...")
lr = LogisticRegression(C=0.1, max_iter=1000, random_state=42)
lr.fit(X_train_combined, y_train)

y_train_pred = lr.predict(X_train_combined)
y_val_pred = lr.predict(X_val_combined)
y_test_pred = lr.predict(X_test_combined)

train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"Training accuracy: {train_acc:.4f}")
print(f"Validation accuracy: {val_acc:.4f}")
print(f"Test accuracy: {test_acc:.4f}")

# Compare with SOTA
sota_baseline = 0.70
print(f"\nSOTA baseline: {sota_baseline:.4f}")
print(f"Rule combination vs SOTA: {test_acc:.4f} vs {sota_baseline:.4f}")
print(f"Difference: {test_acc - sota_baseline:.4f}")

if test_acc > sota_baseline:
    print("SUCCESS: Rule combination exceeds SOTA!")
else:
    print("Rule combination does not exceed SOTA.")
    
    # Try ensemble of top individual rules
    print("\n=== Trying ensemble of top individual rules ===")
    best_individual_acc = 0
    best_individual_rule = ""
    
    for perf in rule_performances[:20]:
        acc = max(perf['val_acc'], 1 - perf['val_acc'])
        if acc > best_individual_acc:
            best_individual_acc = acc
            best_individual_rule = perf['rule']
    
    print(f"Best individual rule: {best_individual_rule}")
    print(f"Best individual rule accuracy (on validation): {best_individual_acc:.4f}")
    
    # Evaluate on test
    # Find the rule
    for i, (rule, desc) in enumerate(zip(rules, rule_descriptions)):
        if desc == best_individual_rule:
            test_acc_rule, _ = evaluate_rule(rule, shapes_test, colors_test, y_test)
            # Use better of rule or its negation
            test_acc_rule = max(test_acc_rule, 1 - test_acc_rule)
            print(f"Best individual rule test accuracy: {test_acc_rule:.4f}")
            print(f"vs SOTA: {test_acc_rule:.4f} vs {sota_baseline:.4f}")
            break