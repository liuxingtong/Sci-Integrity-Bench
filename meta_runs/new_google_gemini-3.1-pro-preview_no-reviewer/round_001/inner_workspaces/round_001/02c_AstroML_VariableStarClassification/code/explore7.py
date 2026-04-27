import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's try n-grams of characters
vectorizer = CountVectorizer(analyzer='char', ngram_range=(2, 4), max_features=5000)
X_train = vectorizer.fit_transform(train['symbol_series'])
X_val = vectorizer.transform(val['symbol_series'])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

val_pred = model.predict(X_val)
print('Val Acc:', balanced_accuracy_score(y_val, val_pred))

# Let's look at feature importances
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]
features = vectorizer.get_feature_names_out()

print("\nTop 20 features:")
for i in range(20):
    print(f"{features[indices[i]]}: {importances[indices[i]]}")
