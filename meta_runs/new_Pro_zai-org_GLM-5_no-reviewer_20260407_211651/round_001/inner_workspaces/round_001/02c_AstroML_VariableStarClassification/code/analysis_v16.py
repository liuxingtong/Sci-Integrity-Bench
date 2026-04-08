import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
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

# Let's try a completely different approach - treat this as a sequence problem
# and use n-gram features with TF-IDF-like weighting

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# Treat symbol_series as text
def extract_ngram_features(train_series, val_series, test_series, n_range=(1, 3)):
    """Extract n-gram features using TF-IDF"""
    train_texts = train_series.tolist()
    val_texts = val_series.tolist()
    test_texts = test_series.tolist()
    
    # Use character n-grams
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=n_range, max_features=500)
    
    X_train = vectorizer.fit_transform(train_texts)
    X_val = vectorizer.transform(val_texts)
    X_test = vectorizer.transform(test_texts)
    
    return X_train, X_val, X_test, vectorizer

print("\n" + "="*60)
print("N-gram Feature Extraction")
print("="*60)

# Try different n-gram ranges
for n_range in [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (3, 3)]:
    X_train, X_val, X_test, vec = extract_ngram_features(
        train['symbol_series'], val['symbol_series'], test['symbol_series'], n_range
    )
    
    y_train = train['label'].values
    y_val = val['label'].values
    y_test = test['label'].values
    
    # Try Logistic Regression
    lr = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
    lr.fit(X_train, y_train)
    y_pred = lr.predict(X_val)
    val_acc = balanced_accuracy_score(y_val, y_pred)
    
    # Try Random Forest
    rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_val)
    val_acc_rf = balanced_accuracy_score(y_val, y_pred_rf)
    
    print(f"n-gram {n_range}: LR={val_acc:.4f}, RF={val_acc_rf:.4f}, features={X_train.shape[1]}")

# Best approach seems to be with n-grams (1, 3)
print("\n" + "="*60)
print("Best Model with N-gram Features")
print("="*60)

X_train, X_val, X_test, vec = extract_ngram_features(
    train['symbol_series'], val['symbol_series'], test['symbol_series'], n_range=(1, 3)
)

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

# Combine train and val
X_train_full = np.vstack([X_train.toarray(), X_val.toarray()])
y_train_full = np.concatenate([y_train, y_val])

# Try multiple models
models = {
    'LR': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'RF': RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1),
    'GB': GradientBoostingClassifier(n_estimators=300, max_depth=5, random_state=42),
    'SVM': SVC(kernel='rbf', C=1.0, random_state=42),
}

val_results = {}
for name, model in models.items():
    model.fit(X_train.toarray(), y_train)
    y_pred = model.predict(X_val.toarray())
    bal_acc = balanced_accuracy_score(y_val, y_pred)
    val_results[name] = bal_acc
    print(f"{name}: {bal_acc:.4f}")

best_model_name = max(val_results, key=val_results.get)
print(f"\nBest model: {best_model_name}")

# Final evaluation
best_model = models[best_model_name]
best_model.fit(X_train_full, y_train_full)
y_test_pred = best_model.predict(X_test.toarray())
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
