#!/usr/bin/env python3
"""
Cell Patch Segmentation Benchmark Analysis
Trains MLP baselines on 4 datasets and reports hold-out Dice scores.
"""

import json
import os
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Select 4 diverse datasets based on registry characteristics
SELECTED_DATASETS = ['D0000', 'D0003', 'D0007', 'D0010']

def load_dataset(dataset_id, split='train'):
    """Load CSV data for a dataset split."""
    path = f'data/patches/{dataset_id}/{split}.csv'
    return pd.read_csv(path)

def calculate_dice_from_labels(y_true, y_pred):
    """
    Calculate Dice score for segmentation proxy.
    
    Since labels are foreground fraction buckets (0-3), we treat this as
    a binary segmentation proxy where:
    - label >= 1 indicates some foreground presence
    - label = 0 indicates background
    
    Dice = 2 * TP / (2 * TP + FP + FN)
    """
    # Convert to binary: foreground (label >= 1) vs background (label = 0)
    y_true_binary = (y_true >= 1).astype(int)
    y_pred_binary = (y_pred >= 1).astype(int)
    
    tp = np.sum((y_true_binary == 1) & (y_pred_binary == 1))
    fp = np.sum((y_true_binary == 0) & (y_pred_binary == 1))
    fn = np.sum((y_true_binary == 1) & (y_pred_binary == 0))
    
    if tp == 0 and fp == 0 and fn == 0:
        return 1.0  # Perfect prediction when no foreground exists
    
    dice = 2 * tp / (2 * tp + fp + fn)
    return dice

def calculate_multiclass_dice(y_true, y_pred, n_classes=4):
    """
    Calculate mean Dice across all classes (multi-class segmentation proxy).
    """
    dice_scores = []
    for c in range(n_classes):
        y_true_binary = (y_true == c).astype(int)
        y_pred_binary = (y_pred == c).astype(int)
        
        tp = np.sum((y_true_binary == 1) & (y_pred_binary == 1))
        fp = np.sum((y_true_binary == 0) & (y_pred_binary == 1))
        fn = np.sum((y_true_binary == 1) & (y_pred_binary == 0))
        
        if tp == 0 and fp == 0 and fn == 0:
            dice = 1.0
        else:
            dice = 2 * tp / (2 * tp + fp + fn)
        dice_scores.append(dice)
    
    return np.mean(dice_scores)

def train_and_evaluate(dataset_id):
    """Train MLP baseline and evaluate on test set."""
    print(f"Processing dataset: {dataset_id}")
    
    # Load data
    train_df = load_dataset(dataset_id, 'train')
    val_df = load_dataset(dataset_id, 'val')
    test_df = load_dataset(dataset_id, 'test')
    
    # Extract features and labels
    feature_cols = [f'feat_{i}' for i in range(32)]
    
    X_train = train_df[feature_cols].values
    y_train = train_df['label'].values
    
    X_val = val_df[feature_cols].values
    y_val = val_df['label'].values
    
    X_test = test_df[feature_cols].values
    y_test = test_df['label'].values
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Train MLP classifier
    mlp = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20
    )
    mlp.fit(X_train_scaled, y_train)
    
    # Evaluate on test set
    y_pred = mlp.predict(X_test_scaled)
    
    # Calculate Dice scores
    binary_dice = calculate_dice_from_labels(y_test, y_pred)
    multiclass_dice = calculate_multiclass_dice(y_test, y_pred)
    
    # Calculate accuracy for reference
    accuracy = np.mean(y_test == y_pred)
    
    results = {
        'dataset_id': dataset_id,
        'binary_dice': binary_dice,
        'multiclass_dice': multiclass_dice,
        'accuracy': accuracy,
        'n_train': len(X_train),
        'n_test': len(X_test),
        'y_pred': y_pred,
        'y_test': y_test
    }
    
    print(f"  Binary Dice: {binary_dice:.4f}")
    print(f"  Multi-class Dice: {multiclass_dice:.4f}")
    print(f"  Accuracy: {accuracy:.4f}")
    
    return results

def main():
    print("=" * 60)
    print("Cell Patch Segmentation Benchmark Analysis")
    print("=" * 60)
    
    # Load registry for metadata
    with open('data/cell_benchmark_registry.json', 'r') as f:
        registry = json.load(f)
    
    registry_dict = {d['dataset_id']: d for d in registry['datasets']}
    
    # Train and evaluate on selected datasets
    all_results = []
    for dataset_id in SELECTED_DATASETS:
        result = train_and_evaluate(dataset_id)
        result['published_dice_sota'] = registry_dict[dataset_id]['published_dice_sota']
        result['positive_pixel_rate'] = registry_dict[dataset_id]['positive_pixel_rate']
        result['train_patches'] = registry_dict[dataset_id]['train_patches']
        all_results.append(result)
    
    # Save results
    os.makedirs('outputs', exist_ok=True)
    
    # Save numerical results
    results_summary = []
    for r in all_results:
        results_summary.append({
            'dataset_id': r['dataset_id'],
            'binary_dice': r['binary_dice'],
            'multiclass_dice': r['multiclass_dice'],
            'accuracy': r['accuracy'],
            'published_dice_sota': r['published_dice_sota'],
            'positive_pixel_rate': r['positive_pixel_rate'],
            'train_patches': r['train_patches']
        })
    
    results_df = pd.DataFrame(results_summary)
    results_df.to_csv('outputs/results_summary.csv', index=False)
    print("\nResults saved to outputs/results_summary.csv")
    
    # Generate plots
    os.makedirs('report/images', exist_ok=True)
    
    # Plot 1: Binary Dice comparison
    plt.figure(figsize=(10, 6))
    datasets = [r['dataset_id'] for r in all_results]
    binary_dice = [r['binary_dice'] for r in all_results]
    published_dice = [r['published_dice_sota'] for r in all_results]
    
    x = np.arange(len(datasets))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width/2, binary_dice, width, label='MLP Baseline (Binary Dice)', color='#2E86AB')
    bars2 = ax.bar(x + width/2, published_dice, width, label='Published SOTA', color='#A23B72')
    
    ax.set_xlabel('Dataset ID', fontsize=12)
    ax.set_ylabel('Dice Score', fontsize=12)
    ax.set_title('Segmentation Performance: MLP Baseline vs Published SOTA', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.legend()
    ax.set_ylim(0, 1.0)
    
    # Add value labels
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
    plt.savefig('report/images/dice_comparison.png', dpi=150)
    plt.close()
    print("Saved: report/images/dice_comparison.png")
    
    # Plot 2: Multi-class Dice and Accuracy
    fig, ax = plt.subplots(figsize=(10, 6))
    multiclass_dice = [r['multiclass_dice'] for r in all_results]
    accuracy = [r['accuracy'] for r in all_results]
    
    x = np.arange(len(datasets))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, multiclass_dice, width, label='Multi-class Dice', color='#06A77D')
    bars2 = ax.bar(x + width/2, accuracy, width, label='Accuracy', color='#D62828')
    
    ax.set_xlabel('Dataset ID', fontsize=12)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('MLP Baseline: Multi-class Dice and Accuracy', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.legend()
    ax.set_ylim(0, 1.0)
    
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
    plt.savefig('report/images/multiclass_metrics.png', dpi=150)
    plt.close()
    print("Saved: report/images/multiclass_metrics.png")
    
    # Plot 3: Dice vs Positive Pixel Rate
    fig, ax = plt.subplots(figsize=(10, 6))
    positive_rates = [r['positive_pixel_rate'] for r in all_results]
    
    scatter = ax.scatter(positive_rates, binary_dice, s=100, c=range(len(datasets)), 
                         cmap='viridis', edgecolors='black', linewidth=1)
    
    for i, dataset_id in enumerate(datasets):
        ax.annotate(dataset_id, (positive_rates[i], binary_dice[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=10)
    
    ax.set_xlabel('Positive Pixel Rate', fontsize=12)
    ax.set_ylabel('Binary Dice Score', fontsize=12)
    ax.set_title('Relationship Between Positive Pixel Rate and Segmentation Performance', fontsize=14)
    ax.set_xlim(-0.05, 0.9)
    ax.set_ylim(0, 1.0)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/dice_vs_pixel_rate.png', dpi=150)
    plt.close()
    print("Saved: report/images/dice_vs_pixel_rate.png")
    
    # Plot 4: Confusion matrices for each dataset
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for idx, result in enumerate(all_results):
        cm = confusion_matrix(result['y_test'], result['y_pred'])
        # Normalize
        cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        
        sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues', 
                    ax=axes[idx], cbar=False,
                    xticklabels=[0, 1, 2, 3], yticklabels=[0, 1, 2, 3])
        axes[idx].set_xlabel('Predicted Label')
        axes[idx].set_ylabel('True Label')
        axes[idx].set_title(f'{result["dataset_id"]}\nBinary Dice: {result["binary_dice"]:.3f}')
    
    plt.suptitle('Confusion Matrices (Normalized) for Each Dataset', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig('report/images/confusion_matrices.png', dpi=150)
    plt.close()
    print("Saved: report/images/confusion_matrices.png")
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    
    return results_df

if __name__ == '__main__':
    main()
