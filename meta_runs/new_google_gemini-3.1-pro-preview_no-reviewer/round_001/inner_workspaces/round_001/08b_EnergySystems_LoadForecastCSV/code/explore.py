import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv('data/load_15min.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

# Plot raw data
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['load_mw'], label='Raw Load')
plt.title('Raw 15-minute Load Data')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True)
plt.savefig('outputs/raw_load.png')
plt.close()

# Missing values analysis
missing = df['load_mw'].isna().sum()
print(f'Missing values: {missing}')

# Impute missing values using linear interpolation
df['load_mw_imputed'] = df['load_mw'].interpolate(method='linear')

# Plot imputed data
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['load_mw_imputed'], label='Imputed Load', color='orange')
plt.plot(df.index, df['load_mw'], label='Raw Load', color='blue')
plt.title('Imputed 15-minute Load Data')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True)
plt.savefig('outputs/imputed_load.png')
plt.close()

# Save imputed data
df.to_csv('outputs/load_imputed.csv')

# Daily profile
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['time'] = df['hour'] + df['minute'] / 60

plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x='time', y='load_mw_imputed')
plt.title('Average Daily Load Profile')
plt.xlabel('Hour of Day')
plt.ylabel('Load (MW)')
plt.grid(True)
plt.savefig('outputs/daily_profile.png')
plt.close()
