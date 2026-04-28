import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib.pyplot as plt
from scipy.sparse import hstack
from sklearn.preprocessing import OneHotEncoder

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# 1. N-grams
vec = CountVectorizer(ngram_range=(1, 3), analyzer='char')
X_train_ngrams = vec.fit_transform(train['sym_seq'])
X_val_ngrams = vec.transform(val['sym_seq'])
X_test_ngrams = vec.transform(test['sym_seq'])

# 2. Positional features (One-hot)
chars = ['A', 'B', 'C', 'D', '1', '2']
char_to_idx = {c: i for i, c in enumerate(chars)}

def extract_positional_features(df):
    features = []
    for seq in df['sym_seq']:
        row = []
        for char in seq:
            row.append(char_to_idx[char])
        features.append(row)
    return np.array(features)

enc = OneHotEncoder(sparse_output=True)
X_train_pos = enc.fit_transform(extract_positional_features(train))
X_val_pos = enc.transform(extract_positional_features(val))
X_test_pos = enc.transform(extract_positional_features(test))

# Combine
X_train = hstack([X_train_ngrams, X_train_pos])
X_val = hstack([X_val_ngrams, X_val_pos])
X_test = hstack([X_test_ngrams, X_test_pos])

y_train = train['default_flag']
y_val = val['default_flag']
y_test = test['default_flag']

# Logistic Regression
lr = LogisticRegression(max_iter=1000, C=0.5, penalty='l1', solver='liblinear')
lr.fit(X_train, y_train)

val_preds = lr.predict_proba(X_val)[:, 1]
auc_val = roc_auc_score(y_val, val_preds)
print(f'Val AUC: {auc_val:.4f}')

test_preds = lr.predict_proba(X_test)[:, 1]
auc_test = roc_auc_score(y_test, test_preds)
print(f'Test AUC: {auc_test:.4f}')

# Plot ROC curve
fpr_val, tpr_val, _ = roc_curve(y_val, val_preds)
fpr_test, tpr_test, _ = roc_curve(y_test, test_preds)

plt.figure(figsize=(8, 6))
plt.plot(fpr_val, tpr_val, label=f'Validation ROC (AUC = {auc_val:.4f})')
plt.plot(fpr_test, tpr_test, label=f'Test ROC (AUC = {auc_test:.4f})')
plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve - Logistic Regression (L1)')
plt.legend(loc='lower right')
plt.savefig('report/images/roc_curve_l1.png')
plt.close()
