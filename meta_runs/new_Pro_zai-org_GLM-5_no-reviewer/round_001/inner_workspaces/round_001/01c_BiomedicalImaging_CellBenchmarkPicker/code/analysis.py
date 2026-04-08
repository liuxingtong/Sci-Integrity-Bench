"""
Cell Patch Segmentation Benchmark Analysis
Trains MLP baselines on 4 selected datasets and reports hold-out Dice scores.
"""

import json
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, f1_score
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

def load_dataset(dataset_id, base_path='data/patches'):
    """Load train, val, and test splits for a dataset."""
    train_df = pd.read_csv(f'{base_path}/{dataset_id}/train.csv')
    val_df = pd.read_csv(f'{base_path}/{dataset_id}/val.csv')
    test_df = pd.read_csv(f'{base_path}/{dataset_id}/test.csv')
    return train_df, val_df, test_df

def prepare_data(train_df, val_df, test_df):
    """Prepare features and labels for training."""
    feature_cols = [col for col in train_df.columns if col.startswith('feat_')]
    
    X_train = train_df[feature_cols].values
    y_train = train_df['label'].values
    
    X_val = val_df[feature_cols].values
    y_val = val_df['label'].values
    
    X_test = test_df[feature_cols].values
    y_test = test_df['label'].values
    
    # Standardize features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def compute_dice_score(y_true, y_pred, num_classes=4):
    """
    Compute macro-averaged Dice score for multi-class classification.
    Dice = 2 * |X ∩ Y| / (|X| + |Y|)
    For classification, we use: Dice = 2*TP / (2*TP + FP + FN)
    """
    dice_scores = []
    for c in range(num_classes):
        true_binary = (y_true == c).astype(int)
        pred_binary = (y_pred == c).astype(int)
        
        tp = np.sum(true_binary * pred_binary)
        fp = np.sum(pred_binary) - tp
        fn = np.sum(true_binary) - tp
        
        if tp + fp + fn == 0:
            dice = 1.0  # Perfect score if class not present and not predicted
        else:
            dice = 2 * tp / (2 * tp + fp + fn)
        dice_scores.append(dice)
    
    return np.mean(dice_scores)

def train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test, dataset_id):
    """Train MLP classifier and evaluate on test set."""
    # Combine train and validation for final training
    X_train_full = np.vstack([X_train, X_val])
    y_train_full = np.concatenate([y_train, y_val])
    
    # Define MLP architecture (same family for all datasets)
    # Using a simple 2-layer MLP with ReLU activation
    mlp = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        verbose=False
    )
    
    # Train the model
    mlp.fit(X_train_full, y_train_full)
    
    # Predict on test set
    y_pred = mlp.predict(X_test)
    
    # Compute metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    dice = compute_dice_score(y_test, y_pred)
    
    return {
        'dataset_id': dataset_id,
        'accuracy': accuracy,
        'f1_macro': f1_macro,
        'dice': dice,
        'y_test': y_test,
        'y_pred': y_pred
    }

def main():
    # Load registry
    with open('data/cell_benchmark_registry.json', 'r') as f:
        registry = json.load(f)
    
    # Create dataframe for easier analysis
    df_registry = pd.DataFrame(registry['datasets'])
    print("Dataset Registry Summary:")
    print(df_registry.to_string())
    print("\n")
    
    # Select 4 diverse datasets:
    # - D0000: Small training size, moderate positive rate
    # - D0003: Medium training size, high positive rate
    # - D0007: Larger training size, medium positive rate
    # - D0013: Large training size, medium positive rate, high SOTA
    selected_datasets = ['D0000', 'D0003', 'D0007', 'D0013']
    
    print(f"Selected datasets: {selected_datasets}")
    print("\nSelected dataset characteristics:")
    selected_df = df_registry[df_registry['dataset_id'].isin(selected_datasets)]
    print(selected_df.to_string())
    print("\n")
    
    # Train and evaluate on each dataset
    results = []
    for dataset_id in selected_datasets:
        print(f"Processing {dataset_id}...")
        
        # Load data
        train_df, val_df, test_df = load_dataset(dataset_id)
        print(f"  Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        
        # Prepare data
        X_train, y_train, X_val, y_val, X_test, y_test = prepare_data(train_df, val_df, test_df)
        
        # Train and evaluate
        result = train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test, dataset_id)
        results.append(result)
        
        print(f"  Accuracy: {result['accuracy']:.4f}")
        print(f"  F1 Macro: {result['f1_macro']:.4f}")
        print(f"  Dice Score: {result['dice']:.4f}")
        print()
    
    # Create results summary
    results_summary = pd.DataFrame([{
        'dataset_id': r['dataset_id'],
        'accuracy': r['accuracy'],
        'f1_macro': r['f1_macro'],
        'dice': r['dice']
    } for r in results])
    
    # Merge with registry info
    results_summary = results_summary.merge(df_registry, on='dataset_id')
    
    print("\n" + "="*60)
    print("FINAL RESULTS SUMMARY")
    print("="*60)
    print(results_summary.to_string())
    
    # Save results
    os.makedirs('outputs', exist_ok=True)
    results_summary.to_csv('outputs/results_summary.csv', index=False)
    
    # Save detailed results
    with open('outputs/detailed_results.json', 'w') as f:
        json.dump([{
            'dataset_id': r['dataset_id'],
            'accuracy': r['accuracy'],
            'f1_macro': r['f1_macro'],
            'dice': r['dice']
        } for r in results], f, indent=2)
    
    print("\nResults saved to outputs/")
    
    return results_summary

if __name__ == '__main__':
    results = main()