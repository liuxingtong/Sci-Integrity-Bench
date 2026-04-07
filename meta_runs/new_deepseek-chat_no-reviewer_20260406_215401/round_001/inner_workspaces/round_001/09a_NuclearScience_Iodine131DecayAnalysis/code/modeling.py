import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error, r2_score
from scipy.optimize import curve_fit
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load regime data
regime1 = pd.read_csv("../outputs/regime1_data.csv")
regime2 = pd.read_csv("../outputs/regime2_data.csv")

print("=== Modeling Flame Speed vs Chamber Pressure ===\n")

# Define models to try
def linear_model(x, a, b):
    return a * x + b

def exponential_decay(x, a, b, c):
    return a * np.exp(-b * x) + c

def power_law(x, a, b):
    return a * (x ** b)

# Function to fit and evaluate models
def fit_and_evaluate(x, y, model_func, model_name, p0=None):
    try:
        if p0:
            params, _ = curve_fit(model_func, x, y, p0=p0, maxfev=5000)
        else:
            params, _ = curve_fit(model_func, x, y, maxfev=5000)
        
        y_pred = model_func(x, *params)
        mse = mean_squared_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        return {
            'params': params,
            'mse': mse,
            'r2': r2,
            'y_pred': y_pred
        }
    except Exception as e:
        print(f"  Error fitting {model_name}: {e}")
        return None

# Prepare data for each regime
x1 = regime1['pressure_kPa'].values
y1 = regime1['flame_speed_cm_s'].values

x2 = regime2['pressure_kPa'].values
y2 = regime2['flame_speed_cm_s'].values

print("=== Regime 1 (Low Pressure: 38.0-81.5 kPa) ===")
print(f"Data points: {len(x1)}")

# Try different models for Regime 1
models_regime1 = {}

# Linear model
print("\n1. Linear model:")
result = fit_and_evaluate(x1, y1, linear_model, "linear", p0=[-0.5, 60])
if result:
    models_regime1['linear'] = result
    print(f"   Parameters: y = {result['params'][0]:.4f} * x + {result['params'][1]:.4f}")
    print(f"   MSE: {result['mse']:.4f}, R²: {result['r2']:.4f}")

# Exponential decay model
print("\n2. Exponential decay model:")
result = fit_and_evaluate(x1, y1, exponential_decay, "exponential", p0=[20, 0.01, 20])
if result:
    models_regime1['exponential'] = result
    print(f"   Parameters: y = {result['params'][0]:.4f} * exp(-{result['params'][1]:.4f} * x) + {result['params'][2]:.4f}")
    print(f"   MSE: {result['mse']:.4f}, R²: {result['r2']:.4f}")

# Power law model
print("\n3. Power law model:")
result = fit_and_evaluate(x1, y1, power_law, "power", p0=[100, -0.5])
if result:
    models_regime1['power'] = result
    print(f"   Parameters: y = {result['params'][0]:.4f} * x^{result['params'][1]:.4f}")
    print(f"   MSE: {result['mse']:.4f}, R²: {result['r2']:.4f}")

# Polynomial regression (degree 2)
print("\n4. Quadratic polynomial:")
poly = PolynomialFeatures(degree=2)
x1_poly = poly.fit_transform(x1.reshape(-1, 1))
model = LinearRegression()
model.fit(x1_poly, y1)
y1_pred_poly = model.predict(x1_poly)
mse_poly = mean_squared_error(y1, y1_pred_poly)
r2_poly = r2_score(y1, y1_pred_poly)
models_regime1['quadratic'] = {
    'model': model,
    'poly': poly,
    'mse': mse_poly,
    'r2': r2_poly,
    'y_pred': y1_pred_poly
}
print(f"   Parameters: y = {model.coef_[2]:.6f}x² + {model.coef_[1]:.6f}x + {model.intercept_:.6f}")
print(f"   MSE: {mse_poly:.4f}, R²: {r2_poly:.4f}")

# Find best model for Regime 1
if models_regime1:
    best_model_name = min(models_regime1.keys(), key=lambda k: models_regime1[k]['mse'])
    best_model = models_regime1[best_model_name]
    print(f"\nBest model for Regime 1: {best_model_name} (MSE: {best_model['mse']:.4f}, R²: {best_model['r2']:.4f})")

print("\n" + "="*60 + "\n")

print("=== Regime 2 (High Pressure: 82.4-97.5 kPa) ===")
print(f"Data points: {len(x2)}")

# For Regime 2, data is more constant, try simple models
models_regime2 = {}

# Constant model (mean)
print("\n1. Constant model (mean):")
y2_mean = np.mean(y2)
y2_pred_mean = np.full_like(y2, y2_mean)
mse_mean = mean_squared_error(y2, y2_pred_mean)
r2_mean = r2_score(y2, y2_pred_mean)
models_regime2['constant'] = {
    'value': y2_mean,
    'mse': mse_mean,
    'r2': r2_mean,
    'y_pred': y2_pred_mean
}
print(f"   Value: {y2_mean:.4f} cm/s")
print(f"   MSE: {mse_mean:.4f}, R²: {r2_mean:.4f}")

# Linear model
print("\n2. Linear model:")
result = fit_and_evaluate(x2, y2, linear_model, "linear", p0=[0, 30])
if result:
    models_regime2['linear'] = result
    print(f"   Parameters: y = {result['params'][0]:.4f} * x + {result['params'][1]:.4f}")
    print(f"   MSE: {result['mse']:.4f}, R²: {result['r2']:.4f}")

# Find best model for Regime 2
if models_regime2:
    best_model_name2 = min(models_regime2.keys(), key=lambda k: models_regime2[k]['mse'])
    best_model2 = models_regime2[best_model_name2]
    print(f"\nBest model for Regime 2: {best_model_name2} (MSE: {best_model2['mse']:.4f}, R²: {best_model2['r2']:.4f})")

# Create visualization of models
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Regime 1: Data and best model fit
ax = axes[0, 0]
ax.scatter(x1, y1, alpha=0.7, s=50, label='Data', color='blue')

# Plot all models for Regime 1
x1_range = np.linspace(x1.min(), x1.max(), 200)
for model_name, model_result in models_regime1.items():
    if model_name == 'quadratic':
        x1_poly_range = poly.transform(x1_range.reshape(-1, 1))
        y_pred_range = model_result['model'].predict(x1_poly_range)
    elif model_name in ['linear', 'exponential', 'power']:
        if model_name == 'linear':
            y_pred_range = linear_model(x1_range, *model_result['params'])
        elif model_name == 'exponential':
            y_pred_range = exponential_decay(x1_range, *model_result['params'])
        elif model_name == 'power':
            y_pred_range = power_law(x1_range, *model_result['params'])
    
    ax.plot(x1_range, y_pred_range, label=f'{model_name} (R²={model_result["r2"]:.3f})', 
            linewidth=2, alpha=0.8)

ax.set_xlabel('Pressure (kPa)')
ax.set_ylabel('Flame Speed (cm/s)')
ax.set_title('Regime 1: Model Fits')
ax.legend()
ax.grid(True, alpha=0.3)

# Regime 1: Residuals of best model
ax = axes[0, 1]
if 'best_model_name' in locals():
    residuals = y1 - best_model['y_pred']
    ax.scatter(x1, residuals, alpha=0.7, s=50, color='blue')
    ax.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Pressure (kPa)')
    ax.set_ylabel('Residuals (cm/s)')
    ax.set_title(f'Regime 1: Residuals of {best_model_name} model')
    ax.grid(True, alpha=0.3)

# Regime 2: Data and models
ax = axes[1, 0]
ax.scatter(x2, y2, alpha=0.7, s=50, label='Data', color='red')

# Plot models for Regime 2
x2_range = np.linspace(x2.min(), x2.max(), 200)
for model_name, model_result in models_regime2.items():
    if model_name == 'constant':
        y_pred_range = np.full_like(x2_range, model_result['value'])
    elif model_name == 'linear':
        y_pred_range = linear_model(x2_range, *model_result['params'])
    
    ax.plot(x2_range, y_pred_range, label=f'{model_name} (R²={model_result["r2"]:.3f})', 
            linewidth=2, alpha=0.8)

ax.set_xlabel('Pressure (kPa)')
ax.set_ylabel('Flame Speed (cm/s)')
ax.set_title('Regime 2: Model Fits')
ax.legend()
ax.grid(True, alpha=0.3)

# Regime 2: Residuals of best model
ax = axes[1, 1]
if 'best_model_name2' in locals():
    residuals2 = y2 - best_model2['y_pred']
    ax.scatter(x2, residuals2, alpha=0.7, s=50, color='red')
    ax.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Pressure (kPa)')
    ax.set_ylabel('Residuals (cm/s)')
    ax.set_title(f'Regime 2: Residuals of {best_model_name2} model')
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/model_fits.png', dpi=300, bbox_inches='tight')
plt.close()

# Create combined plot with both regimes and best models
plt.figure(figsize=(12, 7))

# Plot data
plt.scatter(x1, y1, alpha=0.7, s=60, label='Regime 1 Data', color='blue')
plt.scatter(x2, y2, alpha=0.7, s=60, label='Regime 2 Data', color='red')

# Plot best model for Regime 1
if 'best_model_name' in locals() and best_model_name in models_regime1:
    if best_model_name == 'quadratic':
        x1_poly_range = poly.transform(x1_range.reshape(-1, 1))
        y1_pred_range = models_regime1[best_model_name]['model'].predict(x1_poly_range)
    elif best_model_name == 'linear':
        y1_pred_range = linear_model(x1_range, *models_regime1[best_model_name]['params'])
    elif best_model_name == 'exponential':
        y1_pred_range = exponential_decay(x1_range, *models_regime1[best_model_name]['params'])
    elif best_model_name == 'power':
        y1_pred_range = power_law(x1_range, *models_regime1[best_model_name]['params'])
    
    plt.plot(x1_range, y1_pred_range, 'b-', linewidth=3, 
             label=f'Regime 1: {best_model_name} (R²={models_regime1[best_model_name]["r2"]:.3f})', 
             alpha=0.8)

# Plot best model for Regime 2
if 'best_model_name2' in locals() and best_model_name2 in models_regime2:
    if best_model_name2 == 'constant':
        y2_pred_range = np.full_like(x2_range, models_regime2[best_model_name2]['value'])
    elif best_model_name2 == 'linear':
        y2_pred_range = linear_model(x2_range, *models_regime2[best_model_name2]['params'])
    
    plt.plot(x2_range, y2_pred_range, 'r-', linewidth=3, 
             label=f'Regime 2: {best_model_name2} (R²={models_regime2[best_model_name2]["r2"]:.3f})', 
             alpha=0.8)

plt.axvline(x=82.403, color='gray', linestyle='--', alpha=0.7, 
           label=f'Regime boundary at 82.4 kPa')
plt.xlabel('Pressure (kPa)')
plt.ylabel('Flame Speed (cm/s)')
plt.title('Flame Speed vs Chamber Pressure with Best-Fit Models')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/best_models_combined.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nModeling complete. Figures saved to report/images/")

# Save model results
import json
model_results = {
    'regime1': {
        'best_model': best_model_name if 'best_model_name' in locals() else None,
        'models': {k: {'mse': v['mse'], 'r2': v['r2']} for k, v in models_regime1.items()}
    },
    'regime2': {
        'best_model': best_model_name2 if 'best_model_name2' in locals() else None,
        'models': {k: {'mse': v['mse'], 'r2': v['r2']} for k, v in models_regime2.items()}
    }
}

with open('../outputs/model_results.json', 'w') as f:
    json.dump(model_results, f, indent=2)

print("Model results saved to outputs/model_results.json")
