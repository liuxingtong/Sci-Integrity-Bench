#!/usr/bin/env python3
"""
Explore the benchmark data to understand patterns.
"""

import pandas as pd
import numpy as np

# Look at a few benchmarks in detail
for code in ['ZOBKB', 'LHVPV']:
    print(f"\n{'='*60}")
    print(f"Benchmark: {code}")
    print(f"{'='*60}")
    
    train = pd.read_csv(f'data/{code}_train.csv')
    val = pd.read_csv(f'data/{code}_val.csv')
    test = pd.read_csv(f'data/{code}_test.csv')
    
    print(f"\nTrain head:")
    print(train.head(10).to_string())
    
    print(f"\nLabel distribution in train:")
    print(train['label'].value_counts())
    
    print(f"\nLabel distribution in test:")
    print(test['label'].value_counts())
    
    # Check unique values per column
    print(f"\nUnique values per column in train:")
    for col in train.columns:
        print(f"  {col}: {train[col].nunique()} unique values")
