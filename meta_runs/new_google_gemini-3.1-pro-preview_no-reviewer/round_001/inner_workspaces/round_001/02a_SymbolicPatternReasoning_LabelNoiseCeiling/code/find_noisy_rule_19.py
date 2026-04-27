import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Let's rethink the task name: "LabelNoiseCeiling"
# This is a very specific name. It implies that the task is to find the ceiling of performance under label noise.
# If the SOTA is 70%, it means the ceiling is 70%.
# This means the labels are exactly 30% noisy.
# If the labels are 30% noisy, then ANY model that learns the true rule will get exactly 70% accuracy on the training set, validation set, and test set.
# But we haven't found ANY model that gets 70% accuracy on the validation set.
# The best validation accuracy we got was ~55%.
# This means our models are NOT learning the true rule.
# Why? Because the true rule is too complex, OR we are overfitting the noise.

# Let's try to train a very simple model, like Naive Bayes, which is robust to noise.
from sklearn.naive_bayes import MultinomialNB, GaussianNB
from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(train[feature_cols])
y_train = train['label']

val = pd.read_csv('data/spr_bench_val.csv')
X_val = encoder.transform(val[feature_cols])
y_val = val['label']

nb = MultinomialNB()
nb.fit(X_train, y_train)
print(f"MultinomialNB - Train: {accuracy_score(y_train, nb.predict(X_train)):.4f}, Val: {accuracy_score(y_val, nb.predict(X_val)):.4f}")

gnb = GaussianNB()
gnb.fit(X_train, y_train)
print(f"GaussianNB - Train: {accuracy_score(y_train, gnb.predict(X_train)):.4f}, Val: {accuracy_score(y_val, gnb.predict(X_val)):.4f}")

# Let's try Naive Bayes on abstract features
def extract_all_features(df):
    X = pd.DataFrame()
    shapes = ['T', 'S', 'C', 'D']
    colors = ['r', 'g', 'b', 'y']
    
    for s in shapes:
        X[f'count_shape_{s}'] = df[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s), axis=1)
    for c in colors:
        X[f'count_color_{c}'] = df[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c), axis=1)
        
    for s in shapes:
        X[f'first_shape_{s}'] = df['token_0'].str[0] == s
        X[f'last_shape_{s}'] = df[f'token_{len(feature_cols)-1}'].str[0] == s
    for c in colors:
        X[f'first_color_{c}'] = df['token_0'].str[1] == c
        X[f'last_color_{c}'] = df[f'token_{len(feature_cols)-1}'].str[1] == c
        
    X['has_adj_shape'] = df[feature_cols].apply(lambda x: any(x[i][0] == x[i+1][0] for i in range(len(x)-1)), axis=1)
    X['has_adj_color'] = df[feature_cols].apply(lambda x: any(x[i][1] == x[i+1][1] for i in range(len(x)-1)), axis=1)
    
    X['unique_shapes'] = df[feature_cols].apply(lambda x: len(set(t[0] for t in x)), axis=1)
    X['unique_colors'] = df[feature_cols].apply(lambda x: len(set(t[1] for t in x)), axis=1)
    
    return X

X_train_abs = extract_all_features(train)
X_val_abs = extract_all_features(val)

nb_abs = MultinomialNB()
nb_abs.fit(X_train_abs, y_train)
print(f"MultinomialNB (Abs) - Train: {accuracy_score(y_train, nb_abs.predict(X_train_abs)):.4f}, Val: {accuracy_score(y_val, nb_abs.predict(X_val_abs)):.4f}")

gnb_abs = GaussianNB()
gnb_abs.fit(X_train_abs, y_train)
print(f"GaussianNB (Abs) - Train: {accuracy_score(y_train, gnb_abs.predict(X_train_abs)):.4f}, Val: {accuracy_score(y_val, gnb_abs.predict(X_val_abs)):.4f}")
