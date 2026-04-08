import pandas as pd
import numpy as np
import json
import os
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns

# Define Dice coefficient function for multiclass
def multiclass_dice_score(y_true, y_pred, n_classes=4):
    """Compute Dice score for multiclass classification."""
    dice_scores = []
    for class_idx in range(n_classes):
        true_binary = (y_true == class_idx).astype(int)
        pred_binary = (y_pred == class_idx).astype(int)
        
        intersection = np.sum(true_binary * pred_binary)
        union = np.sum(true_binary) + np.sum(pred_binary)
        
        if union == 0:
            dice = 1.0  # Both empty
        else:
            dice = 2.0 * intersection / union
        dice_scores.append(dice)
    
    # Return macro average Dice
    return np.mean(dice_scores)

# Selected datasets
selected_datasets = ['D0000', 'D0001', 'D0002', 'D0013']

# Load registry
with open('data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)

datasets_info = {ds['dataset_id']: ds for ds in registry['datasets']}

# Store results
results = []

# Create output directory
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Train model for each dataset
for dataset_id in selected_datasets:
    print(f"\n=== Training on dataset {dataset_id} ===")
    
    # Load data
    train_path = f'data/patches/{dataset_id}/train.csv'
    val_path = f'data/patches/{dataset_id}/val.csv'
    test_path = f'data/patches/{dataset_id}/test.csv'
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    # Prepare features and labels
    X_train = train_df.drop('label', axis=1).values
    y_train = train_df['label'].values
    
    X_val = val_df.drop('label', axis=1).values
    y_val = val_df['label'].values
    
    X_test = test_df.drop('label', axis=1).values
    y_test = test_df['label'].values
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Train MLP classifier
    # Small MLP for small dataset
    mlp = MLPClassifier(
        hidden_layer_sizes=(32, 16),  # Two hidden layers
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.2,
        n_iter_no_change=20
    )
    
    mlp.fit(X_train_scaled, y_train)
    
    # Predictions
    y_train_pred = mlp.predict(X_train_scaled)
    y_val_pred = mlp.predict(X_val_scaled)
    y_test_pred = mlp.predict(X_test_scaled)
    
    # Calculate metrics
    train_acc = accuracy_score(y_train, y_train_pred)
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    train_f1 = f1_score(y_train, y_train_pred, average='macro')
    val_f1 = f1_score(y_val, y_val_pred, average='macro')
    test_f1 = f1_score(y_test, y_test_pred, average='macro')
    
    train_dice = multiclass_dice_score(y_train, y_train_pred)
    val_dice = multiclass_dice_score(y_val, y_val_pred)
    test_dice = multiclass_dice_score(y_test, y_test_pred)
    
    # Get dataset info
    info = datasets_info[dataset_id]
    sota_dice = info['published_dice_sota']
    
    print(f"Train accuracy: {train_acc:.3f}")
    print(f"Val accuracy: {val_acc:.3f}")
    print(f"Test accuracy: {test_acc:.3f}")
    print(f"Train Dice: {train_dice:.3f}")
    print(f"Val Dice: {val_dice:.3f}")
    print(f"Test Dice: {test_dice:.3f}")
    print(f"Published SOTA Dice: {sota_dice:.3f}")
    
    # Store results
    results.append({
        'dataset_id': dataset_id,
        'train_samples': len(X_train),
        'val_samples': len(X_val),
        'test_samples': len(X_test),
        'train_accuracy': train_acc,
        'val_accuracy': val_acc,
        'test_accuracy': test_acc,
        'train_dice': train_dice,
        'val_dice': val_dice,
        'test_dice': test_dice,
        'published_sota_dice': sota_dice,
        'positive_pixel_rate': info['positive_pixel_rate'],
        'train_patches': info['train_patches']
    })
    
    # Save predictions for analysis
    pred_df = pd.DataFrame({
        'true': y_test,
        'pred': y_test_pred
    })
    pred_df.to_csv(f'outputs/{dataset_id}_predictions.csv', index=False)

# Convert results to DataFrame
results_df = pd.DataFrame(results)
print("\n=== Summary Results ===")
print(results_df.to_string())

# Save results
results_df.to_csv('outputs/mlp_baseline_results.csv', index=False)

# Create visualization
plt.figure(figsize=(10, 6))

# Bar plot of Dice scores
x = np.arange(len(selected_datasets))
width = 0.35

plt.bar(x - width/2, results_df['test_dice'], width, label='Our MLP (Test)', alpha=0.8)
plt.bar(x + width/2, results_df['published_sota_dice'], width, label='Published SOTA', alpha=0.8)

plt.xlabel('Dataset')
plt.ylabel('Dice Score')
plt.title('Dice Score Comparison: Our MLP vs Published SOTA')
plt.xticks(x, selected_datasets)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/dice_comparison.png', dpi=150)
plt.close()

# Create scatter plot: Positive pixel rate vs Dice score
plt.figure(figsize=(8, 6))
plt.scatter(results_df['positive_pixel_rate'], results_df['test_dice'], 
            s=100, alpha=0.7, label='Our MLP (Test)')
plt.scatter(results_df['positive_pixel_rate'], results_df['published_sota_dice'], 
            s=100, alpha=0.7, label='Published SOTA', marker='s')

for i, row in results_df.iterrows():
    plt.annotate(row['dataset_id'], 
                 (row['positive_pixel_rate'], row['test_dice']),
                 xytext=(5, 5), textcoords='offset points')

plt.xlabel('Positive Pixel Rate')
plt.ylabel('Dice Score')
plt.title('Dice Score vs Positive Pixel Rate')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/dice_vs_positive_rate.png', dpi=150)
plt.close()

print("\nVisualizations saved to report/images/")