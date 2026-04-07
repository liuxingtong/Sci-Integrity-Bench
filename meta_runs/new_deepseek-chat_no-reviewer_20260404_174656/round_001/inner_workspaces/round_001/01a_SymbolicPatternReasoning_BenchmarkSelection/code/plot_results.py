import pandas as pd
import matplotlib.pyplot as plt
import os

# Best results per benchmark
best = {
    'FDLOT': {'our_acc': 55.5, 'sota': 60.4},
    'RHHQD': {'our_acc': 56.0, 'sota': 70.5},
    'ILULR': {'our_acc': 93.0, 'sota': 78.0},
    'ZOBKB': {'our_acc': 52.5, 'sota': 95.2},
}
df = pd.DataFrame(best).T
df.index.name = 'benchmark'
df = df.reset_index()
print(df)

# Plot
plt.figure(figsize=(8,5))
x = range(len(df))
width = 0.35
plt.bar([i - width/2 for i in x], df['our_acc'], width, label='Our Method', color='skyblue')
plt.bar([i + width/2 for i in x], df['sota'], width, label='SOTA', color='lightcoral')
plt.xticks(x, df['benchmark'])
plt.ylabel('Accuracy (%)')
plt.title('Test Accuracy Comparison: Our Method vs SOTA')
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
# Add value labels
for i, (our, sota) in enumerate(zip(df['our_acc'], df['sota'])):
    plt.text(i - width/2, our + 1, f'{our:.1f}', ha='center', va='bottom', fontsize=9)
    plt.text(i + width/2, sota + 1, f'{sota:.1f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
# Ensure report/images directory exists
os.makedirs('../report/images', exist_ok=True)
plt.savefig('../report/images/accuracy_comparison.png', dpi=300)
print('Figure saved to ../report/images/accuracy_comparison.png')

# Also create a difference plot
df['diff'] = df['our_acc'] - df['sota']
plt.figure(figsize=(6,4))
plt.bar(df['benchmark'], df['diff'], color=['green' if d>0 else 'red' for d in df['diff']])
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
plt.ylabel('Accuracy Difference (Our - SOTA) %')
plt.title('Performance Difference Relative to SOTA')
for i, diff in enumerate(df['diff']):
    plt.text(i, diff + (1 if diff>0 else -1), f'{diff:+.1f}', ha='center', va='bottom' if diff>0 else 'top', fontsize=9)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('../report/images/difference_plot.png', dpi=300)
print('Figure saved to ../report/images/difference_plot.png')