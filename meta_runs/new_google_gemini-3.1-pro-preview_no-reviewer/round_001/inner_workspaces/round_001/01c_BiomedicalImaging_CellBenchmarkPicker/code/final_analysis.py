import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import seaborn as sns

# Selected datasets based on diversity in SOTA Dice and positive pixel rate
selected_datasets = ['D0001', 'D0002', 'D0007', 'D0014']

def pseudo_dice(y_true, y_pred):
    # y_true and y_pred are fractions (0, 0.333, 0.667, 1.0)
    intersection = np.minimum(y_true, y_pred).sum()
    total_size = y_true.sum() + y_pred.sum()
    if total_size == 0:
        return 1.0
    return 2 * intersection / total_size

results = []

for ds in selected_datasets:
    train_df = pd.read_csv(f'data/patches/{ds}/train.csv')
    val_df = pd.read_csv(f'data/patches/{ds}/val.csv')
    test_df = pd.read_csv(f'data/patches/{ds}/test.csv')
    
    X_train = train_df.drop(columns=['label'])
    y_train_class = train_df['label']
    
    X_val = val_df.drop(columns=['label'])
    y_val_class = val_df['label']
    y_val_frac = val_df['label'] / 3.0
    
    X_test = test_df.drop(columns=['label'])
    y_test_class = test_df['label']
    y_test_frac = test_df['label'] / 3.0
    
    # Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train_class)
    
    # Predict and convert to fractions
    val_pred_frac = rf.predict(X_val) / 3.0
    test_pred_frac = rf.predict(X_test) / 3.0
    
    val_dice = pseudo_dice(y_val_frac, val_pred_frac)
    test_dice = pseudo_dice(y_test_frac, test_pred_frac)
    
    results.append({
        'Dataset': ds,
        'Validation Dice': val_dice,
        'Test Dice': test_dice
    })

results_df = pd.DataFrame(results)
print("Results:")
print(results_df)
results_df.to_csv('outputs/final_results.csv', index=False)

# Plotting
plt.figure(figsize=(8, 5))
sns.barplot(data=results_df.melt(id_vars='Dataset', value_vars=['Validation Dice', 'Test Dice']),
            x='Dataset', y='value', hue='variable', palette='viridis')
plt.title('Random Forest Baseline: Pseudo-Dice Score by Dataset')
plt.ylabel('Pseudo-Dice Score')
plt.ylim(0, 1)
plt.legend(title='Split')
plt.tight_layout()
plt.savefig('report/images/rf_dice_scores.png')
plt.close()

# Also plot the metadata for these datasets to show diversity
with open('data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)['datasets']

meta_df = pd.DataFrame([d for d in registry if d['dataset_id'] in selected_datasets])

fig, ax1 = plt.subplots(figsize=(8, 5))

color = 'tab:blue'
ax1.set_xlabel('Dataset')
ax1.set_ylabel('Published SOTA Dice', color=color)
ax1.bar(meta_df['dataset_id'], meta_df['published_dice_sota'], color=color, alpha=0.6, label='SOTA Dice')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_ylim(0, 1)

ax2 = ax1.twinx()  
color = 'tab:red'
ax2.set_ylabel('Positive Pixel Rate', color=color)  
ax2.plot(meta_df['dataset_id'], meta_df['positive_pixel_rate'], color=color, marker='o', linewidth=2, label='Pos Pixel Rate')
ax2.tick_params(axis='y', labelcolor=color)
ax2.set_ylim(0, 1)

fig.tight_layout()  
plt.title('Metadata of Selected Datasets')
plt.savefig('report/images/dataset_metadata.png')
plt.close()
