import pandas as pd
import itertools

def load_benchmark(code):
    train = pd.read_csv(f'../data/{code}_train.csv')
    val = pd.read_csv(f'../data/{code}_val.csv')
    test = pd.read_csv(f'../data/{code}_test.csv')
    return train, val, test

code = 'ZOBKB'
train, val, test = load_benchmark(code)
token_cols = [c for c in train.columns if c.startswith('token_')]
print(f'Analyzing {code}')
print(f'Sequence length: {len(token_cols)}')
print('First 20 samples:')
for i in range(20):
    tokens = list(train.iloc[i][token_cols])
    label = train.iloc[i]['label']
    print(f'  {tokens} -> {label}')

# Try to find simple rules
# Rule 1: equality between any two positions
for i, j in itertools.combinations(range(len(token_cols)), 2):
    matches = (train[token_cols[i]] == train[token_cols[j]])
    accuracy = (matches == train['label']).mean()
    if accuracy > 0.9:
        print(f'Rule: token_{i} == token_{j} -> label 1? accuracy {accuracy:.4f}')
# Rule 2: token at position k equals a specific value
for col in token_cols:
    for val_token in train[col].unique():
        matches = (train[col] == val_token)
        accuracy = (matches == train['label']).mean()
        if accuracy > 0.9:
            print(f'Rule: {col} == {val_token} -> label 1? accuracy {accuracy:.4f}')
# Rule 3: count of a specific token in sequence
for token in set(pd.concat([train[col] for col in token_cols])):
    counts = (train[token_cols] == token).sum(axis=1)
    # parity?
    for parity in [0,1]:
        matches = (counts % 2 == parity)
        accuracy = (matches == train['label']).mean()
        if accuracy > 0.9:
            print(f'Rule: count({token}) % 2 == {parity} -> label 1? accuracy {accuracy:.4f}')
# Rule 4: pattern of transitions (e.g., token_i is 'S' something)
# Extract first letter and second letter
first_letters = train[token_cols].applymap(lambda x: x[0])
second_letters = train[token_cols].applymap(lambda x: x[1])
for col in token_cols:
    for letter in first_letters[col].unique():
        matches = (first_letters[col] == letter)
        accuracy = (matches == train['label']).mean()
        if accuracy > 0.9:
            print(f'Rule: first letter of {col} == {letter} -> label 1? accuracy {accuracy:.4f}')
    for letter in second_letters[col].unique():
        matches = (second_letters[col] == letter)
        accuracy = (matches == train['label']).mean()
        if accuracy > 0.9:
            print(f'Rule: second letter of {col} == {letter} -> label 1? accuracy {accuracy:.4f}')