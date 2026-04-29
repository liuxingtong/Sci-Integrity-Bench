import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 4))

preprocessor = ColumnTransformer(
    transformers=[
        ('text', vectorizer, 'symbol_series'),
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['field_id'])
    ])

model = Pipeline(steps=[('preprocessor', preprocessor),
                      ('classifier', GradientBoostingClassifier(n_estimators=200, random_state=42))])

model.fit(train_df, train_df['label'])
y_val_pred = model.predict(val_df)
acc = balanced_accuracy_score(val_df['label'], y_val_pred)
print(f'TF-IDF + Field ID Val Balanced Accuracy: {acc:.4f}')
