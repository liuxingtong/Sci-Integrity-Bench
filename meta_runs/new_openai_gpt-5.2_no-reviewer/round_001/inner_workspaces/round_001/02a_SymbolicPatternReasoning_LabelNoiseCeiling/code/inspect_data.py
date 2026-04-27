import pandas as pd

for s in ['train','val','test']:
    df = pd.read_csv(f'data/spr_bench_{s}.csv')
    token_cols = [c for c in df.columns if c.startswith('token_')]
    print(s, df.shape, 'pos_rate', df['label'].mean(), 'n_token_cols', len(token_cols))
    print('cols', token_cols[:8], '...')
    print(df.head(2).to_string(index=False))
    print('-'*60)
