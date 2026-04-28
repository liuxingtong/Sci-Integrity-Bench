import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('data/flame_pressure_series.csv')

# Plot data
plt.figure(figsize=(10, 6))
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], label='Data')
plt.xlabel('Pressure (kPa)')
plt.ylabel('Flame Speed (cm/s)')
plt.title('Flame Speed vs Chamber Pressure')
plt.legend()
plt.grid(True)
plt.savefig('outputs/raw_data.png')
plt.close()
