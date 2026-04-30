import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    os.makedirs('../outputs', exist_ok=True)
    train = pd.read_csv('../data/train.csv')
    
    print("Default rate:", train['default_flag'].mean())
    
    # Character frequencies
    chars = ['A', 'B', 'C', 'D', '1', '2']
    for c in chars:
        train[f'count_{c}'] = train['sym_seq'].str.count(c)
        
    for c in chars:
        print(f"Mean count {c} for default=0: {train[train['default_flag']==0][f'count_{c}'].mean():.2f}")
        print(f"Mean count {c} for default=1: {train[train['default_flag']==1][f'count_{c}'].mean():.2f}")
        
    # Position specific frequencies
    seq_len = 20
    pos_stats = []
    for i in range(seq_len):
        train[f'pos_{i}'] = train['sym_seq'].str[i]
        for c in chars:
            rate_0 = (train[train['default_flag']==0][f'pos_{i}'] == c).mean()
            rate_1 = (train[train['default_flag']==1][f'pos_{i}'] == c).mean()
            pos_stats.append({'pos': i, 'char': c, 'rate_0': rate_0, 'rate_1': rate_1, 'diff': rate_1 - rate_0})
            
    pos_df = pd.DataFrame(pos_stats)
    pos_df['abs_diff'] = pos_df['diff'].abs()
    print("\nTop position differences:")
    print(pos_df.sort_values('abs_diff', ascending=False).head(10))

if __name__ == '__main__':
    main()
