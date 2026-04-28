import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

train = pd.read_csv('data/train.csv')

chars = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']

for c in chars:
    train[f'count_{c}'] = train['symbol_series'].apply(lambda s: s.count(c))

print(train.groupby('label')[[f'count_{c}' for c in chars]].mean())

# Let's also look at the variance of the characters if we map them to numbers
# Assuming u=0, v=1, w=2, x=3, y=4, z=5. What about * and .?
# Let's just look at the counts first.
