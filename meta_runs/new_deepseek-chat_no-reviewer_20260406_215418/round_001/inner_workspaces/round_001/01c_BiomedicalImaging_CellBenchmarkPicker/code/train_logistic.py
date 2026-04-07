import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import json
import os

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

def train_logistic(dataset_id):
    print(f"\n=== Logistic Regression on {dataset_id} ===")
    train_df = pd.read_csv(f'../data/patches/{dataset_id}/train.csv')
    val_df = pd.read_csv(f'../data/patches/{dataset_id}/val.csv')
    test_df = pd.read_csv(f'../data/patches/{dataset_id}/test.csv')
    
    combined_df = pd.concat([train_df, val_df], ignore_index=True)
    
    X_train = combined_df.drop('label', axis=1).values.astype(np.float32)
    y_train = combined_df['label'].values.astype(np.int64)
    X_test = test_df.drop('label', axis=1).values.astype(np.float32)
    y_test = test_df['label'].values.astype(np.int64)
    
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Logistic regression with multinomial
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    macro_dice, per_class_dice = compute_dice_multiclass(y_test, y_pred)
    
    print(f"  Test Accuracy: {accuracy:.4f}")
    print(f"  Macro Dice: {macro_dice:.4f}")
    print(f"  Per-class Dice: {[f'{d:.4f}' for d in per_class_dice]}")
    
    return {
        'dataset_id': dataset_id,
        'accuracy': accuracy,
        'macro_dice': macro_dice,
        'per_class_dice': per_class_dice,
        'model': model,
        'scaler': scaler
    }

if __name__ == '__main__':
    selected = ['D0014', 'D0010', 'D0009', 'D0008']
    results = []
    for dataset_id in selected:
        res = train_logistic(dataset_id)
        results.append(res)
    
    print("\n=== Summary ===")
    for res in results:
        print(f"{res['dataset_id']}: Macro Dice = {res['macro_dice']:.4f}, Accuracy = {res['accuracy']:.4f}")
    
    os.makedirs('../outputs', exist_ok=True)
    with open('../outputs/logistic_results.json', 'w') as f:
        json_data = []
        for res in results:
            json_data.append({
                'dataset_id': res['dataset_id'],
                'accuracy': float(res['accuracy']),
                'macro_dice': float(res['macro_dice']),
                'per_class_dice': [float(d) for d in res['per_class_dice']]
            })
        json.dump(json_data, f, indent=2)
    print("\nResults saved to outputs/logistic_results.json")
