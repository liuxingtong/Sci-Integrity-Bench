"""
Visualization script for cell patch segmentation benchmark results.
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

def main():
    # Load results
    results_df = pd.read_csv('outputs/results_summary.csv')
    
    # Load registry for comparison
    with open('data/cell_benchmark_registry.json', 'r') as f:
        registry = json.load(f)
    registry_df = pd.DataFrame(registry['datasets'])
    
    # Create images directory
    os.makedirs('report/images', exist_ok=True)
    
    # Figure 1: Dice Score Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(results_df))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, results_df['dice'], width, label='MLP Baseline (Ours)', color='steelblue', alpha=0.8)
    bars2 = ax.bar(x + width/2, results_df['published_dice_sota'], width, label='Published SOTA', color='coral', alpha=0.8)
    
    ax.set_xlabel('Dataset ID', fontsize=12)
    ax.set_ylabel('Dice Score', fontsize=12)
    ax.set_title('Hold-out Dice Score: MLP Baseline vs Published SOTA', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(results_df['dataset_id'])
    ax.legend(loc='upper left')
    ax.set_ylim(0, 1.0)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('report/images/dice_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/dice_comparison.png")
    
    # Figure 2: Performance vs Training Size
    fig, ax = plt.subplots(figsize=(10, 6))
    
    scatter = ax.scatter(results_df['train_patches'], results_df['dice'], 
                         s=200, c=results_df['positive_pixel_rate'], cmap='viridis', 
                         alpha=0.8, edgecolors='black', linewidth=1)
    
    # Add dataset labels
    for i, row in results_df.iterrows():
        ax.annotate(row['dataset_id'], 
                    (row['train_patches'], row['dice']),
                    textcoords="offset points", xytext=(10, 5),
                    ha='left', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Training Patches', fontsize=12)
    ax.set_ylabel('Dice Score', fontsize=12)
    ax.set_title('MLP Baseline Performance vs Training Data Size', fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Positive Pixel Rate', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('report/images/performance_vs_size.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/performance_vs_size.png")
    
    # Figure 3: Performance metrics breakdown
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    
    metrics = ['accuracy', 'f1_macro', 'dice']
    titles = ['Accuracy', 'F1 Macro', 'Dice Score']
    colors = ['#3498db', '#2ecc71', '#9b59b6']
    
    for idx, (metric, title, color) in enumerate(zip(metrics, titles, colors)):
        ax = axes[idx]
        bars = ax.bar(results_df['dataset_id'], results_df[metric], color=color, alpha=0.8, edgecolor='black')
        ax.set_xlabel('Dataset ID', fontsize=11)
        ax.set_ylabel(title, fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_ylim(0, 1.0)
        
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
    
    plt.suptitle('Performance Metrics Breakdown Across Datasets', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('report/images/metrics_breakdown.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/metrics_breakdown.png")
    
    # Figure 4: Dataset characteristics overview
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Training patches distribution
    ax1 = axes[0]
    all_data = registry_df.sort_values('train_patches')
    colors = ['steelblue' if d in results_df['dataset_id'].values else 'lightgray' for d in all_data['dataset_id']]
    ax1.barh(all_data['dataset_id'], all_data['train_patches'], color=colors, edgecolor='black')
    ax1.set_xlabel('Training Patches', fontsize=11)
    ax1.set_ylabel('Dataset ID', fontsize=11)
    ax1.set_title('Training Data Size (Selected datasets in blue)', fontsize=12, fontweight='bold')
    
    # Positive pixel rate distribution
    ax2 = axes[1]
    colors = ['coral' if d in results_df['dataset_id'].values else 'lightgray' for d in all_data['dataset_id']]
    ax2.barh(all_data['dataset_id'], all_data['positive_pixel_rate'], color=colors, edgecolor='black')
    ax2.set_xlabel('Positive Pixel Rate', fontsize=11)
    ax2.set_ylabel('Dataset ID', fontsize=11)
    ax2.set_title('Positive Pixel Rate (Selected datasets in coral)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('report/images/dataset_characteristics.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/dataset_characteristics.png")
    
    # Figure 5: Gap analysis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    results_df['gap'] = results_df['published_dice_sota'] - results_df['dice']
    
    bars = ax.bar(results_df['dataset_id'], results_df['gap'], color='indianred', alpha=0.8, edgecolor='black')
    ax.set_xlabel('Dataset ID', fontsize=12)
    ax.set_ylabel('Dice Score Gap', fontsize=12)
    ax.set_title('Gap Between MLP Baseline and Published SOTA', fontsize=14, fontweight='bold')
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('report/images/gap_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/gap_analysis.png")
    
    print("\nAll visualizations saved successfully!")

if __name__ == '__main__':
    main()