import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train_raw = train[feature_cols]
y_train = train['label'].values
X_val_raw = val[feature_cols]
y_val = val['label'].values
X_test_raw = test[feature_cols]
y_test = test['label'].values

print("Data loaded successfully")
print(f"Train: {X_train_raw.shape}, Validation: {X_val_raw.shape}, Test: {X_test_raw.shape}")

# Create token vocabulary
all_tokens = set()
for col in feature_cols:
    all_tokens.update(X_train_raw[col].unique())
    all_tokens.update(X_val_raw[col].unique())
    all_tokens.update(X_test_raw[col].unique())

token_list = sorted(list(all_tokens))
token_to_idx = {token: i+1 for i, token in enumerate(token_list)}  # 0 for padding
vocab_size = len(token_list) + 1  # +1 for padding token

print(f"Vocabulary size: {vocab_size}")
print(f"Tokens: {token_list}")

# Convert tokens to indices
def tokens_to_indices(df):
    indices = []
    for idx, row in df.iterrows():
        seq_indices = [token_to_idx[row[col]] for col in feature_cols]
        indices.append(seq_indices)
    return np.array(indices)

X_train_idx = tokens_to_indices(X_train_raw)
X_val_idx = tokens_to_indices(X_val_raw)
X_test_idx = tokens_to_indices(X_test_raw)

print(f"\nSequence length: {X_train_idx.shape[1]}")

# Transformer model components
def transformer_encoder(inputs, head_size, num_heads, ff_dim, dropout=0):
    # Normalization and Attention
    x = layers.LayerNormalization(epsilon=1e-6)(inputs)
    x = layers.MultiHeadAttention(
        key_dim=head_size, num_heads=num_heads, dropout=dropout
    )(x, x)
    x = layers.Dropout(dropout)(x)
    res = x + inputs

    # Feed Forward Part
    x = layers.LayerNormalization(epsilon=1e-6)(res)
    x = layers.Dense(ff_dim, activation="relu")(x)
    x = layers.Dropout(dropout)(x)
    x = layers.Dense(inputs.shape[-1])(x)
    return x + res

# Build model
sequence_length = X_train_idx.shape[1]
embedding_dim = 32

inputs = keras.Input(shape=(sequence_length,))
x = layers.Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=sequence_length)(inputs)
x = layers.Dropout(0.1)(x)

# Add multiple transformer blocks
for _ in range(2):
    x = transformer_encoder(x, head_size=embedding_dim, num_heads=4, ff_dim=64, dropout=0.1)

# Global pooling and output
x = layers.GlobalAveragePooling1D()(x)
x = layers.Dropout(0.2)(x)
x = layers.Dense(32, activation="relu")(x)
x = layers.Dropout(0.2)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)

model = keras.Model(inputs=inputs, outputs=outputs)

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='binary_crossentropy',
    metrics=['accuracy']
)

model.summary()

# Train model
print("\nTraining Transformer model...")
history = model.fit(
    X_train_idx, y_train,
    validation_data=(X_val_idx, y_val),
    epochs=50,
    batch_size=32,
    verbose=1
)

# Evaluate
print("\nEvaluating model...")
train_pred_proba = model.predict(X_train_idx)
train_pred = (train_pred_proba > 0.5).astype(int).flatten()
val_pred_proba = model.predict(X_val_idx)
val_pred = (val_pred_proba > 0.5).astype(int).flatten()
test_pred_proba = model.predict(X_test_idx)
test_pred = (test_pred_proba > 0.5).astype(int).flatten()

train_acc = accuracy_score(y_train, train_pred)
val_acc = accuracy_score(y_val, val_pred)
test_acc = accuracy_score(y_test, test_pred)

print(f"Training accuracy: {train_acc:.4f}")
print(f"Validation accuracy: {val_acc:.4f}")
print(f"Test accuracy: {test_acc:.4f}")

# Compare with SOTA
sota_baseline = 0.70
print(f"\nSOTA baseline: {sota_baseline:.4f}")
print(f"Transformer test accuracy vs SOTA: {test_acc:.4f} vs {sota_baseline:.4f}")
print(f"Difference: {test_acc - sota_baseline:.4f}")

if test_acc > sota_baseline:
    print("SUCCESS: Transformer model exceeds the SOTA baseline!")
else:
    print("Transformer model does not exceed the SOTA baseline yet.")

# Save training history
history_df = pd.DataFrame(history.history)
history_df.to_csv('../outputs/transformer_training_history.csv', index=False)
print("\nTraining history saved to outputs/transformer_training_history.csv")