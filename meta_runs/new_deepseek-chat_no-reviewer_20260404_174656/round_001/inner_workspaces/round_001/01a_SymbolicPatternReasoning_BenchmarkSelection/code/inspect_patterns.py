import pandas as pd

def load_benchmark(code):
    train = pd.read_csv(f'../data/{code}_train.csv')
    val = pd.read_csv(f'../data/{code}_val.csv')
    test = pd.read_csv(f'../data/{code}_test.csv')
    return train, val, test

for code in ['ILULR', 'FDLOT']:
    train, val, test = load_benchmark(code)
    token_cols = [c for c in train.columns if c.startswith('token_')]
    print(f'\n=== {code} ===')
    print('First 10 training samples:')
    for i in range(10):
        tokens = list(train.iloc[i][token_cols])
        label = train.iloc[i]['label']
        print(f'  {tokens} -> {label}')
    # Check if there's any obvious pattern
    # Group by token sequence and label
    seq_label = train.groupby(token_cols + ['label']).size().reset_index()
    print(f'Number of unique sequences: {len(seq_label)}')
    # Are there duplicate sequences with different labels?
    dup = seq_label[token_cols].duplicated()
    if dup.any():
        print('Warning: some sequences have multiple labels (ambiguous)')
    else:
        print('Each unique sequence has a unique label')
    # Show most frequent sequences
    print('Most frequent sequences:')
    top = train.groupby(token_cols).size().sort_values(ascending=False).head(5)
    for seq, count in top.items():
        label = train[train[token_cols].apply(tuple, axis=1) == seq]['label'].iloc[0]
        print(f'  {list(seq)}: count={count}, label={label}')