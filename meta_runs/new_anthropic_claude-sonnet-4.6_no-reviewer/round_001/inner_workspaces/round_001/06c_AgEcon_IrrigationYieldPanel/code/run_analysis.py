#!/usr/bin/env python3
"""
Irrigation Impact Analysis
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import ttest_ind
import os
import traceback

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

log = []

def log_print(msg):
    print(msg)
    log.append(str(msg))

try:
    # Load data
    df = pd.read_csv('data/field_year_panel.csv')
    log_print(f'Data loaded: {df.shape}')
    log_print(f'Columns: {list(df.columns)}')
    
    # Column names from the data
    field_col = 'field_id'
    year_col = 'year'
    yield_col = 'yield_kg_ha'
    irrig_col = 'irrigation_mm'
    fert_col = 'fertilizer_kg_ha'
    rain_col = 'rainfall_mm'
    quota_col = 'quota_enforced'
    
    # Verify columns exist
    for col in [field_col, year_col, yield_col, irrig_col, fert_col, rain_col, quota_col]:
        if col not in df.columns:
            log_print(f'WARNING: Column {col} not found!')
            # Try to find it
            for c in df.columns:
                if col.split('_')[0] in c.lower():
                    log_print(f'  Found similar: {c}')
    
    log_print(f'\nBasic stats:')
    log_print(str(df.describe()))
    log_print(f'\nMissing values:')
    log_print(str(df.isnull().sum()))
    log_print(f'\nQuota values: {sorted(df[quota_col].unique())}')
    log_print(f'Year range: {df[year_col].min()} - {df[year_col].max()}')
    log_print(f'Fields: {df[field_col].nunique()}')
    
except Exception as e:
    log_print(f'Error in data loading: {e}')
    traceback.print_exc()

with open('outputs/run_log.txt', 'w') as f:
    f.write('\n'.join(log))

log_print('Log saved.')
