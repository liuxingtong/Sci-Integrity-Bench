import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Let's go back to the most successful approach so far: n-grams.
# The baseline is 0.78. We got ~0.56 with simple n-grams.
# Maybe we need to use word n-grams instead of char n-grams?
# But the string is just characters without spaces.
# What if we split the string into words of length k?

def split_into_words(s, k):
    return ' '.join([s[i:i+k] for i in range(0, len(s), k)])

for k in [2, 4, 5, 8]:
    train[f'words_{k}'] = train['symbol_series'].apply(lambda x: split_into_words(x, k))
    val[f'words_{k}'] = val['symbol_series'].apply(lambda x: split_into_words(x, k))
    
    vectorizer = TfidfVectorizer(ngram_range=(1, 3))
    X_train = vectorizer.fit_transform(train[f'words_{k}'])
    X_val = vectorizer.transform(val[f'words_{k}'])
    
    model = LogisticRegression(random_state=42)
    model.fit(X_train, train['label'])
    val_pred = model.predict(X_val)
    print(f'Words {k} LR Val Acc:', balanced_accuracy_score(val['label'], val_pred))
    
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, train['label'])
    val_pred = model.predict(X_val)
    print(f'Words {k} RF Val Acc:', balanced_accuracy_score(val['label'], val_pred))
