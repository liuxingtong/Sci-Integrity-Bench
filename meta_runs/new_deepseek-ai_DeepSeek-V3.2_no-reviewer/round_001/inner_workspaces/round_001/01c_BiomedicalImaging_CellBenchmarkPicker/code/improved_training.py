import pandas as pd
import numpy as np
import json
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
import matplotlib.pyplot as plt

# Dice function
def multiclass_dice_score(y_true, y_pred, n_classes=4):
    dice_scores = []
    for class_idx in range(n_classes):
        true_binary = (y_true == class_idx).astype(int)
        pred_binary = (y_pred == class_idx).astype(int)
        
        intersection = np.sum(true_binary * pred_binary)
        union = np.sum(true_binary) + np.sum(pred_binary)
        
        if union == 0:
            dice = 1.0
        else:
            dice = 2.0 * intersection / union
        dice_scores.append(dice)
    return np.mean(dice_scores)

# Selected datasets
selected_datasets = ['D0000', 'D0001', 'D0002', 'D0013']

# Load registry
with open('data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)

datasets_info = {ds['dataset_id']: ds for ds in registry['datasets']}

# Store results
results = []

for dataset_id in selected_datasets:
    print(f"\n=== Dataset {dataset_id} ===")
    
    # Load data
    train_df = pd.read_csv(f'data/patches/{dataset_id}/train.csv')
    val_df = pd.read_csv(f'data/patches/{dataset_id}/val.csv')
    test_df = pd.read_csv(f'data/patches/{dataset_id}/test.csv')
    
    # Combine train and val for cross-validation (small data)
    X_trainval = pd.concat([train_df.drop('label', axis=1), val_df.drop('label', axis=1)])
    y_trainval = pd.concat([train_df['label'], val_df['label']])
    
    X_test = test_df.drop('label', axis=1).values
    y_test = test_df['label'].values
    
    # Standardize
    scaler = StandardScaler()
    X_trainval_scaled = scaler.fit_transform(X_trainval)
    X_test_scaled = scaler.transform(X_test)
    
    # Try different models with regularization
    models = {
        'Logistic_Reg_C1': LogisticRegression(C=1.0, max_iter=1000, random_state=42),
        'Logistic_Reg_C0.1': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
        'MLP_Reg': MLPClassifier(hidden_layer_sizes=(32, 16), alpha=0.1, max_iter=1000, 
                                 random_state=42, early_stopping=True),
        'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
    }
    
    # 5-fold cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    best_model = None
    best_score = 0
    best_name = ''
    
    for name, model in models.items():
        # Cross-validation
        cv_scores = cross_val_score(model, X_trainval_scaled, y_trainval, 
                                   cv=cv, scoring='accuracy')
        mean_cv = np.mean(cv_scores)
        std_cv = np.std(cv_scores)
        
        print(f"{name}: CV accuracy = {mean_cv:.3f} ± {std_cv:.3f}")
        
        if mean_cv > best_score:
            best_score = mean_cv
            best_model = model
            best_name = name
    
    # Train best model on all train+val data
    best_model.fit(X_trainval_scaled, y_trainval)
    
    # Predict on test
    y_test_pred = best_model.predict(X_test_scaled)
    
    # Calculate metrics
    test_acc = np.mean(y_test == y_test_pred)
    test_dice = multiclass_dice_score(y_test, y_test_pred)
    
    sota_dice = datasets_info[dataset_id]['published_dice_sota']
    
    print(f"Best model: {best_name}")
    print(f"Test accuracy: {test_acc:.3f}")
    print(f"Test Dice: {test_dice:.3f}")
    print(f"Published SOTA Dice: {sota_dice:.3f}")
    
    results.append({
        'dataset_id': dataset_id,
        'best_model': best_name,
        'test_accuracy': test_acc,
        'test_dice': test_dice,
        'published_sota_dice': sota_dice,
        'positive_pixel_rate': datasets_info[dataset_id]['positive_pixel_rate'],
        'train_patches': datasets_info[dataset_id]['train_patches']
    })

# Create results DataFrame
results_df = pd.DataFrame(results)
print("\n=== Final Results ===")
print(results_df.to_string())

# Save results
results_df.to_csv('outputs/improved_results.csv', index=False)

# Visualization
plt.figure(figsize=(10, 6))
x = np.arange(len(selected_datasets))
width = 0.35

plt.bar(x - width/2, results_df['test_dice'], width, label='Our Best Model', alpha=0.8)
plt.bar(x + width/2, results_df['published_sota_dice'], width, label='Published SOTA', alpha=0.8)

plt.xlabel('Dataset')
plt.ylabel('Dice Score')
plt.title('Improved Model: Dice Score Comparison')
plt.xticks(x, selected_datasets)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/improved_dice_comparison.png', dpi=150)
plt.close()

print("\nVisualization saved to report/images/improved_dice_comparison.png")