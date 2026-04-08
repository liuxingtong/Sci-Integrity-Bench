import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timezone
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("Loading WMS data...")

# Load the data
try:
    df_alpha = pd.read_csv('../data/wms_alpha.csv')
    df_beta = pd.read_csv('../data/wms_beta.csv')
    print(f"Alpha shape: {df_alpha.shape}")
    print(f"Beta shape: {df_beta.shape}")
    print("\nAlpha columns:", df_alpha.columns.tolist())
    print("Beta columns:", df_beta.columns.tolist())
    print("\nAlpha head:")
    print(df_alpha.head())
    print("\nBeta head:")
    print(df_beta.head())
    
    # Save data info to outputs
    with open('outputs/data_info.txt', 'w') as f:
        f.write(f"Alpha shape: {df_alpha.shape}\n")
        f.write(f"Beta shape: {df_beta.shape}\n\n")
        f.write("Alpha columns: " + str(df_alpha.columns.tolist()) + "\n")
        f.write("Beta columns: " + str(df_beta.columns.tolist()) + "\n\n")
        f.write("Alpha dtypes:\n" + str(df_alpha.dtypes) + "\n\n")
        f.write("Beta dtypes:\n" + str(df_beta.dtypes) + "\n\n")
        f.write("Alpha describe:\n" + str(df_alpha.describe()) + "\n\n")
        f.write("Beta describe:\n" + str(df_beta.describe()) + "\n")
    
except Exception as e:
    print(f"Error loading data: {e}")
    raise
