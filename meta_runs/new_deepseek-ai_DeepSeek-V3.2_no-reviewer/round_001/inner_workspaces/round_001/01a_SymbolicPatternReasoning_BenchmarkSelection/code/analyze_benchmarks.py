import pandas as pd
import json
import os
import numpy as np

# Load registry and order
with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)
with open("../data/benchmark_order.json") as f:
    order = json.load(f)

# Create summary dataframe
summary_data = []
for code in order:
    info = registry[code]
    # Load train data to get sequence length
    train = pd.read_csv(f"../data/{code}_train.csv")
    token_cols = [col for col in train.columns if col.startswith('token_')]
    seq_len = len(token_cols)
    
    summary_data.append({
        'code': code,
        'sota_accuracy': info['sota_accuracy'],
        'train_size': info['train_size'],
        'val_size': info['val_size'],
        'test_size': info['test_size'],
        'sequence_length': seq_len,
        'num_features': seq_len,  # each token is a categorical feature
        'presentation_order': order.index(code) + 1
    })

summary_df = pd.DataFrame(summary_data)
print("Benchmark Summary:")
print(summary_df.to_string())
print("\n")

# Statistics
print("SOTA Accuracy Statistics:")
print(f"Mean: {summary_df['sota_accuracy'].mean():.2f}%")
print(f"Std: {summary_df['sota_accuracy'].std():.2f}%")
print(f"Min: {summary_df['sota_accuracy'].min():.2f}% (code: {summary_df.loc[summary_df['sota_accuracy'].idxmin(), 'code']})")
print(f"Max: {summary_df['sota_accuracy'].max():.2f}% (code: {summary_df.loc[summary_df['sota_accuracy'].idxmax(), 'code']})")
print(f"Median: {summary_df['sota_accuracy'].median():.2f}%")

print("\nSequence Length Statistics:")
print(f"Mean: {summary_df['sequence_length'].mean():.2f}")
print(f"Std: {summary_df['sequence_length'].std():.2f}")
print(f"Min: {summary_df['sequence_length'].min()} (code: {summary_df.loc[summary_df['sequence_length'].idxmin(), 'code']})")
print(f"Max: {summary_df['sequence_length'].max()} (code: {summary_df.loc[summary_df['sequence_length'].idxmax(), 'code']})")

# Group by difficulty
print("\nDifficulty Groups (by SOTA accuracy):")
summary_df['difficulty'] = pd.cut(summary_df['sota_accuracy'], 
                                   bins=[0, 70, 80, 90, 100],
                                   labels=['Very Hard (<70%)', 'Hard (70-80%)', 'Medium (80-90%)', 'Easy (>90%)'])
print(summary_df.groupby('difficulty').size())

# Show one from each difficulty group
print("\nOne benchmark from each difficulty group:")
for diff in ['Very Hard (<70%)', 'Hard (70-80%)', 'Medium (80-90%)', 'Easy (>90%)']:
    group = summary_df[summary_df['difficulty'] == diff]
    if len(group) > 0:
        sample = group.iloc[0]
        print(f"{diff}: {sample['code']} (SOTA: {sample['sota_accuracy']}%, SeqLen: {sample['sequence_length']})")