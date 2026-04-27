import pandas as pd
import re

df = pd.read_csv('outputs/merged_catalog.csv')

for idx, row in df.iterrows():
    print(f"{row['norm_acc']}: {row['note']}")
