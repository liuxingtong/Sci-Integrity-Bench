import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. 
# Let's look at the protocol again. "Classify variable vs non-variable sources using symbol_series features."
# What if the characters are just a string representation of a light curve, and we need to use a specific string kernel?
# We tried spectrum kernel (k-mer counts) and got 0.58.
# What if we use a mismatch kernel or a subsequence kernel?
# Let's try to use the `string_kernel` from `pykernels` or just implement a simple one.
# Actually, let's try to use the `CountVectorizer` with character n-grams again, but with a different classifier.
# We tried LR, SVC, RF, XGB. SVC Linear got 0.57.
# What if we use a Naive Bayes classifier?

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

best_acc = 0
for n_max in [3, 5, 7, 10, 15]:
    vec = CountVectorizer(analyzer='char', ngram_range=(1, n_max))
    X_train = vec.fit_transform(train['symbol_series'])
    X_val = vec.transform(val['symbol_series'])
    
    clf_nb = MultinomialNB()
    clf_nb.fit(X_train, train['label'])
    acc_nb = balanced_accuracy_score(val['label'], clf_nb.predict(X_val))
    
    print(f'n_max={n_max} -> NB: {acc_nb:.4f}')
    if acc_nb > best_acc:
        best_acc = acc_nb

print(f'Best Acc: {best_acc:.4f}')
