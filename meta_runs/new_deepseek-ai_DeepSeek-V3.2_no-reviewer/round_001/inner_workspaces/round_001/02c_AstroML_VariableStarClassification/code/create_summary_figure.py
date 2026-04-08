import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output directory
os.makedirs('../report/images', exist_ok=True)

# Load results from all experiments
experiments = [
    {'name': 'Basic Features + RF', 'val_acc': 0.5411, 'test_acc': 0.4726},
    {'name': 'Advanced Features + GB', 'val_acc': 0.5756, 'test_acc': 0.5132},
    {'name': 'N-gram Features + RF', 'val_acc': 0.5509, 'test_acc': 0.4780},
    {'name': 'Pattern Features + GB', 'val_acc': 0.5756, 'test_acc': 0.5132},
    {'name': 'Ensemble + RF', 'val_acc': 0.4724, 'test_acc': 0.4724},
    {'name': 'Baseline', 'val_acc': 0.7800, 'test_acc': 0.7800}
]

experiments_df = pd.DataFrame(experiments)

# Create summary figure
plt.figure(figsize=(14, 8))

# Plot 1: Performance comparison
plt.subplot(2, 2, 1)
x = np.arange(len(experiments_df))
width = 0.35

plt.bar(x - width/2, experiments_df['val_acc'], width, label='Validation', alpha=0.8, color='skyblue')
plt.bar(x + width/2, experiments_df['test_acc'], width, label='Test', alpha=0.8, color='lightcoral')
plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Random')
plt.xlabel('Model')
plt.ylabel('Balanced Accuracy')
plt.title('Model Performance Comparison')
plt.xticks(x, experiments_df['name'], rotation=45, ha='right')
plt.legend()
plt.grid(True, alpha=0.3, axis='y')
plt.ylim(0, 1.0)

# Plot 2: Performance gap to baseline
plt.subplot(2, 2, 2)
baseline = 0.78
gaps = baseline - experiments_df['test_acc'][:-1]  # Exclude baseline itself

plt.bar(range(len(gaps)), gaps, color='orange', alpha=0.7)
plt.xlabel('Model')
plt.ylabel('Gap to Baseline')
plt.title('Performance Gap to Baseline (0.78)')
plt.xticks(range(len(gaps)), experiments_df['name'][:-1], rotation=45, ha='right')
plt.grid(True, alpha=0.3, axis='y')

# Plot 3: Feature type comparison
feature_types = ['Basic', 'Advanced', 'N-gram', 'Pattern', 'Ensemble']
performance = [0.4726, 0.5132, 0.4780, 0.5132, 0.4724]

plt.subplot(2, 2, 3)
colors = plt.cm.Set3(np.linspace(0, 1, len(feature_types)))
plt.bar(feature_types, performance, color=colors, alpha=0.8)
plt.axhline(y=baseline, color='r', linestyle='--', label=f'Baseline ({baseline})')
plt.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, label='Random')
plt.xlabel('Feature Type')
plt.ylabel('Test Balanced Accuracy')
plt.title('Performance by Feature Type')
plt.legend()
plt.grid(True, alpha=0.3, axis='y')
plt.ylim(0, 1.0)

# Plot 4: Error analysis (from final model)
plt.subplot(2, 2, 4)
# Simulate error distribution based on confusion matrix
error_types = ['FN (0→1)', 'FP (1→0)']
error_counts = [44, 29]  # From best model confusion matrix
total_errors = sum(error_counts)

plt.pie(error_counts, labels=error_types, autopct='%1.1f%%', 
        colors=['lightcoral', 'skyblue'], startangle=90)
plt.title(f'Error Distribution\nTotal Errors: {total_errors}/150 ({total_errors/150*100:.1f}%)')

plt.tight_layout()
plt.savefig('../report/images/summary_figure.png', dpi=150, bbox_inches='tight')
plt.close()

print("Summary figure created and saved to report/images/summary_figure.png")

# Create a simple performance table for the report
print("\nPerformance Summary Table:")
print("="*80)
print(f"{'Model':<30} {'Val Bal. Acc':<15} {'Test Bal. Acc':<15} {'Gap to Baseline':<15}")
print("-"*80)

for _, row in experiments_df.iterrows():
    name = row['name']
    val_acc = row['val_acc']
    test_acc = row['test_acc']
    
    if name == 'Baseline':
        gap = 0.0
    else:
        gap = 0.78 - test_acc
    
    print(f"{name:<30} {val_acc:<15.4f} {test_acc:<15.4f} {gap:<15.4f}")

print("="*80)