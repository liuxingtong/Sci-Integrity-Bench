import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
print("Loading data...")
train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

print(f"Train size: {len(train)}, Val size: {len(val)}, Test size: {len(test)}")

# Define the character set
CHARS = ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}

# Best approach from previous analysis: n-gram (1, 2) with RF
print("\n" + "="*60)
print("Best Approach: N-gram (1, 2) with Random Forest")
print("="*60)

train_texts = train['symbol_series'].tolist()
val_texts = val['symbol_series'].tolist()
test_texts = test['symbol_series'].tolist()

vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 2), max_features=200)
X_train = vectorizer.fit_transform(train_texts).toarray()
X_val = vectorizer.transform(val_texts).toarray()
X_test = vectorizer.transform(test_texts).toarray()

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Features shape: {X_train.shape}")

# Try ensemble methods
print("\n" + "="*60)
print("Ensemble Methods")
print("="*60)

# Define base models
rf = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
gb = GradientBoostingClassifier(n_estimators=300, max_depth=5, random_state=42)
lr = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
svm = SVC(kernel='rbf', C=1.0, probability=True, random_state=42)

# Voting classifier
voting = VotingClassifier(
    estimators=[('rf', rf), ('gb', gb), ('lr', lr), ('svm', svm)],
    voting='soft'
)

# Stacking classifier
stacking = StackingClassifier(
    estimators=[('rf', rf), ('gb', gb), ('lr', lr)],
    final_estimator=LogisticRegression(max_iter=2000),
    cv=5
)

models = {
    'RF': RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1),
    'GB': GradientBoostingClassifier(n_estimators=300, max_depth=5, random_state=42),
    'LR': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'SVM': SVC(kernel='rbf', C=1.0, probability=True, random_state=42),
    'Voting': voting,
    'Stacking': stacking,
}

val_results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)
    bal_acc = balanced_accuracy_score(y_val, y_pred)
    val_results[name] = bal_acc
    print(f"{name}: {bal_acc:.4f}")

best_model_name = max(val_results, key=val_results.get)
print(f"\nBest model: {best_model_name} with {val_results[best_model_name]:.4f}")

# Final evaluation
X_train_full = np.vstack([X_train, X_val])
y_train_full = np.concatenate([y_train, y_val])

best_model = models[best_model_name]
best_model.fit(X_train_full, y_train_full)
y_test_pred = best_model.predict(X_test)
test_bal_acc = balanced_accuracy_score(y_test, y_test_pred)

print(f"\nTest Balanced Accuracy: {test_bal_acc:.4f}")
print(f"Baseline: 0.78")

print("\nClassification Report:")
print(classification_report(y_test, y_test_pred, target_names=['Non-variable', 'Variable']))

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'predicted_label': y_test_pred
})
predictions_df.to_csv('outputs/predictions.csv', index=False)

print("\nAnalysis complete!")
