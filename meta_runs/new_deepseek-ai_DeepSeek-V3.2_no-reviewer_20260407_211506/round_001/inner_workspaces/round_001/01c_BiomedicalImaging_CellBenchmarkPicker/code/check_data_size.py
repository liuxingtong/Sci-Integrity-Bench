import pandas as pd
import os

# Check a few datasets
for ds_id in ['D0014', 'D0011', 'D0006', 'D0003']:
    train_path = f"../data/patches/{ds_id}/train.csv"
    val_path = f"../data/patches/{ds_id}/val.csv"
    test_path = f"../data/patches/{ds_id}/test.csv"
    
    for split, path in [('train', train_path), ('val', val_path), ('test', test_path)]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"Dataset {ds_id} {split}: {len(df)} rows, {df.shape[1]} columns")
            print(f"  Label distribution: {dict(df['label'].value_counts().sort_index())}")
        else:
            print(f"Dataset {ds_id} {split}: File not found")
    print()