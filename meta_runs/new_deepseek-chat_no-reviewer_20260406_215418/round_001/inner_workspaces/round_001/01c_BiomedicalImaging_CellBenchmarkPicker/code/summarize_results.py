import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Load registry
with open('../data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)
registry_df = pd.DataFrame(registry['datasets'])
registry_df.set_index('dataset_id', inplace=True)

# Load results
mlp = pd.read_json('../outputs/mlp_results.json')
logistic = pd.read_json('../outputs/logistic_results.json')
regression = pd.read_json('../outputs/regression_results.json')
majority = pd.read_json('../outputs/majority_results.json')

# Create summary dataframe
datasets = ['D0014', 'D0010', 'D0009', 'D0008']
summary = []
for ds in datasets:
    sota = registry_df.loc[ds, 'published_dice_sota']
    mlp_row = mlp[mlp['dataset_id'] == ds].iloc[0]
    log_row = logistic[logistic['dataset_id'] == ds].iloc[0]
    reg_row = regression[regression['dataset_id'] == ds].iloc[0]
    maj_row = majority[majority['dataset_id'] == ds].iloc[0]
    
    summary.append({
        'dataset_id': ds,
        'published_dice_sota': sota,
        'mlp_macro_dice': mlp_row['macro_dice'],
        'logistic_macro_dice': log_row['macro_dice'],
        'regression_binary_dice': reg_row['dice'],
        'majority_macro_dice': maj_row['macro_dice'],
        'mlp_accuracy': mlp_row['accuracy'],
        'logistic_accuracy': log_row['accuracy'],
        'regression_accuracy': reg_row['accuracy'],
        'majority_accuracy': maj_row['accuracy'],
        'positive_pixel_rate': registry_df.loc[ds, 'positive_pixel_rate'],
        'train_patches': registry_df.loc[ds, 'train_patches']
    })

summary_df = pd.DataFrame(summary)
print("=== Results Summary ===")
print(summary_df.to_string(index=False))

# Save summary CSV
os.makedirs('../outputs', exist_ok=True)
summary_df.to_csv('../outputs/summary.csv', index=False)

# Plot 1: Comparison of Dice scores across datasets
plt.figure(figsize=(10, 6))
x = np.arange(len(datasets))
width = 0.15
plt.bar(x - 1.5*width, summary_df['published_dice_sota'], width, label='Published SOTA', color='gray')
plt.bar(x - 0.5*width, summary_df['mlp_macro_dice'], width, label='MLP (multiclass)', color='steelblue')
plt.bar(x + 0.5*width, summary_df['logistic_macro_dice'], width, label='Logistic Regression', color='orange')
plt.bar(x + 1.5*width, summary_df['regression_binary_dice'], width, label='Regression (binary)', color='green')
plt.bar(x + 2.5*width, summary_df['majority_macro_dice'], width, label='Majority Class', color='red')
plt.xlabel('Dataset')
plt.ylabel('Dice Score')
plt.title('Comparison of Dice Scores Across Datasets and Baselines')
plt.xticks(x, datasets)
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/dice_comparison.png', dpi=300)
print("Saved dice_comparison.png")

# Plot 2: Accuracy vs Dice for MLP
plt.figure(figsize=(8, 6))
plt.scatter(summary_df['mlp_accuracy'], summary_df['mlp_macro_dice'], s=100, label='MLP', alpha=0.7)
plt.scatter(summary_df['logistic_accuracy'], summary_df['logistic_macro_dice'], s=100, label='Logistic', alpha=0.7)
plt.scatter(summary_df['regression_accuracy'], summary_df['regression_binary_dice'], s=100, label='Regression', alpha=0.7)
plt.scatter(summary_df['majority_accuracy'], summary_df['majority_macro_dice'], s=100, label='Majority', alpha=0.7)
for i, row in summary_df.iterrows():
    plt.annotate(row['dataset_id'], (row['mlp_accuracy']+0.01, row['mlp_macro_dice']+0.01))
plt.xlabel('Accuracy')
plt.ylabel('Dice Score')
plt.title('Accuracy vs Dice Score for Different Baselines')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/accuracy_vs_dice.png', dpi=300)
print("Saved accuracy_vs_dice.png")

# Plot 3: Effect of positive_pixel_rate on performance
plt.figure(figsize=(10, 6))
plt.subplot(1, 2, 1)
plt.scatter(summary_df['positive_pixel_rate'], summary_df['mlp_macro_dice'], label='MLP Dice', color='steelblue')
plt.scatter(summary_df['positive_pixel_rate'], summary_df['logistic_macro_dice'], label='Logistic Dice', color='orange')
plt.xlabel('Positive Pixel Rate')
plt.ylabel('Dice Score')
plt.title('Dice vs Positive Pixel Rate')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.scatter(summary_df['positive_pixel_rate'], summary_df['mlp_accuracy'], label='MLP Accuracy', color='steelblue')
plt.scatter(summary_df['positive_pixel_rate'], summary_df['logistic_accuracy'], label='Logistic Accuracy', color='orange')
plt.xlabel('Positive Pixel Rate')
plt.ylabel('Accuracy')
plt.title('Accuracy vs Positive Pixel Rate')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/effect_positive_pixel_rate.png', dpi=300)
print("Saved effect_positive_pixel_rate.png")

print("\nAll plots saved to report/images/")
