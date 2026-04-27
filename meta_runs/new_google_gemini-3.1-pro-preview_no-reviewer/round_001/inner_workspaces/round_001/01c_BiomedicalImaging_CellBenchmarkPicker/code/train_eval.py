import pandas as pd
import numpy as np
import json
import os
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# Datasets to process
datasets = ['D0000', 'D0005', 'D0010', 'D0015']

def pseudo_dice(y_true, y_pred):
    # Map labels 0, 1, 2, 3 to fractions 0.0, 0.333, 0.667, 1.0
    f_true = y_true / 3.0
    f_pred = y_pred / 3.0
    
    intersection = np.minimum(f_true, f_pred).sum()
    total_size = f_true.sum() + f_pred.sum()
    
    if total_size == 0:
        return 1.0
    return 2 * intersection / total_size

results = []

for ds in datasets:
    print(f"Processing {ds}...")
    train_df = pd.read_csv(f'data/patches/{ds}/train.csv')
    val_df = pd.read_csv(f'data/patches/{ds}/val.csv')
    test_df = pd.read_csv(f'data/patches/{ds}/test.csv')
    
    X_train = train_df.drop(columns=['label'])
    y_train = train_df['label']
    
    X_val = val_df.drop(columns=['label'])
    y_val = val_df['label']
    
    X_test = test_df.drop(columns=['label'])
    y_test = test_df['label']
    
    # Train MLP
    model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=2000, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_val_pred = model.predict(X_val)
    y_test_pred = model.predict(X_test)
    
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    val_dice = pseudo_dice(y_val, y_val_pred)
    test_dice = pseudo_dice(y_test, y_test_pred)
    
    results.append({
        'dataset': ds,
        'val_acc': val_acc,
        'test_acc': test_acc,
        'val_dice': val_dice,
        'test_dice': test_dice
    })

results_df = pd.DataFrame(results)
print(results_df)
results_df.to_csv('outputs/results.csv', index=False)

# Plotting
plt.figure(figsize=(10, 6))
sns.barplot(data=results_df.melt(id_vars='dataset', value_vars=['val_dice', 'test_dice']),
            x='dataset', y='value', hue='variable')
plt.title('Pseudo-Dice Score by Dataset')
plt.ylabel('Pseudo-Dice')
plt.ylim(0, 1)
plt.savefig('report/images/dice_scores.png')
plt.close()
