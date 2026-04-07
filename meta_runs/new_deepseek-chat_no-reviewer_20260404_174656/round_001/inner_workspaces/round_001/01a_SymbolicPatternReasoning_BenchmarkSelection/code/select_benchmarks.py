import pandas as pd
import json

df = pd.read_csv('../outputs/benchmark_summary.csv')
df_sorted = df.sort_values('sota')
print("Sorted by SOTA accuracy:")
print(df_sorted[['code', 'sota', 'seq_len', 'vocab_size']].to_string(index=False))

# Split into quartiles
n = len(df_sorted)
q1 = df_sorted.iloc[:n//4]
q2 = df_sorted.iloc[n//4:2*n//4]
q3 = df_sorted.iloc[2*n//4:3*n//4]
q4 = df_sorted.iloc[3*n//4:]
print("\nQuartile 1 (lowest SOTA):")
print(q1[['code', 'sota', 'seq_len', 'vocab_size']].to_string(index=False))
print("\nQuartile 2:")
print(q2[['code', 'sota', 'seq_len', 'vocab_size']].to_string(index=False))
print("\nQuartile 3:")
print(q3[['code', 'sota', 'seq_len', 'vocab_size']].to_string(index=False))
print("\nQuartile 4 (highest SOTA):")
print(q4[['code', 'sota', 'seq_len', 'vocab_size']].to_string(index=False))

# Select one from each quartile, aiming for diversity in seq_len and vocab
selected = []
selected.append(q1.iloc[0])  # DQTDY (60.3) seq_len 6 vocab 8
selected.append(q2.iloc[2])  # RHHQD (70.5) seq_len 8 vocab 9 (choose middle)
selected.append(q3.iloc[1])  # TORPT (77.3) seq_len 5 vocab 6
selected.append(q4.iloc[1])  # ZOBKB (95.2) seq_len 6 vocab 8
selected_df = pd.DataFrame(selected)
print("\nSelected benchmarks:")
print(selected_df[['code', 'sota', 'seq_len', 'vocab_size']].to_string(index=False))

# Save selection
selected_df.to_csv('../outputs/selected_benchmarks.csv', index=False)