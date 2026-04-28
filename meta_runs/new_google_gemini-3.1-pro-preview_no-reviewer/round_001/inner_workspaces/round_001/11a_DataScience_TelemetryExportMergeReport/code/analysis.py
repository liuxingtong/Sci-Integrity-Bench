import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
site_df = pd.read_csv('data/site_daily_kwh.csv')
field_df = pd.read_csv('data/field_ops_export.csv')

# Standardize site_df
site_df['date'] = pd.to_datetime(site_df['record_date'])
site_df['unit'] = site_df['generator_unit'].str.replace('-', '')
site_df = site_df.rename(columns={'net_kwh': 'site_kwh'})
site_df = site_df[['date', 'unit', 'site_kwh']]

# Standardize field_df
field_df['date'] = pd.to_datetime(field_df['ReadingDt'], errors='coerce')
field_df = field_df.dropna(subset=['date'])
field_df['unit'] = field_df['Unit'].str.replace('-', '')
field_df = field_df.rename(columns={'Delivered_kWh': 'field_kwh'})
field_df = field_df[['date', 'unit', 'field_kwh']]

# Merge datasets
merged_df = pd.merge(site_df, field_df, on=['date', 'unit'], how='outer')

# Calculate discrepancy
merged_df['discrepancy'] = merged_df['site_kwh'] - merged_df['field_kwh']
merged_df['abs_discrepancy'] = merged_df['discrepancy'].abs()

# Save merged data
merged_df.to_csv('outputs/merged_data.csv', index=False)

# Basic stats
stats = merged_df.describe()
stats.to_csv('outputs/summary_stats.csv')

# Plot 1: Time series of total kWh per day
daily_total = merged_df.groupby('date')[['site_kwh', 'field_kwh']].sum().reset_index()
plt.figure(figsize=(12, 6))
plt.plot(daily_total['date'], daily_total['site_kwh'], label='Site Historian', alpha=0.7)
plt.plot(daily_total['date'], daily_total['field_kwh'], label='Field Ops', alpha=0.7, linestyle='--')
plt.title('Total Daily Energy Production (Q1)')
plt.xlabel('Date')
plt.ylabel('Total kWh')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/daily_total_kwh.png')
plt.close()

# Plot 2: Discrepancy over time
plt.figure(figsize=(12, 6))
sns.scatterplot(data=merged_df, x='date', y='discrepancy', hue='unit')
plt.title('Daily Discrepancy (Site - Field) by Unit')
plt.xlabel('Date')
plt.ylabel('Discrepancy (kWh)')
plt.axhline(0, color='black', linestyle='--')
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/discrepancy_scatter.png')
plt.close()

# Plot 3: Total production by unit
unit_total = merged_df.groupby('unit')[['site_kwh', 'field_kwh']].sum().reset_index()
unit_total_melted = pd.melt(unit_total, id_vars='unit', var_name='source', value_name='total_kwh')
plt.figure(figsize=(10, 6))
sns.barplot(data=unit_total_melted, x='unit', y='total_kwh', hue='source')
plt.title('Total Energy Production by Unit (Q1)')
plt.xlabel('Generator Unit')
plt.ylabel('Total kWh')
plt.grid(axis='y')
plt.tight_layout()
plt.savefig('report/images/unit_total_kwh.png')
plt.close()

# Plot 4: Distribution of discrepancies
plt.figure(figsize=(10, 6))
sns.histplot(merged_df['discrepancy'].dropna(), bins=30, kde=True)
plt.title('Distribution of Measurement Discrepancies (Site - Field)')
plt.xlabel('Discrepancy (kWh)')
plt.ylabel('Frequency')
plt.grid(axis='y')
plt.tight_layout()
plt.savefig('report/images/discrepancy_dist.png')
plt.close()

# Identify units with highest discrepancy
unit_discrepancy = merged_df.groupby('unit')['abs_discrepancy'].mean().reset_index()
unit_discrepancy = unit_discrepancy.sort_values('abs_discrepancy', ascending=False)
unit_discrepancy.to_csv('outputs/unit_discrepancy.csv', index=False)

print("Analysis complete. Outputs saved.")
