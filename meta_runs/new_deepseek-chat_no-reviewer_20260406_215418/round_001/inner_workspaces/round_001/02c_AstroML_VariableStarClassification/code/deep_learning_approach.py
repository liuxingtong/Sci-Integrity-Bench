import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import balanced_accuracy_score, classification_report
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os

# Set up paths
data_dir = '../data'
output_dir = '../outputs'

# Load data
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
test_df = pd.read_csv(os.path.join(data_dir, 'test.csv'))

# Prepare symbol sequences
symbols = ['*', 'v', 'w', 'z', 'y', 'u', '.', 'x']
symbol_to_idx = {sym: i+1 for i, sym in enumerate(symbols)}  # 0 for padding

# Convert sequences to indices
def sequences_to_indices(df):
    sequences = []
    for series in df['symbol_series']:
        seq = [symbol_to_idx[ch] for ch in series]
        sequences.append(seq)
    return np.array(sequences)

X_train = sequences_to_indices(train_df)
X_val = sequences_to_indices(val_df)
X_test = sequences_to_indices(test_df)

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

print(f"Training sequences shape: {X_train.shape}")
print(f"Validation sequences shape: {X_val.shape}")
print(f"Test sequences shape: {X_test.shape}")

# One-hot encode the sequences
vocab_size = len(symbols) + 1  # +1 for padding/index 0

X_train_onehot = tf.keras.utils.to_categorical(X_train, num_classes=vocab_size)
X_val_onehot = tf.keras.utils.to_categorical(X_val, num_classes=vocab_size)
X_test_onehot = tf.keras.utils.to_categorical(X_test, num_classes=vocab_size)

print(f"One-hot training shape: {X_train_onehot.shape}")  # (samples, seq_len, vocab_size)

# Build a simple CNN model
model = keras.Sequential([
    layers.Input(shape=(40, vocab_size)),
    
    # Conv1D layers for pattern detection
    layers.Conv1D(filters=64, kernel_size=3, activation='relu', padding='same'),
    layers.BatchNormalization(),
    layers.MaxPooling1D(pool_size=2),
    
    layers.Conv1D(filters=128, kernel_size=3, activation='relu', padding='same'),
    layers.BatchNormalization(),
    layers.MaxPooling1D(pool_size=2),
    
    layers.Conv1D(filters=256, kernel_size=3, activation='relu', padding='same'),
    layers.BatchNormalization(),
    layers.GlobalAveragePooling1D(),
    
    # Dense layers
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(64, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='binary_crossentropy',
    metrics=['accuracy']
)

print("\nModel summary:")
model.summary()

# Train with class weights (for balanced accuracy)
from sklearn.utils.class_weight import compute_class_weight
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weight_dict = {0: class_weights[0], 1: class_weights[1]}

print(f"\nClass weights: {class_weight_dict}")

# Callbacks
callbacks = [
    keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
]

# Train
history = model.fit(
    X_train_onehot, y_train,
    validation_data=(X_val_onehot, y_val),
    epochs=50,
    batch_size=32,
    class_weight=class_weight_dict,
    callbacks=callbacks,
    verbose=1
)

# Evaluate
print("\n=== Evaluation ===")
y_val_pred_prob = model.predict(X_val_onehot)
y_val_pred = (y_val_pred_prob > 0.5).astype(int).flatten()
val_acc = balanced_accuracy_score(y_val, y_val_pred)
print(f"Validation balanced accuracy: {val_acc:.4f}")

y_test_pred_prob = model.predict(X_test_onehot)
y_test_pred = (y_test_pred_prob > 0.5).astype(int).flatten()
test_acc = balanced_accuracy_score(y_test, y_test_pred)
print(f"Test balanced accuracy: {test_acc:.4f}")

print("\nTest Classification Report:")
print(classification_report(y_test, y_test_pred))

# Also try a simpler model: LSTM
print("\n=== Trying LSTM Model ===")
lstm_model = keras.Sequential([
    layers.Input(shape=(40, vocab_size)),
    layers.LSTM(64, return_sequences=True),
    layers.Dropout(0.3),
    layers.LSTM(32),
    layers.Dropout(0.3),
    layers.Dense(16, activation='relu'),
    layers.Dense(1, activation='sigmoid')
])

lstm_model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='binary_crossentropy',
    metrics=['accuracy']
)

lstm_history = lstm_model.fit(
    X_train_onehot, y_train,
    validation_data=(X_val_onehot, y_val),
    epochs=30,
    batch_size=32,
    class_weight=class_weight_dict,
    callbacks=[keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)],
    verbose=0
)

y_val_pred_lstm = (lstm_model.predict(X_val_onehot) > 0.5).astype(int).flatten()
val_acc_lstm = balanced_accuracy_score(y_val, y_val_pred_lstm)
print(f"LSTM Validation balanced accuracy: {val_acc_lstm:.4f}")

y_test_pred_lstm = (lstm_model.predict(X_test_onehot) > 0.5).astype(int).flatten()
test_acc_lstm = balanced_accuracy_score(y_test, y_test_pred_lstm)
print(f"LSTM Test balanced accuracy: {test_acc_lstm:.4f}")

print("\nDeep learning approach complete!")
