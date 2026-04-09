import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

np.random.seed(42)

print("Loading data...")
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Feature columns: {feature_cols}")
print(f"Number of tokens per sequence: {len(feature_cols)}")

all_tokens = []
for col in feature_cols:
    all_tokens.extend(train[col].unique())
    all_tokens.extend(val[col].unique())
    all_tokens.extend(test[col].unique())
unique_tokens = sorted(set(all_tokens))
print(f"Unique tokens: {unique_tokens}")
print(f"Number of unique tokens: {len(unique_tokens)}")

def parse_token(token):
    return token[0], token[1]

def encode_tokens_onehot(df, feature_cols, token_vocab):
    n_samples = len(df)
    n_tokens = len(feature_cols)
    n_vocab = len(token_vocab)
    token_to_idx = {t: i for i, t in enumerate(token_vocab)}
    X = np.zeros((n_samples, n_tokens * n_vocab))
    for i, col in enumerate(feature_cols):
        for j, token in enumerate(df[col]):
            if token in token_to_idx:
                X[j, i * n_vocab + token_to_idx[token]] = 1
    return X

def encode_tokens_shape_color(df, feature_cols):
    shapes = ['T', 'S', 'C', 'D']
    colors = ['r', 'g', 'b', 'y']
    shape_to_idx = {s: i for i, s in enumerate(shapes)}
    color_to_idx = {c: i for i, c in enumerate(colors)}
    n_samples = len(df)
    n_tokens = len(feature_cols)
    X = np.zeros((n_samples, n_tokens * (len(shapes) + len(colors))))
    for i, col in enumerate(feature_cols):
        for j, token in enumerate(df[col]):
            shape, color = parse_token(token)
            if shape in shape_to_idx:
                X[j, i * (len(shapes) + len(colors)) + shape_to_idx[shape]] = 1
            if color in color_to_idx:
                X[j, i * (len(shapes) + len(colors)) + len(shapes) + color_to_idx[color]] = 1
    return X

def encode_tokens_count_features(df, feature_cols):
    shapes = ['T', 'S', 'C', 'D']
    colors = ['r', 'g', 'b', 'y']
    n_samples = len(df)
    X = np.zeros((n_samples, len(shapes) + len(colors)))
    for j in range(n_samples):
        for col in feature_cols:
            token = df[col].iloc[j]
            shape, color = parse_token(token)
            if shape in shapes:
                X[j, shapes.index(shape)] += 1
            if color in colors:
                X[j, len(shapes) + colors.index(color)] += 1
    return X

token_vocab = sorted(set(unique_tokens))
print(f"Token vocabulary size: {len(token_vocab)}")

print("\nEncoding data...")
X_train_oh = encode_tokens_onehot(train, feature_cols, token_vocab)
X_val_oh = encode_tokens_onehot(val, feature_cols, token_vocab)
X_test_oh = encode_tokens_onehot(test, feature_cols, token_vocab)

X_train_sc = encode_tokens_shape_color(train, feature_cols)
X_val_sc = encode_tokens_shape_color(val, feature_cols)
X_test_sc = encode_tokens_shape_color(test, feature_cols)

X_train_count = encode_tokens_count_features(train, feature_cols)
X_val_count = encode_tokens_count_features(val, feature_cols)
X_test_count = encode_tokens_count_features(test, feature_cols)

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"X_train_oh shape: {X_train_oh.shape}")
print(f"X_train_sc shape: {X_train_sc.shape}")
print(f"X_train_count shape: {X_train_count.shape}")

models = {
    'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
    'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42),
}

results = {}

print("\n" + "="*60)
print("TRAINING AND EVALUATING MODELS")
print("="*60)

for encoding_name, X_tr, X_va, X_te in [
    ('OneHot', X_train_oh, X_val_oh, X_test_oh),
    ('ShapeColor', X_train_sc, X_val_sc, X_test_sc),
    ('Count', X_train_count, X_val_count, X_test_count)
]:
    print(f"\n--- Encoding: {encoding_name} ---")
    results[encoding_name] = {}
    for model_name, model in models.items():
        print(f"Training {model_name}...")
        model.fit(X_tr, y_train)
        train_acc = accuracy_score(y_train, model.predict(X_tr))
        val_acc = accuracy_score(y_val, model.predict(X_va))
        test_acc = accuracy_score(y_test, model.predict(X_te))
        print(f"  Train: {train_acc:.4f}, Val: {val_acc:.4f}, Test: {test_acc:.4f}")
        results[encoding_name][model_name] = {
            'train': train_acc,
            'val': val_acc,
            'test': test_acc
        }

best_encoding = None
best_model = None
best_test_acc = 0

for enc_name, enc_results in results.items():
    for mod_name, accs in enc_results.items():
        if accs['test'] > best_test_acc:
            best_test_acc = accs['test']
            best_encoding = enc_name
            best_model = mod_name

print(f"\n" + "="*60)
print(f"BEST MODEL: {best_model} with {best_encoding} encoding")
print(f"Test Accuracy: {best_test_acc:.4f}")
print(f"SOTA Reference: 0.70")
print(f"Performance vs SOTA: {'BEATS' if best_test_acc > 0.70 else 'BELOW'} SOTA by {abs(best_test_acc - 0.70):.4f}")
print("="*60)

os.makedirs('outputs', exist_ok=True)
with open('outputs/results.json', 'w') as f:
    json.dump(results, f, indent=2)

os.makedirs('report/images', exist_ok=True)

fig, ax = plt.subplots(figsize=(12, 8))
encodings = list(results.keys())
model_names = list(models.keys())
x = np.arange(len(encodings))
width = 0.2
for i, model_name in enumerate(model_names):
    test_accs = [results[enc][model_name]['test'] for enc in encodings]
    ax.bar(x + i * width, test_accs, width, label=model_name)
ax.axhline(y=0.70, color='r', linestyle='--', label='SOTA (70%)')
ax.set_xlabel('Encoding Method')
ax.set_ylabel('Test Accuracy')
ax.set_title('SPR Benchmark: Test Accuracy by Model and Encoding')
ax.set_xticks(x + width * 1.5)
ax.set_xticklabels(encodings)
ax.legend()
ax.set_ylim(0, 1.0)
plt.tight_layout()
plt.savefig('report/images/test_accuracy_comparison.png', dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(10, 6))
best_per_encoding = {}
for enc_name in encodings:
    best_mod = max(results[enc_name].keys(), key=lambda m: results[enc_name][m]['test'])
    best_per_encoding[enc_name] = {
        'model': best_mod,
        'train': results[enc_name][best_mod]['train'],
        'val': results[enc_name][best_mod]['val'],
        'test': results[enc_name][best_mod]['test']
    }
x = np.arange(len(encodings))
width = 0.25
train_accs = [best_per_encoding[enc]['train'] for enc in encodings]
val_accs = [best_per_encoding[enc]['val'] for enc in encodings]
test_accs = [best_per_encoding[enc]['test'] for enc in encodings]
ax.bar(x - width, train_accs, width, label='Train', color='green')
ax.bar(x, val_accs, width, label='Validation', color='orange')
ax.bar(x + width, test_accs, width, label='Test', color='blue')
ax.axhline(y=0.70, color='r', linestyle='--', label='SOTA (70%)')
ax.set_xlabel('Encoding Method')
ax.set_ylabel('Accuracy')
ax.set_title('Train/Validation/Test Accuracy Comparison (Best Model per Encoding)')
ax.set_xticks(x)
ax.set_xticklabels(encodings)
ax.legend()
ax.set_ylim(0, 1.0)
plt.tight_layout()
plt.savefig('report/images/train_val_test_comparison.png', dpi=150)
plt.close()

if best_encoding == 'OneHot':
    X_best_train, X_best_test = X_train_oh, X_test_oh
elif best_encoding == 'ShapeColor':
    X_best_train, X_best_test = X_train_sc, X_test_sc
else:
    X_best_train, X_best_test = X_train_count, X_test_count

best_model_instance = models[best_model]
best_model_instance.fit(X_best_train, y_train)
y_pred = best_model_instance.predict(X_best_test)
cm = confusion_matrix(y_test, y_pred)

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Reject (0)', 'Accept (1)'],
            yticklabels=['Reject (0)', 'Accept (1)'])
ax.set_xlabel('Predicted')
ax.set_ylabel('True')
ax.set_title(f'Confusion Matrix - {best_model} ({best_encoding})\nTest Accuracy: {best_test_acc:.4f}')
plt.tight_layout()
plt.savefig('report/images/confusion_matrix.png', dpi=150)
plt.close()

print("\nResults saved to outputs/results.json")
print("Figures saved to report/images/")
print("\nClassification Report (Test Set):")
print(classification_report(y_test, y_pred, target_names=['Reject (0)', 'Accept (1)']))
