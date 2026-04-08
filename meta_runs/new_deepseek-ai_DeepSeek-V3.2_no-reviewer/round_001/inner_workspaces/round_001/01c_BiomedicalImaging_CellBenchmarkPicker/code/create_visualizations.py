import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os
import json

# Create visualizations for the report
os.makedirs('report/images', exist_ok=True)

# 1. Dataset characteristics from registry
registry_path = 'data/cell_benchmark_registry.json'
with open(registry_path, 'r') as f:
    registry = pd.DataFrame(json.load(f)['datasets'])

plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
plt.scatter(registry['train_patches'], registry['published_dice_sota'], alpha=0.7)
plt.xlabel('Train Patches')
plt.ylabel('Published SOTA Dice')
plt.title('SOTA Dice vs Dataset Size')
plt.grid(True, alpha=0.3)

plt.subplot(1, 3, 2)
plt.scatter(registry['positive_pixel_rate'], registry['published_dice_sota'], alpha=0.7)
plt.xlabel('Positive Pixel Rate')
plt.ylabel('Published SOTA Dice')
plt.title('SOTA Dice vs Positive Rate')
plt.grid(True, alpha=0.3)

plt.subplot(1, 3, 3)
plt.hist(registry['published_dice_sota'], bins=10, alpha=0.7, edgecolor='black')
plt.xlabel('Published SOTA Dice')
plt.ylabel('Count')
plt.title('Distribution of SOTA Dice Scores')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/dataset_characteristics.png', dpi=150)
plt.close()

# 2. Feature visualization for one dataset
dataset_id = 'D0000'
train_df = pd.read_csv(f'data/patches/{dataset_id}/train.csv')

plt.figure(figsize=(10, 6))

# Feature distributions by class
for class_label in range(4):
    class_data = train_df[train_df['label'] == class_label].drop('label', axis=1)
    plt.hist(class_data.values.flatten(), bins=30, alpha=0.5, 
             label=f'Class {class_label}', density=True)

plt.xlabel('Feature Value')
plt.ylabel('Density')
plt.title(f'Feature Distributions by Class ({dataset_id})')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/feature_distributions.png', dpi=150)
plt.close()

# 3. PCA visualization for all selected datasets
selected_datasets = ['D0000', 'D0001', 'D0002', 'D0013']

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

for idx, dataset_id in enumerate(selected_datasets):
    train_df = pd.read_csv(f'data/patches/{dataset_id}/train.csv')
    
    X = train_df.drop('label', axis=1).values
    y = train_df['label'].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    ax = axes[idx]
    scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=y, cmap='viridis', alpha=0.7)
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
    ax.set_title(f'{dataset_id} - PCA (Total: {sum(pca.explained_variance_ratio_):.1%})')
    ax.grid(True, alpha=0.3)
    
    # Add colorbar
    if idx == 3:
        plt.colorbar(scatter, ax=ax, label='Class Label')

plt.tight_layout()
plt.savefig('report/images/pca_visualization.png', dpi=150)
plt.close()

# 4. Load our results and create comparison plot
results_path = 'outputs/improved_results.csv'
if os.path.exists(results_path):
    results_df = pd.read_csv(results_path)
    
    plt.figure(figsize=(10, 6))
    
    x = np.arange(len(results_df))
    width = 0.35
    
    bars1 = plt.bar(x - width/2, results_df['test_dice'], width, 
                   label='Our Baseline (Test)', alpha=0.8, color='steelblue')
    bars2 = plt.bar(x + width/2, results_df['published_sota_dice'], width, 
                   label='Published SOTA', alpha=0.8, color='darkorange')
    
    plt.xlabel('Dataset')
    plt.ylabel('Dice Score')
    plt.title('Cell Patch Segmentation: Baseline vs SOTA Performance')
    plt.xticks(x, results_df['dataset_id'])
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    def autolabel(bars):
        for bar in bars:
            height = bar.get_height()
            plt.annotate(f'{height:.3f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
    
    autolabel(bars1)
    autolabel(bars2)
    
    plt.tight_layout()
    plt.savefig('report/images/final_comparison.png', dpi=150)
    plt.close()

print("Visualizations created in report/images/")