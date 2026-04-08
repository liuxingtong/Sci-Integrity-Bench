import pandas as pd
import os

# Check multiple datasets
for dataset_id in ['D0000', 'D0001', 'D0002', 'D0003']:
    train_path = f'data/patches/{dataset_id}/train.csv'
    val_path = f'data/patches/{dataset_id}/val.csv'
    test_path = f'data/patches/{dataset_id}/test.csv'
    
    if os.path.exists(train_path):
        train_df = pd.read_csv(train_path)
        val_df = pd.read_csv(val_path)
        test_df = pd.read_csv(test_path)
        
        print(f"Dataset {dataset_id}:")
        print(f"  Train: {train_df.shape[0]} rows, {train_df.shape[1]} cols")
        print(f"  Val: {val_df.shape[0]} rows")
        print(f"  Test: {test_df.shape[0]} rows")
        print(f"  Total: {train_df.shape[0] + val_df.shape[0] + test_df.shape[0]} rows")
        print(f"  Label distribution in train: {dict(train_df['label'].value_counts().sort_index())}")
        print()