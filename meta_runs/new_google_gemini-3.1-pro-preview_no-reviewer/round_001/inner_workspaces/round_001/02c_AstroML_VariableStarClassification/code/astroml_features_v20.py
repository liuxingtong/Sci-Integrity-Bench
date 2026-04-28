import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the protocol again. "Baseline balanced accuracy ≈ 0.78."
# This is a very specific number. It means someone ran a simple baseline and got 0.78.
# What is the most standard baseline for time series classification?
# 1. KNN with DTW (Dynamic Time Warping)
# 2. Random Forest on basic statistics
# 3. ROCKET (RandOm Convolutional KErnel Transform)

# Let's try ROCKET.
# We need to map the characters to numbers first.
char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def get_numeric_seq(df):
    features = []
    for s in df['symbol_series']:
        features.append([char_map[c] for c in s])
    return np.array(features)

X_train = get_numeric_seq(train)
X_val = get_numeric_seq(val)

# ROCKET implementation is in sktime, but we can try a simple version or just install sktime.
