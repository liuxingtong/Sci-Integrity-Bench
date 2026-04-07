import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

# Prepare sequences
chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {char: i+1 for i, char in enumerate(chars)}  # 0 is for padding
max_len = 20  # All sequences are length 20

# Convert sequences to indices
def seq_to_indices(seqs):
    indices = []
    for seq in seqs:
        idx_seq = [char_to_idx[char] for char in seq]
        indices.append(idx_seq)
    return np.array(indices)

X_train_seq = seq_to_indices(train['sym_seq'])
X_val_seq = seq_to_indices(val['sym_seq'])
X_test_seq = seq_to_indices(test['sym_seq'])

y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

print("Sequence data shapes:")
print(f"X_train_seq: {X_train_seq.shape}")
print(f"X_val_seq: {X_val_seq.shape}")
print(f"X_test_seq: {X_test_seq.shape}")

# Try a simple neural network with embeddings
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.callbacks import EarlyStopping

# Set random seed for reproducibility
tf.random.set_seed(42)
np.random.seed(42)

# Build model
vocab_size = len(chars) + 1  # +1 for padding
embedding_dim = 8

model = keras.Sequential([
    layers.Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=max_len),
    layers.Flatten(),
    layers.Dense(32, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(16, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)

print("\nModel summary:")
model.summary()

# Train model
early_stopping = EarlyStopping(
    monitor='val_auc',
    patience=20,
    restore_best_weights=True,
    mode='max'
)

history = model.fit(
    X_train_seq, y_train,
    validation_data=(X_val_seq, y_val),
    epochs=100,
    batch_size=32,
    callbacks=[early_stopping],
    verbose=1
)

# Evaluate on validation set
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, precision_score, recall_score
val_pred = model.predict(X_val_seq)
val_auc = roc_auc_score(y_val, val_pred)
val_pred_class = (val_pred > 0.5).astype(int)
val_accuracy = accuracy_score(y_val, val_pred_class)
val_f1 = f1_score(y_val, val_pred_class)

print("\n" + "="*60)
print("Validation Set Performance (Neural Network with Embeddings):")
print("="*60)
print(f"AUC: {val_auc:.4f}")
print(f"Accuracy: {val_accuracy:.4f}")
print(f"F1 Score: {val_f1:.4f}")

# Evaluate on test set
test_pred = model.predict(X_test_seq)
test_auc = roc_auc_score(y_test, test_pred)
test_pred_class = (test_pred > 0.5).astype(int)
test_accuracy = accuracy_score(y_test, test_pred_class)
test_precision = precision_score(y_test, test_pred_class)
test_recall = recall_score(y_test, test_pred_class)
test_f1 = f1_score(y_test, test_pred_class)

print("\n" + "="*60)
print("Test Set Performance (Neural Network with Embeddings):")
print("="*60)
print(f"AUC: {test_auc:.4f}")
print(f"Accuracy: {test_accuracy:.4f}")
print(f"Precision: {test_precision:.4f}")
print(f"Recall: {test_recall:.4f}")
print(f"F1 Score: {test_f1:.4f}")

# Compare with baseline
baseline_auc = 0.72
print(f"\nBaseline AUC: {baseline_auc:.4f}")
print(f"Our model AUC: {test_auc:.4f}")
print(f"Difference: {test_auc - baseline_auc:.4f}")

# Save the model
model.save('../outputs/neural_model.h5')
print("\nModel saved to outputs/neural_model.h5")

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# Plot 1: Training history
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Loss
axes[0].plot(history.history['loss'], label='Train Loss')
axes[0].plot(history.history['val_loss'], label='Val Loss')
axes[0].set_title('Model Loss')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Accuracy
axes[1].plot(history.history['accuracy'], label='Train Accuracy')
axes[1].plot(history.history['val_accuracy'], label='Val Accuracy')
axes[1].set_title('Model Accuracy')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# AUC
axes[2].plot(history.history['auc'], label='Train AUC')
axes[2].plot(history.history['val_auc'], label='Val AUC')
axes[2].set_title('Model AUC')
axes[2].set_xlabel('Epoch')
axes[2].set_ylabel('AUC')
axes[2].legend()
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/neural_training_history.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: ROC curve
fig, ax = plt.subplots(figsize=(8, 6))

from sklearn.metrics import roc_curve
fpr, tpr, thresholds = roc_curve(y_test, test_pred)

ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {test_auc:.3f})')
ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('ROC Curve - Neural Network with Embeddings')
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/neural_roc_curve.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Confusion matrix
fig, ax = plt.subplots(figsize=(8, 6))
from sklearn.metrics import confusion_matrix
import seaborn as sns

cm = confusion_matrix(y_test, test_pred_class)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Non-default', 'Default'],
            yticklabels=['Non-default', 'Default'])
ax.set_title('Confusion Matrix - Neural Network')
ax.set_ylabel('True Label')
ax.set_xlabel('Predicted Label')

plt.tight_layout()
plt.savefig('../report/images/neural_confusion_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualizations saved to report/images/")
