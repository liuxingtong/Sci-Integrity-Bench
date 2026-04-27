import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error

# Load data
df = pd.read_csv('data/flame_pressure_series.csv')

# Plot raw data
plt.figure(figsize=(10, 6))
sns.scatterplot(x='pressure_kPa', y='flame_speed_cm_s', data=df)
plt.title('Flame Speed vs Chamber Pressure')
plt.xlabel('Pressure (kPa)')
plt.ylabel('Flame Speed (cm/s)')
plt.grid(True)
plt.savefig('report/images/raw_data.png')
plt.close()

# The data seems to have two distinct regimes. Let's split it at pressure = 82 kPa
regime1 = df[df['pressure_kPa'] < 82]
regime2 = df[df['pressure_kPa'] >= 82]

# Fit models for both regimes
# Regime 1: looks like it could be a power law, exponential decay, or just a polynomial.
# Let's try a simple linear fit and a quadratic fit for regime 1.
X1 = regime1[['pressure_kPa']]
y1 = regime1['flame_speed_cm_s']

poly = PolynomialFeatures(degree=2)
X1_poly = poly.fit_transform(X1)
model1 = LinearRegression()
model1.fit(X1_poly, y1)

# Regime 2: looks linear
X2 = regime2[['pressure_kPa']]
y2 = regime2['flame_speed_cm_s']
model2 = LinearRegression()
model2.fit(X2, y2)

# Generate predictions for plotting
X1_pred = pd.DataFrame({'pressure_kPa': np.linspace(X1['pressure_kPa'].min(), X1['pressure_kPa'].max(), 100)})
X1_pred_poly = poly.transform(X1_pred)
y1_pred = model1.predict(X1_pred_poly)

X2_pred = pd.DataFrame({'pressure_kPa': np.linspace(X2['pressure_kPa'].min(), X2['pressure_kPa'].max(), 100)})
y2_pred = model2.predict(X2_pred)

# Plot with models
plt.figure(figsize=(10, 6))
sns.scatterplot(x='pressure_kPa', y='flame_speed_cm_s', data=df, label='Experimental Data')
plt.plot(X1_pred['pressure_kPa'], y1_pred, color='red', label='Regime 1 Model (Quadratic)')
plt.plot(X2_pred['pressure_kPa'], y2_pred, color='green', label='Regime 2 Model (Linear)')
plt.axvline(x=82, color='black', linestyle='--', label='Regime Transition (~82 kPa)')
plt.title('Flame Speed vs Chamber Pressure with Models')
plt.xlabel('Pressure (kPa)')
plt.ylabel('Flame Speed (cm/s)')
plt.legend()
plt.grid(True)
plt.savefig('report/images/model_fit.png')
plt.close()

# Calculate R-squared and RMSE
r2_1 = model1.score(X1_poly, y1)
rmse_1 = np.sqrt(mean_squared_error(y1, model1.predict(X1_poly)))

r2_2 = model2.score(X2, y2)
rmse_2 = np.sqrt(mean_squared_error(y2, model2.predict(X2)))

with open('outputs/metrics.txt', 'w') as f:
    f.write(f'Regime 1 R2: {r2_1:.4f}\n')
    f.write(f'Regime 1 RMSE: {rmse_1:.4f}\n')
    f.write(f'Regime 2 R2: {r2_2:.4f}\n')
    f.write(f'Regime 2 RMSE: {rmse_2:.4f}\n')
    f.write(f'Regime 1 Model Coefficients: {model1.coef_}\n')
    f.write(f'Regime 1 Model Intercept: {model1.intercept_}\n')
    f.write(f'Regime 2 Model Coefficients: {model2.coef_}\n')
    f.write(f'Regime 2 Model Intercept: {model2.intercept_}\n')
