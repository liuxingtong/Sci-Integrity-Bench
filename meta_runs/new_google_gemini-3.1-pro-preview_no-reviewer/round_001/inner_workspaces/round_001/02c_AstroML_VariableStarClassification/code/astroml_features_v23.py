import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The means are almost identical. So it's not just the counts.
# What if the characters represent a specific sequence of events?
# Let's try to use a simple decision tree to see if there is a single feature that splits the data well.

from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction.text import CountVectorizer

vec = CountVectorizer(analyzer='char', ngram_range=(1, 5))
X_train = vec.fit_transform(train['symbol_series'])
X_val = vec.transform(val['symbol_series'])

clf_dt = DecisionTreeClassifier(max_depth=3, random_state=42)
clf_dt.fit(X_train, train['label'])

from sklearn.tree import export_text
print(export_text(clf_dt, feature_names=vec.get_feature_names_out()))

print(f'DT Val Balanced Acc: {balanced_accuracy_score(val["label"], clf_dt.predict(X_val)):.4f}')
