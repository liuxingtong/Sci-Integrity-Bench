"""
Credit Default Prediction - Neural Network Approach
Using LSTM and CNN to capture sequential patterns
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# TensorFlow imports
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D, Flatten, Embedding
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except:
    TF_AVAILABLE = False
    print("TensorFlow not available")

np.random.seed(42)
if TF_AVAILABLE:
    tf.random.set_seed(42)

import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=" * 60)
print("Credit Default Prediction - Neural Network Approach")
print("=" * 60)

# Load data
print("\n[1] Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

# ============================================================
# Sequence Encoding
# ============================================================
print("\n[2] Encoding sequences...")

# Create character to index mapping
chars = ['A', 'B', 'C', 'D', '1', '2']
char_to_idx = {c: i for i, c in enumerate(chars)}

def encode_sequence(seq):
    """One-hot encode sequence"""
    encoded = np.zeros((len(seq), len(chars)))
    for i, char in enumerate(seq):
        if char in char_to_idx:
            encoded[i, char_to_idx[char]] = 1
    return encoded

# Encode all sequences
X_train_seq = np.array([encode_sequence(seq) for seq in train_df['sym_seq']])
X_val_seq = np.array([encode_sequence(seq) for seq in val_df['sym_seq']])
X_test_seq = np.array([encode_sequence(seq) for seq in test_df['sym_seq']])

print(f"Sequence shape: {X_train_seq.shape}")

# ============================================================
# Neural Network Models
# ============================================================
print("\n[3] Training Neural Network Models...")

results = {}

if TF_AVAILABLE:
    # 1. LSTM Model
    print("\nTraining LSTM...")
    
    model_lstm = Sequential([
        LSTM(64, input_shape=(20, 6), return_sequences=True),
        Dropout(0.3),
        LSTM(32),
        Dropout(0.3),
        Dense(16, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    
    model_lstm.compile(optimizer=Adam(learning_rate=0.001), 
                       loss='binary_crossentropy', 
                       metrics=['AUC'])
    
    early_stop = EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)
    
    history_lstm = model_lstm.fit(
        X_train_seq, y_train,
        validation_data=(X_val_seq, y_val),
        epochs=100,
        batch_size=32,
        callbacks=[early_stop],
        verbose=0
    )
    
    val_pred_lstm = model_lstm.predict(X_val_seq, verbose=0).flatten()
    test_pred_lstm = model_lstm.predict(X_test_seq, verbose=0).flatten()
    
    val_auc_lstm = roc_auc_score(y_val, val_pred_lstm)
    test_auc_lstm = roc_auc_score(y_test, test_pred_lstm)
    
    results['LSTM'] = {'val_auc': val_auc_lstm, 'test_auc': test_auc_lstm,
                       'val_pred': val_pred_lstm, 'test_pred': test_pred_lstm,
                       'history': history_lstm}
    
    print(f"  Val AUC: {val_auc_lstm:.4f}, Test AUC: {test_auc_lstm:.4f}")
    
    # 2. CNN Model
    print("\nTraining CNN...")
    
    model_cnn = Sequential([
        Conv1D(64, 3, activation='relu', input_shape=(20, 6)),
        MaxPooling1D(2),
        Conv1D(32, 3, activation='relu'),
        MaxPooling1D(2),
        Flatten(),
        Dense(32, activation='relu'),
        Dropout(0.3),
        Dense(16, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    
    model_cnn.compile(optimizer=Adam(learning_rate=0.001),
                      loss='binary_crossentropy',
                      metrics=['AUC'])
    
    history_cnn = model_cnn.fit(
        X_train_seq, y_train,
        validation_data=(X_val_seq, y_val),
        epochs=100,
        batch_size=32,
        callbacks=[early_stop],
        verbose=0
    )
    
    val_pred_cnn = model_cnn.predict(X_val_seq, verbose=0).flatten()
    test_pred_cnn = model_cnn.predict(X_test_seq, verbose=0).flatten()
    
    val_auc_cnn = roc_auc_score(y_val, val_pred_cnn)
    test_auc_cnn = roc_auc_score(y_test, test_pred_cnn)
    
    results['CNN'] = {'val_auc': val_auc_cnn, 'test_auc': test_auc_cnn,
                      'val_pred': val_pred_cnn, 'test_pred': test_pred_cnn,
                      'history': history_cnn}
    
    print(f"  Val AUC: {val_auc_cnn:.4f}, Test AUC: {test_auc_cnn:.4f}")
    
    # 3. Simple Dense Model
    print("\nTraining Dense Network...")
    
    X_train_flat = X_train_seq.reshape(X_train_seq.shape[0], -1)
    X_val_flat = X_val_seq.reshape(X_val_seq.shape[0], -1)
    X_test_flat = X_test_seq.reshape(X_test_seq.shape[0], -1)
    
    model_dense = Sequential([
        Dense(128, activation='relu', input_shape=(120,)),
        Dropout(0.4),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    
    model_dense.compile(optimizer=Adam(learning_rate=0.001),
                        loss='binary_crossentropy',
                        metrics=['AUC'])
    
    history_dense = model_dense.fit(
        X_train_flat, y_train,
        validation_data=(X_val_flat, y_val),
        epochs=100,
        batch_size=32,
        callbacks=[early_stop],
        verbose=0
    )
    
    val_pred_dense = model_dense.predict(X_val_flat, verbose=0).flatten()
    test_pred_dense = model_dense.predict(X_test_flat, verbose=0).flatten()
    
    val_auc_dense = roc_auc_score(y_val, val_pred_dense)
    test_auc_dense = roc_auc_score(y_test, test_pred_dense)
    
    results['Dense NN'] = {'val_auc': val_auc_dense, 'test_auc': test_auc_dense,
                           'val_pred': val_pred_dense, 'test_pred': test_pred_dense,
                           'history': history_dense}
    
    print(f"  Val AUC: {val_auc_dense:.4f}, Test AUC: {test_auc_dense:.4f}")

# ============================================================
# Visualizations
# ============================================================
print("\n[4] Generating Visualizations...")

plt.style.use('seaborn-v0_8-whitegrid')

# ROC Curves
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_val, res['val_pred'])
    axes[0].plot(fpr, tpr, label=f"{name} (AUC={res['val_auc']:.3f})", linewidth=2)

axes[0].plot([0, 1], [0, 1], 'k--', label='Random (0.500)')
axes[0].axhline(y=0.72, color='r', linestyle=':', alpha=0.7, label='Baseline (0.72)')
axes[0].set_xlabel('False Positive Rate', fontsize=12)
axes[0].set_ylabel('True Positive Rate', fontsize=12)
axes[0].set_title('ROC Curves - Validation Set', fontsize=14, fontweight='bold')
axes[0].legend(loc='lower right', fontsize=9)
axes[0].set_xlim([0, 1])
axes[0].set_ylim([0, 1])

for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    axes[1].plot(fpr, tpr, label=f"{name} (AUC={res['test_auc']:.3f})", linewidth=2)

axes[1].plot([0, 1], [0, 1], 'k--', label='Random (0.500)')
axes[1].axhline(y=0.72, color='r', linestyle=':', alpha=0.7, label='Baseline (0.72)')
axes[1].set_xlabel('False Positive Rate', fontsize=12)
axes[1].set_ylabel('True Positive Rate', fontsize=12)
axes[1].set_title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
axes[1].legend(loc='lower right', fontsize=9)
axes[1].set_xlim([0, 1])
axes[1].set_ylim([0, 1])

plt.tight_layout()
plt.savefig('../report/images/roc_curves_nn.png', dpi=300, bbox_inches='tight')
plt.close()

# Model Comparison
fig, ax = plt.subplots(figsize=(10, 6))

models = list(results.keys())
val_aucs = [results[m]['val_auc'] for m in models]
test_aucs = [results[m]['test_auc'] for m in models]

x = np.arange(len(models))
width = 0.35

bars1 = ax.bar(x - width/2, val_aucs, width, label='Validation AUC', alpha=0.8)
bars2 = ax.bar(x + width/2, test_aucs, width, label='Test AUC', alpha=0.8)

ax.axhline(y=0.72, color='r', linestyle='--', linewidth=2, label='Baseline (0.72)')

ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('AUC Score', fontsize=12)
ax.set_title('Neural Network Performance Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=15, ha='right')
ax.legend(fontsize=10)
ax.set_ylim([0.4, 0.8])

for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/model_comparison_nn.png', dpi=300, bbox_inches='tight')
plt.close()

# Training History
if TF_AVAILABLE and len(results) > 0:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (name, res) in enumerate(results.items()):
        if 'history' in res:
            hist = res['history']
            axes[idx].plot(hist.history['loss'], label='Train Loss')
            axes[idx].plot(hist.history['val_loss'], label='Val Loss')
            axes[idx].set_xlabel('Epoch', fontsize=10)
            axes[idx].set_ylabel('Loss', fontsize=10)
            axes[idx].set_title(f'{name} - Training History', fontsize=11, fontweight='bold')
            axes[idx].legend(fontsize=8)
    
    plt.tight_layout()
    plt.savefig('../report/images/training_history.png', dpi=300, bbox_inches='tight')
    plt.close()

# ============================================================
# Save Results
# ============================================================
print("\n[5] Saving Results...")

summary = pd.DataFrame({
    'Model': list(results.keys()),
    'Validation_AUC': [results[m]['val_auc'] for m in results.keys()],
    'Test_AUC': [results[m]['test_auc'] for m in results.keys()]
})

summary.to_csv('../outputs/results_summary_nn.csv', index=False)
print("\nResults Summary:")
print(summary)

if len(results) > 0:
    best_model = max(results, key=lambda x: results[x]['test_auc'])
    print(f"\nBest Model: {best_model}")
    print(f"Test AUC: {results[best_model]['test_auc']:.4f}")
    print(f"Baseline: 0.72")
