import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Let's try to use the top substrings as features
# We can use CountVectorizer with a custom vocabulary

def get_top_substrings(series, k, top_n):
    substrings = []
    for s in series:
        for i in range(len(s) - k + 1):
            substrings.append(s[i:i+k])
    from collections import Counter
    counts = Counter(substrings)
    return [item[0] for item in counts.most_common(top_n)]

vocab = set()
for k in [2, 3, 4, 5]:
    vocab.update(get_top_substrings(train[train['label'] == 0]['symbol_series'], k, 100))
    vocab.update(get_top_substrings(train[train['label'] == 1]['symbol_series'], k, 100))

vocab = list(vocab)

vectorizer = CountVectorizer(analyzer='char', ngram_range=(2, 5), vocabulary=vocab)
X_train = vectorizer.fit_transform(train['symbol_series'])
X_val = vectorizer.transform(val['symbol_series'])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Custom Vocab RF Val Acc:', balanced_accuracy_score(y_val, val_pred))

model = SVC(random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Custom Vocab SVC Val Acc:', balanced_accuracy_score(y_val, val_pred))

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Custom Vocab LR Val Acc:', balanced_accuracy_score(y_val, val_pred))
