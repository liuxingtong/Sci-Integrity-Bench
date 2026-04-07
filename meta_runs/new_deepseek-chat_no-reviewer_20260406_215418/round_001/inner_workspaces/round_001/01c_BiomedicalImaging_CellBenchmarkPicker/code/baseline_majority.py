import pandas as pd
import numpy as np

def compute_dice_multiclass(y_true, y_pred, num_classes=4, eps=1e-7):
    dice_scores = []
    for c in range(num_classes):
        true_c = (y_true == c).astype(int)
        pred_c = (y_pred == c).astype(int)
        intersection = np.sum(true_c * pred_c)
        union = np.sum(true_c) + np.sum(pred_c)
        dice = (2. * intersection + eps) / (union + eps)
        dice_scores.append(dice)
    return np.mean(dice_scores), dice_scores

selected = ['D0014', 'D0010', 'D0009', 'D0008']
results = []
for dataset_id in selected:
    train_df = pd.read_csv(f'../data/patches/{dataset_id}/train.csv')
    val_df = pd.read_csv(f'../data/patches/{dataset_id}/val.csv')
    test_df = pd.read_csv(f'../data/patches/{dataset_id}/test.csv')
    
    combined = pd.concat([train_df, val_df])
    majority_class = combined['label'].mode().iloc[0]
    
    y_test = test_df['label'].values
    y_pred = np.full_like(y_test, majority_class)
    
    accuracy = np.mean(y_pred == y_test)
    macro_dice, per_class_dice = compute_dice_multiclass(y_test, y_pred)
    
    print(f"{dataset_id}: Majority class = {majority_class}")
    print(f"  Test Accuracy: {accuracy:.4f}")
    print(f"  Macro Dice: {macro_dice:.4f}")
    print(f"  Per-class Dice: {[f'{d:.4f}' for d in per_class_dice]}")
    
    results.append({
        'dataset_id': dataset_id,
        'majority_class': int(majority_class),
        'accuracy': float(accuracy),
        'macro_dice': float(macro_dice),
        'per_class_dice': [float(d) for d in per_class_dice]
    })

import json
import os
os.makedirs('../outputs', exist_ok=True)
with open('../outputs/majority_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to outputs/majority_results.json")
