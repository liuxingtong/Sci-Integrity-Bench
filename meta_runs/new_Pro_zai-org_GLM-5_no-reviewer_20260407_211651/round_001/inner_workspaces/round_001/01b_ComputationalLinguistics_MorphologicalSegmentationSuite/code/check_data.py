import pandas as pd
import os

codes = ['KWP', 'HLP', 'ZTE', 'ZAX', 'CWR', 'PUV', 'USY', 'WVZ', 'FGL', 'OOG', 'HIB', 'OSV', 'VDN', 'MDA', 'DWN', 'NWK', 'BJP']

for c in codes:
    train_path = f'data/corpora/{c}/train.csv'
    val_path = f'data/corpora/{c}/val.csv'
    test_path = f'data/corpora/{c}/test.csv'
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    print(f'{c}: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}')
