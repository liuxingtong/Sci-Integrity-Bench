import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import torch
import json

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# Load registry to get benchmark metadata
with open('../data/registry.json', 'r') as f:
    registry = json.load(f)

benchmarks = {b['code']: b for b in registry['benchmarks']}

# Load results
results_df = pd.read_csv('../outputs/results_summary.csv')
print("Results summary:")
print(results_df)

# Add metadata
results_df['script_family'] = results_df['benchmark'].map(lambda x: benchmarks[x]['script_family'])
results_df['dev_bleu'] = results_df['benchmark'].map(lambda x: benchmarks[x]['dev_bleu'])
results_df['test_size'] = results_df['benchmark'].map(lambda x: benchmarks[x]['test_size'])

# Plot 1: chrF++ scores by benchmark
plt.figure(figsize=(10, 6))
ax = sns.barplot(x='benchmark', y='chrf_score', hue='script_family', data=results_df)
plt.title('chrF++ Scores by Benchmark')
plt.ylabel('chrF++ Score')
plt.xlabel('Benchmark Code')
plt.ylim(0, 100)
for i, v in enumerate(results_df['chrf_score']):
    ax.text(i, v + 1, f'{v:.2f}', ha='center')
plt.tight_layout()
plt.savefig('../report/images/chrf_scores.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: chrF++ vs dev_bleu
plt.figure(figsize=(10, 6))
sns.scatterplot(x='dev_bleu', y='chrf_score', hue='script_family', size='test_size', 
                sizes=(100, 500), data=results_df)
plt.title('chrF++ Score vs Development BLEU')
plt.xlabel('Development BLEU (from registry)')
plt.ylabel('chrF++ Score')
plt.tight_layout()
plt.savefig('../report/images/chrf_vs_bleu.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Training curves for each benchmark
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, code in enumerate(results_df['benchmark']):
    if idx >= len(axes):
        break
    
    # Load model checkpoint
    checkpoint_path = f'../outputs/model_{code}.pt'
    if os.path.exists(checkpoint_path):
        checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
        train_losses = checkpoint['train_losses']
        val_losses = checkpoint['val_losses']
        
        ax = axes[idx]
        ax.plot(train_losses, label='Train Loss', alpha=0.7)
        ax.plot(val_losses, label='Val Loss', alpha=0.7)
        ax.set_title(f'{code} ({benchmarks[code]["script_family"]})')
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Loss')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
# Hide unused subplots
for idx in range(len(results_df), len(axes)):
    axes[idx].set_visible(False)

plt.suptitle('Training Curves for Each Benchmark', fontsize=16)
plt.tight_layout()
plt.savefig('../report/images/training_curves.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nPlots saved to report/images/")
