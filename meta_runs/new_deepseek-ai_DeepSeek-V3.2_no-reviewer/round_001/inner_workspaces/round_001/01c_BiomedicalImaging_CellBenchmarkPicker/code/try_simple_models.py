import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

# Reuse Dice function
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

# Test on D0000
dataset_id = 'D0000'
train_df = pd.read_csv(f'data/patches/{dataset_id}/train.csv')
val_df = pd.read_csv(f'data/patches/{dataset_id}/val.csv')
test_df = pd.read_csv(f'data/patches/{dataset_id}/test.csv')

X_train = train_df.drop('label', axis=1).values
y_train = train_df['label'].values
X_val = val_df.drop('label', axis=1).values
y_val = val_df['label'].values
X_test = test_df.drop('label', axis=1).values
y_test = test_df['label'].values

# Standardize
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

print(f"Dataset: {dataset_id}")
print(f"Training set shape: {X_train.shape}")
print(f"Class distribution in train: {np.bincount(y_train)}")
print(f"Class distribution in test: {np.bincount(y_test)}")

# Try different models
models = {
    'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
    'MLP_small': MLPClassifier(hidden_layer_sizes=(16,), max_iter=500, random_state=42),
    'MLP_medium': MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500, random_state=42),
    'MLP_large': MLPClassifier(hidden_layer_sizes=(64, 32, 16), max_iter=500, random_state=42),
}

results = []
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    train_dice = multiclass_dice_score(y_train, y_train_pred)
    test_dice = multiclass_dice_score(y_test, y_test_pred)
    
    results.append({
        'model': name,
        'train_acc': train_acc,
        'test_acc': test_acc,
        'train_dice': train_dice,
        'test_dice': test_dice
    })
    
    print(f"\n{name}:")
    print(f"  Train accuracy: {train_acc:.3f}")
    print(f"  Test accuracy: {test_acc:.3f}")
    print(f"  Train Dice: {train_dice:.3f}")
    print(f"  Test Dice: {test_dice:.3f}")

# Also check if random guessing baseline
print("\nRandom guessing (proportional to class distribution):")
class_probs = np.bincount(y_train) / len(y_train)
random_preds = np.random.choice([0,1,2,3], size=len(y_test), p=class_probs)
random_acc = accuracy_score(y_test, random_preds)
random_dice = multiclass_dice_score(y_test, random_preds)
print(f"  Expected test accuracy: {random_acc:.3f}")
print(f"  Expected test Dice: {random_dice:.3f}")

# Majority class baseline
majority_class = np.argmax(np.bincount(y_train))
majority_preds = np.full(len(y_test), majority_class)
majority_acc = accuracy_score(y_test, majority_preds)
majority_dice = multiclass_dice_score(y_test, majority_preds)
print(f"\nMajority class baseline (class {majority_class}):")
print(f"  Test accuracy: {majority_acc:.3f}")
print(f"  Test Dice: {majority_dice:.3f}")