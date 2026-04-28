import pandas as pd
import matplotlib.pyplot as plt
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

df = pd.read_csv('data/beverage_temperature_series.csv')

plt.figure(figsize=(10, 6))
plt.plot(df['time_min'], df['temperature_c'], marker='.', linestyle='-')
plt.xlabel('Time (min)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Temperature over Time')
plt.grid(True)
plt.savefig('report/images/raw_data.png')
plt.close()
