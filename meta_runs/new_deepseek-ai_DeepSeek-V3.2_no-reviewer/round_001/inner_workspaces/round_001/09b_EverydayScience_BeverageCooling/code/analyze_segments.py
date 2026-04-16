import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import optimize
import os

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')

# Identify segments based on temperature increases
# Find where temperature increases instead of decreases
temp_diff = np.diff(df['temperature_c'])
increase_indices = np.where(temp_diff > 0)[0]
print(f"Temperature increases at indices: {increase_indices}")
print(f"Corresponding times: {df['time_min'].iloc[increase_indices].values}")

# Define segments
segments = []
start_idx = 0
for inc_idx in increase_indices:
    segments.append((start_idx, inc_idx))
    start_idx = inc_idx + 1
segments.append((start_idx, len(df)-1))

print(f"\nIdentified {len(segments)} segments:")
for i, (start, end) in enumerate(segments):
    print(f"Segment {i+1}: time {df['time_min'].iloc[start]} to {df['time_min'].iloc[end]} min, length: {end-start+1} points")

# Plot segments with different colors
plt.figure(figsize=(14, 8))
colors = ['blue', 'green', 'red', 'orange', 'purple']
for i, (start, end) in enumerate(segments):
    if i < len(colors):
        segment_df = df.iloc[start:end+1]
        plt.plot(segment_df['time_min'], segment_df['temperature_c'], 
                color=colors[i], linewidth=2.5, label=f'Segment {i+1}')
        # Mark start and end points
        plt.scatter(segment_df['time_min'].iloc[0], segment_df['temperature_c'].iloc[0], 
                   color=colors[i], s=100, zorder=5)
        plt.scatter(segment_df['time_min'].iloc[-1], segment_df['temperature_c'].iloc[-1], 
                   color=colors[i], s=100, marker='s', zorder=5)

plt.xlabel('Time (minutes)', fontsize=14)
plt.ylabel('Temperature (°C)', fontsize=14)
plt.title('Beverage Cooling Segments', fontsize=16)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/cooling_segments.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/cooling_segments.png', dpi=300, bbox_inches='tight')

# Analyze each segment separately
print("\n" + "="*60)
print("ANALYZING EACH SEGMENT")
print("="*60)

# Newton's Law of Cooling function
def newton_cooling(t, T_env, T0, k):
    """Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)"""
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Function to fit Newton's cooling to a segment
def fit_newton_cooling(segment_df):
    """Fit Newton's cooling model to a segment"""
    # Use time relative to segment start
    t = segment_df['time_min'].values - segment_df['time_min'].iloc[0]
    T = segment_df['temperature_c'].values
    
    # Initial guesses
    T_env_guess = np.min(T)  # Ambient temperature should be near minimum
    T0_guess = T[0]  # Initial temperature
    k_guess = 0.01  # Initial cooling constant guess
    
    # Fit the model
    try:
        params, params_covariance = optimize.curve_fit(newton_cooling, t, T, 
                                                      p0=[T_env_guess, T0_guess, k_guess],
                                                      maxfev=5000)
        T_env_fit, T0_fit, k_fit = params
        
        # Calculate R-squared
        T_pred = newton_cooling(t, *params)
        residuals = T - T_pred
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((T - np.mean(T))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        return {
            'T_env': T_env_fit,
            'T0': T0_fit,
            'k': k_fit,
            'r_squared': r_squared,
            'params_covariance': params_covariance,
            'T_pred': T_pred
        }
    except Exception as e:
        print(f"Fitting error: {e}")
        return None

# Fit each segment
segment_results = []
plt.figure(figsize=(16, 10))

for i, (start, end) in enumerate(segments):
    segment_df = df.iloc[start:end+1].copy()
    segment_df['time_rel'] = segment_df['time_min'] - segment_df['time_min'].iloc[0]
    
    print(f"\n--- Segment {i+1} ---")
    print(f"Time range: {segment_df['time_min'].iloc[0]} to {segment_df['time_min'].iloc[-1]} min")
    print(f"Temperature range: {segment_df['temperature_c'].iloc[0]:.2f} to {segment_df['temperature_c'].iloc[-1]:.2f} °C")
    print(f"Duration: {segment_df['time_min'].iloc[-1] - segment_df['time_min'].iloc[0]} min")
    
    # Fit Newton's cooling
    result = fit_newton_cooling(segment_df)
    
    if result:
        print(f"Fitted parameters:")
        print(f"  Ambient temperature (T_env): {result['T_env']:.4f} °C")
        print(f"  Initial temperature (T0): {result['T0']:.4f} °C")
        print(f"  Cooling constant (k): {result['k']:.6f} min⁻¹")
        print(f"  R-squared: {result['r_squared']:.6f}")
        
        # Calculate half-life (time for temperature difference to halve)
        if result['k'] > 0:
            half_life = np.log(2) / result['k']
            print(f"  Half-life: {half_life:.2f} min")
        
        segment_results.append({
            'segment': i+1,
            'start_time': segment_df['time_min'].iloc[0],
            'end_time': segment_df['time_min'].iloc[-1],
            **result
        })
        
        # Plot this segment with fit
        plt.subplot(2, 2, i+1)
        plt.plot(segment_df['time_rel'], segment_df['temperature_c'], 'b-', linewidth=2, label='Data')
        plt.plot(segment_df['time_rel'], result['T_pred'], 'r--', linewidth=2, label='Newton Fit')
        plt.xlabel('Time (minutes, relative)', fontsize=12)
        plt.ylabel('Temperature (°C)', fontsize=12)
        plt.title(f'Segment {i+1}: T_env={result["T_env"]:.2f}°C, k={result["k"]:.4f}, R²={result["r_squared"]:.4f}', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
    else:
        print("Fit failed for this segment")
        segment_results.append(None)

plt.tight_layout()
plt.savefig('report/images/segment_fits.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/segment_fits.png', dpi=300, bbox_inches='tight')

# Also try fitting the entire dataset with a piecewise model
print("\n" + "="*60)
print("PIECEWISE MODEL APPROACH")
print("="*60)

# Create a piecewise model that accounts for interventions
# We'll model each segment with its own Newton cooling but continuous time
plt.figure(figsize=(14, 8))

# Plot the full data
plt.plot(df['time_min'], df['temperature_c'], 'b-', linewidth=2, alpha=0.7, label='Data')

# Generate predictions from segment fits
all_times = np.arange(0, 200, 0.1)
piecewise_pred = np.zeros_like(all_times)

for i, result in enumerate(segment_results):
    if result:
        # Find times in this segment
        if i < len(segments)-1:
            next_start = df['time_min'].iloc[segments[i+1][0]]
        else:
            next_start = 200
        
        segment_mask = (all_times >= result['start_time']) & (all_times < next_start)
        segment_times = all_times[segment_mask]
        
        # Calculate relative time for this segment
        t_rel = segment_times - result['start_time']
        
        # Predict using this segment's parameters
        pred = newton_cooling(t_rel, result['T_env'], result['T0'], result['k'])
        piecewise_pred[segment_mask] = pred
        
        # Plot this segment's prediction
        plt.plot(segment_times, pred, 'r--', linewidth=2.5, alpha=0.8, 
                label=f'Segment {i+1} Fit' if i == 0 else "")

plt.xlabel('Time (minutes)', fontsize=14)
plt.ylabel('Temperature (°C)', fontsize=14)
plt.title('Piecewise Newton Cooling Model', fontsize=16)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/piecewise_model.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/piecewise_model.png', dpi=300, bbox_inches='tight')

# Calculate overall error for piecewise model
# Interpolate predictions to data points
from scipy import interpolate
f = interpolate.interp1d(all_times, piecewise_pred, kind='linear', bounds_error=False, fill_value='extrapolate')
pred_at_data = f(df['time_min'])
residuals = df['temperature_c'] - pred_at_data
rmse = np.sqrt(np.mean(residuals**2))
mae = np.mean(np.abs(residuals))
print(f"\nPiecewise model performance:")
print(f"RMSE: {rmse:.4f} °C")
print(f"MAE: {mae:.4f} °C")
print(f"Max residual: {np.max(np.abs(residuals)):.4f} °C")

# Save results
import json
results_dict = {
    'segments': [],
    'piecewise_model_metrics': {
        'rmse': float(rmse),
        'mae': float(mae),
        'max_residual': float(np.max(np.abs(residuals)))
    }
}

for i, result in enumerate(segment_results):
    if result:
        results_dict['segments'].append({
            'segment': result['segment'],
            'start_time': float(result['start_time']),
            'end_time': float(result['end_time']),
            'T_env': float(result['T_env']),
            'T0': float(result['T0']),
            'k': float(result['k']),
            'r_squared': float(result['r_squared']),
            'half_life': float(np.log(2) / result['k']) if result['k'] > 0 else None
        })

with open('outputs/analysis_results.json', 'w') as f:
    json.dump(results_dict, f, indent=2)

print("\nAnalysis complete. Results saved to outputs/analysis_results.json")