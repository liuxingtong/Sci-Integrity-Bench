"""
Credit Default Prediction - Neural Network approach
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# Load data
print("Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Encode sequences as integer sequences
def encode_sequences(df):
    """Convert character sequences to integer sequences"""
    char_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, '1': 4, '2': 5}
    seqs = df['sym_seq'].values
    encoded = np.array([[char_map[c] for c in seq] for seq in seqs])
    return encoded

X_train_seq = encode_sequences(train_df)
X_val_seq = encode_sequences(val_df)
X_test_seq = encode_sequences(test_df)

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Sequence shape: {X_train_seq.shape}")

# Try embedding + simple neural network
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout, Flatten, Conv1D, GlobalMaxPooling1D
    
    tf.random.set_seed(42)
    
    print("\nBuilding neural network models...")
    
    results = {}
    
    # Model 1: Simple Embedding + Dense
    model1 = Sequential([
        Embedding(input_dim=6, output_dim=8, input_length=20),
        Flatten(),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.3),
        Dense(1, activation='sigmoid')
    ])
    
    model1.compile(optimizer='adam', loss='binary_crossentropy', metrics=['AUC'])
    
    print("Training Model 1 (Embedding + Dense)...")
    model1.fit(X_train_seq, y_train, epochs=50, batch_size=32, 
               validation_data=(X_val_seq, y_val), verbose=0)
    
    val_pred = model1.predict(X_val_seq, verbose=0).flatten()
    test_pred = model1.predict(X_test_seq, verbose=0).flatten()
    results['NN-Embedding'] = {
        'val_auc': roc_auc_score(y_val, val_pred),
        'test_auc': roc_auc_score(y_test, test_pred),
        'test_pred': test_pred
    }
    print(f"NN-Embedding: Val AUC = {results['NN-Embedding']['val_auc']:.4f}, Test AUC = {results['NN-Embedding']['test_auc']:.4f}")
    
    # Model 2: LSTM
    model2 = Sequential([
        Embedding(input_dim=6, output_dim=8, input_length=20),
        LSTM(32, dropout=0.2, recurrent_dropout=0.2),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    
    model2.compile(optimizer='adam', loss='binary_crossentropy', metrics=['AUC'])
    
    print("Training Model 2 (LSTM)...")
    model2.fit(X_train_seq, y_train, epochs=50, batch_size=32, 
               validation_data=(X_val_seq, y_val), verbose=0)
    
    val_pred = model2.predict(X_val_seq, verbose=0).flatten()
    test_pred = model2.predict(X_test_seq, verbose=0).flatten()
    results['NN-LSTM'] = {
        'val_auc': roc_auc_score(y_val, val_pred),
        'test_auc': roc_auc_score(y_test, test_pred),
        'test_pred': test_pred
    }
    print(f"NN-LSTM: Val AUC = {results['NN-LSTM']['val_auc']:.4f}, Test AUC = {results['NN-LSTM']['test_auc']:.4f}")
    
    # Model 3: CNN
    model3 = Sequential([
        Embedding(input_dim=6, output_dim=8, input_length=20),
        Conv1D(64, 3, activation='relu'),
        Conv1D(32, 3, activation='relu'),
        GlobalMaxPooling1D(),
        Dense(16, activation='relu'),
        Dropout(0.3),
        Dense(1, activation='sigmoid')
    ])
    
    model3.compile(optimizer='adam', loss='binary_crossentropy', metrics=['AUC'])
    
    print("Training Model 3 (CNN)...")
    model3.fit(X_train_seq, y_train, epochs=50, batch_size=32, 
               validation_data=(X_val_seq, y_val), verbose=0)
    
    val_pred = model3.predict(X_val_seq, verbose=0).flatten()
    test_pred = model3.predict(X_test_seq, verbose=0).flatten()
    results['NN-CNN'] = {
        'val_auc': roc_auc_score(y_val, val_pred),
        'test_auc': roc_auc_score(y_test, test_pred),
        'test_pred': test_pred
    }
    print(f"NN-CNN: Val AUC = {results['NN-CNN']['val_auc']:.4f}, Test AUC = {results['NN-CNN']['test_auc']:.4f}")
    
    # Summary
    print("\n" + "="*60)
    print("NEURAL NETWORK RESULTS")
    print("="*60)
    for name, res in results.items():
        print(f"{name:<20} Val: {res['val_auc']:.4f}  Test: {res['test_auc']:.4f}")
    print(f"Baseline: 0.72")
    print("="*60)
    
    # Save results
    results_df = pd.DataFrame({
        'Model': list(results.keys()),
        'Val_AUC': [r['val_auc'] for r in results.values()],
        'Test_AUC': [r['test_auc'] for r in results.values()]
    })
    results_df.to_csv('../outputs/model_results_nn.csv', index=False)
    
    # Best model
    best_model = max(results.items(), key=lambda x: x[1]['val_auc'])
    print(f"\nBest: {best_model[0]} with Test AUC = {best_model[1]['test_auc']:.4f}")
    
    # Generate plots
    print("\nGenerating visualizations...")
    
    # Model comparison
    plt.figure(figsize=(10, 6))
    models = list(results.keys())
    val_aucs = [results[m]['val_auc'] for m in models]
    test_aucs = [results[m]['test_auc'] for m in models]
    
    x = np.arange(len(models))
    width = 0.35
    
    plt.bar(x - width/2, val_aucs, width, label='Validation AUC', color='steelblue', edgecolor='black')
    plt.bar(x + width/2, test_aucs, width, label='Test AUC', color='coral', edgecolor='black')
    
    plt.axhline(y=0.72, color='red', linestyle='--', linewidth=2, label='Baseline AUC = 0.72')
    plt.xlabel('Model', fontsize=12)
    plt.ylabel('AUC Score', fontsize=12)
    plt.title('Neural Network Performance Comparison', fontsize=14, fontweight='bold')
    plt.xticks(x, models)
    plt.legend()
    plt.ylim(0.4, 0.8)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/nn_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # ROC curves
    plt.figure(figsize=(10, 8))
    for model_name, res in results.items():
        fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
        plt.plot(fpr, tpr, label=f"{model_name} (AUC = {res['test_auc']:.3f})", linewidth=2)
    
    plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title('ROC Curves - Neural Networks', fontsize=14, fontweight='bold')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/nn_roc_curves.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("\nNeural network analysis complete!")
    
except ImportError:
    print("TensorFlow not available. Skipping neural network analysis.")
