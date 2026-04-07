import pandas as pd
import os

selected = ['D0014', 'D0010', 'D0009', 'D0008']
for dataset_id in selected:
    train_path = f'../data/patches/{dataset_id}/train.csv'
    val_path = f'../data/patches/{dataset_id}/val.csv'
    test_path = f'../data/patches/{dataset_id}/test.csv'
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    print(f"{dataset_id}: train {train_df.shape}, val {val_df.shape}, test {test_df.shape}")
    print(f"  Label distribution train: {dict(train_df['label'].value_counts().sort_index())}")
    print(f"  Label distribution val: {dict(val_df['label'].value_counts().sort_index())}")
    print(f"  Label distribution test: {dict(test_df['label'].value_counts().sort_index())}")
