import pandas as pd

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

def check_duplicates(df, name):
    # Convert features to a single string for easy grouping
    df['seq'] = df[feature_cols].apply(lambda x: ' '.join(x), axis=1)
    
    # Group by sequence and count unique labels
    grouped = df.groupby('seq')['label'].nunique()
    
    conflicting = grouped[grouped > 1]
    print(f"\n{name} set:")
    print(f"Total sequences: {len(df)}")
    print(f"Unique sequences: {len(grouped)}")
    print(f"Sequences with conflicting labels: {len(conflicting)}")
    
    if len(conflicting) > 0:
        print("Example conflicting sequences:")
        for seq in conflicting.index[:3]:
            print(f"Sequence: {seq}")
            print(df[df['seq'] == seq][['label']])

check_duplicates(train, 'Train')
check_duplicates(val, 'Val')
check_duplicates(test, 'Test')
