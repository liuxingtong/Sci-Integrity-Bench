import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

best_acc = 0
best_rule = ""

def check_rule(preds, name):
    global best_acc, best_rule
    acc = accuracy_score(train['label'], preds)
    if acc < 0.5:
        acc = 1 - acc
        name = f"NOT ({name})"
    if acc > best_acc:
        best_acc = acc
        best_rule = name
    if acc > 0.65:
        print(f"Rule: {name}, Acc: {acc:.4f}")

# 16. Is there a label noise ceiling?
# Let's train a very powerful model (e.g., Random Forest with no depth limit) and see its training accuracy.
# If it's 1.0, then the data is perfectly separable, meaning there is a deterministic rule (or we just overfit).
# Wait, we already did this in train_models.py and got Train Acc: 1.0000 for Random Forest and MLP.
# This means the data IS perfectly separable by these models.
# But validation accuracy is ~0.53.
# This strongly suggests that the labels are mostly random noise, OR the rule is extremely complex and not captured by the inductive bias of these models.
# Let's check if there are identical sequences with different labels.
# We already checked this in check_noise.py and found 0 conflicting sequences.
# BUT, are there any identical sequences at all?

print(f"Total sequences: {len(train)}")
train['seq'] = train[feature_cols].apply(lambda x: ' '.join(x), axis=1)
print(f"Unique sequences: {train['seq'].nunique()}")

# Since all sequences are unique, a model can easily memorize them.
# Let's try to find the rule using a symbolic regression or decision tree approach.

from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(train[feature_cols])
y_train = train['label']

# Train a shallow decision tree to see if there's a simple rule
dt = DecisionTreeClassifier(max_depth=3, random_state=42)
dt.fit(X_train, y_train)
print(f"\nDecision Tree (depth=3) Train Acc: {accuracy_score(y_train, dt.predict(X_train)):.4f}")

# Print the tree
feature_names = encoder.get_feature_names_out(feature_cols)
tree_rules = export_text(dt, feature_names=list(feature_names))
print("\nDecision Tree Rules:")
print(tree_rules)

# Let's try a slightly deeper tree
dt = DecisionTreeClassifier(max_depth=5, random_state=42)
dt.fit(X_train, y_train)
print(f"\nDecision Tree (depth=5) Train Acc: {accuracy_score(y_train, dt.predict(X_train)):.4f}")

# Let's try to find the rule by looking at the SOTA reference.
# The protocol says: "The current state-of-the-art accuracy on SPR_BENCH is 70%."
# This is a huge hint! If the SOTA is only 70%, it means the dataset likely contains 30% label noise!
# Or, the rule is deterministic but only 70% of the data follows it, and 30% is random.
# Or, the rule itself is probabilistic.
# Let's assume there is a simple rule that gives ~70% accuracy.

# Let's re-evaluate all our simple rules and see if any hit ~70%.
# Wait, the best rule we found so far was ~53%.
# Let's check more complex rules.

# 17. Palindrome with noise?
def is_palindrome(row):
    return list(row) == list(row)[::-1]

preds = train[feature_cols].apply(is_palindrome, axis=1)
check_rule(preds, "is palindrome")

# 18. Shape palindrome
def is_shape_palindrome(row):
    shapes = [t[0] for t in row]
    return shapes == shapes[::-1]

preds = train[feature_cols].apply(is_shape_palindrome, axis=1)
check_rule(preds, "is shape palindrome")

# 19. Color palindrome
def is_color_palindrome(row):
    colors = [t[1] for t in row]
    return colors == colors[::-1]

preds = train[feature_cols].apply(is_color_palindrome, axis=1)
check_rule(preds, "is color palindrome")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
