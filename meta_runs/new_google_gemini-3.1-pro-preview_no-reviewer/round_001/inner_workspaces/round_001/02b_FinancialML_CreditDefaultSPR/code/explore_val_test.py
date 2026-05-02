import pandas as pd

val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')
print('Val shape:', val.shape)
print('Test shape:', test.shape)
