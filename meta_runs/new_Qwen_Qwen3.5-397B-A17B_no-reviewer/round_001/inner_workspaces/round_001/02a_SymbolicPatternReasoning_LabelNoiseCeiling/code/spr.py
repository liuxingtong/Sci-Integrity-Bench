import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f'Train: {train.shape}, Val: {val.shape}, Test: {test.shape}')

def extract_features(df, feature_cols):
    features = []
    for col in feature_cols:
        tokens = df[col].astype(str)
        shapes = tokens.str[0]
        colors = tokens.str[1]
        features.append(shapes)
        features.append(colors)
    return pd.DataFrame(features).T

X_train_raw = extract_features(train, feature_cols)
X_val_raw = extract_features(val, feature_cols)
X_test_raw = extract_features(test, feature_cols)

X_train_encoded = np.zeros((X_train_raw.shape[0], X_train_raw.shape[1]))
X_val_encoded = np.zeros((X_val_raw.shape[0], X_val_raw.shape[1]))
X_test_encoded = np.zeros((X_test_raw.shape[0], X_test_raw.shape[1]))

for i in range(X_train_raw.shape[1]):
    le = LabelEncoder()
    all_vals = pd.concat([X_train_raw.iloc[:, i], X_val_raw.iloc[:, i], X_test_raw.iloc[:, i]])
    le.fit(all_vals)
    X_train_encoded[:, i] = le.transform(X_train_raw.iloc[:, i])
    X_val_encoded[:, i] = le.transform(X_val_raw.iloc[:, i])
    X_test_encoded[:, i] = le.transform(X_test_raw.iloc[:, i])

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_encoded)
X_val_scaled = scaler.transform(X_val_encoded)
X_test_scaled = scaler.transform(X_test_encoded)

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
}

results = []
for name, model in models.items():
    print(f'Training {name}...')
    model.fit(X_train_scaled, y_train)
    train_acc = accuracy_score(y_train, model.predict(X_train_scaled))
    val_acc = accuracy_score(y_val, model.predict(X_val_scaled))
    test_acc = accuracy_score(y_test, model.predict(X_test_scaled))
    results.append({'Model': name, 'Train Acc': train_acc, 'Val Acc': val_acc, 'Test Acc': test_acc})
    print(f'  Train: {train_acc:.4f}, Val: {val_acc:.4f}, Test: {test_acc:.4f}')

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))
results_df.to_csv('outputs/results.csv', index=False)

best_idx = results_df['Test Acc'].idxmax()
best_model_name = results_df.loc[best_idx, 'Model']
best_test_acc = results_df.loc[best_idx, 'Test Acc']
print(f'Best: {best_model_name} = {best_test_acc:.4f}')

plt.figure(figsize=(10, 6))
colors = ['green' if acc > 0.70 else 'orange' for acc in results_df['Test Acc']]
plt.barh(results_df['Model'], results_df['Test Acc'], color=colors)
plt.axvline(x=0.70, color='blue', linestyle='--', linewidth=2, label='SOTA (70%)')
plt.xlabel('Test Accuracy')
plt.title('Model Comparison on SPR_BENCH Test Set')
plt.xlim(0, 1.0)
plt.legend()
plt.tight_layout()
plt.savefig('report/images/model_comparison.png', dpi=150)
plt.close()

plt.figure(figsize=(10, 6))
x = np.arange(len(results_df['Model']))
width = 0.25
plt.bar(x - width, results_df['Train Acc'], width, label='Train', color='skyblue')
plt.bar(x, results_df['Val Acc'], width, label='Validation', color='lightgreen')
plt.bar(x + width, results_df['Test Acc'], width, label='Test', color='coral')
plt.axhline(y=0.70, color='blue', linestyle='--', linewidth=2, label='SOTA (70%)')
plt.xlabel('Model')
plt.ylabel('Accuracy')
plt.title('Train/Validation/Test Accuracy Comparison')
plt.xticks(x, results_df['Model'], rotation=45, ha='right')
plt.legend()
plt.tight_layout()
plt.savefig('report/images/accuracy_splits.png', dpi=150)
plt.close()

best_model = models[best_model_name]
y_pred_test = best_model.predict(X_test_scaled)
cm = confusion_matrix(y_test, y_pred_test)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Reject (0)', 'Accept (1)'], yticklabels=['Reject (0)', 'Accept (1)'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title(f'Confusion Matrix - {best_model_name}')
plt.tight_layout()
plt.savefig('report/images/confusion_matrix.png', dpi=150)
plt.close()

print(classification_report(y_test, y_pred_test, target_names=['Reject (0)', 'Accept (1)']))
with open('outputs/classification_report.txt', 'w') as rf:
    rf.write(f'Classification Report - {best_model_name}\n')
    rf.write(classification_report(y_test, y_pred_test, target_names=['Reject (0)', 'Accept (1)']))
print('Done!')
