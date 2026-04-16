import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import norm
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
data = pd.read_csv('data/beverage_temperature_series.csv')
time = data['time_min'].values
temp = data['temperature_c'].values

print("Data Overview:")
print(f"Time range: {time.min()} to {time.max()} minutes")
print(f"Temperature range: {temp.min():.2f} to {temp.max():.2f} °C")
print(f"Number of data points: {len(time)}")

# Newton's Law of Cooling: T(t) = T_ambient + (T_initial - T_ambient) * exp(-k*t)
def newton_cooling(t, T_ambient, T_initial, k):
    return T_ambient + (T_initial - T_ambient) * np.exp(-k * t)

# Initial parameter estimates
T_initial_est = temp[0]  # 85°C
T_ambient_est = temp[-1]  # Around 31°C (final temperature)
k_est = 0.01  # Initial guess for cooling constant

print(f"\nInitial estimates:")
print(f"T_initial: {T_initial_est}°C")
print(f"T_ambient: {T_ambient_est:.2f}°C")
print(f"k: {k_est}")

# Fit the model
try:
    popt, pcov = curve_fit(
        newton_cooling, 
        time, 
        temp,
        p0=[T_ambient_est, T_initial_est, k_est],
        bounds=([0, 50, 0], [50, 100, 1]),  # Reasonable bounds
        maxfev=10000
    )
    T_ambient_fit, T_initial_fit, k_fit = popt
    perr = np.sqrt(np.diag(pcov))
    
    print(f"\nFitted Parameters:")
    print(f"T_ambient = {T_ambient_fit:.3f} ± {perr[0]:.3f} °C")
    print(f"T_initial = {T_initial_fit:.3f} ± {perr[1]:.3f} °C")
    print(f"k = {k_fit:.6f} ± {perr[2]:.6f} min⁻¹")
    
    # Calculate time constant (tau = 1/k)
    tau = 1 / k_fit
    tau_err = perr[2] / (k_fit ** 2)
    print(f"\nTime constant (τ = 1/k): {tau:.2f} ± {tau_err:.2f} minutes")
    
    # Calculate half-life (time to reach halfway between T_initial and T_ambient)
    half_life = np.log(2) / k_fit
    print(f"Half-life: {half_life:.2f} minutes")
    
    # Generate fitted curve
    time_fine = np.linspace(0, time.max(), 500)
    temp_fit = newton_cooling(time_fine, T_ambient_fit, T_initial_fit, k_fit)
    
    # Calculate residuals
    temp_predicted = newton_cooling(time, T_ambient_fit, T_initial_fit, k_fit)
    residuals = temp - temp_predicted
    
    # Calculate R-squared
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((temp - np.mean(temp)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    print(f"\nR-squared: {r_squared:.6f}")
    
    # RMSE
    rmse = np.sqrt(np.mean(residuals ** 2))
    print(f"RMSE: {rmse:.3f} °C")
    
    # Save results
    results = {
        'T_ambient': T_ambient_fit,
        'T_ambient_err': perr[0],
        'T_initial': T_initial_fit,
        'T_initial_err': perr[1],
        'k': k_fit,
        'k_err': perr[2],
        'tau': tau,
        'tau_err': tau_err,
        'half_life': half_life,
        'r_squared': r_squared,
        'rmse': rmse
    }
    
    # Save to file
    with open('outputs/fit_results.txt', 'w') as f:
        f.write("Newton's Law of Cooling Fit Results\n")
        f.write("="*50 + "\n\n")
        f.write(f"Model: T(t) = T_ambient + (T_initial - T_ambient) * exp(-k*t)\n\n")
        f.write(f"Fitted Parameters:\n")
        f.write(f"  T_ambient = {T_ambient_fit:.4f} ± {perr[0]:.4f} °C\n")
        f.write(f"  T_initial = {T_initial_fit:.4f} ± {perr[1]:.4f} °C\n")
        f.write(f"  k = {k_fit:.6f} ± {perr[2]:.6f} min⁻¹\n\n")
        f.write(f"Derived Quantities:\n")
        f.write(f"  Time constant (τ) = {tau:.2f} ± {tau_err:.2f} minutes\n")
        f.write(f"  Half-life = {half_life:.2f} minutes\n\n")
        f.write(f"Goodness of Fit:\n")
        f.write(f"  R-squared = {r_squared:.6f}\n")
        f.write(f"  RMSE = {rmse:.4f} °C\n")
    
    # Create Figure 1: Temperature vs Time with Fit
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(time, temp, s=10, alpha=0.7, label='Observed Data', color='blue')
    ax.plot(time_fine, temp_fit, 'r-', linewidth=2, label=f'Newton\'s Law Fit (R² = {r_squared:.4f})')
    ax.axhline(y=T_ambient_fit, color='green', linestyle='--', linewidth=1.5, 
               label=f'Ambient Temperature = {T_ambient_fit:.1f}°C')
    ax.set_xlabel('Time (minutes)', fontsize=12)
    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('Beverage Cooling: Temperature vs Time', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/temperature_vs_time.png', dpi=150)
    plt.close()
    print("\nFigure 1 saved: report/images/temperature_vs_time.png")
    
    # Create Figure 2: Residuals Plot
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    # Residuals vs Time
    axes[0].scatter(time, residuals, s=10, alpha=0.7, color='blue')
    axes[0].axhline(y=0, color='red', linestyle='-', linewidth=1)
    axes[0].set_xlabel('Time (minutes)', fontsize=12)
    axes[0].set_ylabel('Residuals (°C)', fontsize=12)
    axes[0].set_title('Residuals vs Time', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    
    # Histogram of residuals
    axes[1].hist(residuals, bins=30, edgecolor='black', alpha=0.7, density=True)
    x_range = np.linspace(residuals.min(), residuals.max(), 100)
    axes[1].plot(x_range, norm.pdf(x_range, 0, np.std(residuals)), 'r-', linewidth=2, label='Normal Distribution')
    axes[1].set_xlabel('Residuals (°C)', fontsize=12)
    axes[1].set_ylabel('Density', fontsize=12)
    axes[1].set_title('Distribution of Residuals', fontsize=14)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/residuals_analysis.png', dpi=150)
    plt.close()
    print("Figure 2 saved: report/images/residuals_analysis.png")
    
    # Create Figure 3: Semi-log plot (ln(T - T_ambient) vs time)
    # This should be linear if Newton's Law holds
    temp_diff = temp - T_ambient_fit
    temp_diff_fit = T_initial_fit - T_ambient_fit
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(time, np.log(temp_diff), s=10, alpha=0.7, label='Data', color='blue')
    ax.plot(time_fine, np.log(temp_diff_fit) - k_fit * time_fine, 'r-', linewidth=2, label='Linear Fit')
    ax.set_xlabel('Time (minutes)', fontsize=12)
    ax.set_ylabel('ln(T - T_ambient)', fontsize=12)
    ax.set_title('Semi-log Plot: Verification of Newton\'s Law of Cooling', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/semilog_verification.png', dpi=150)
    plt.close()
    print("Figure 3 saved: report/images/semilog_verification.png")
    
    # Identify anomalies (large residuals)
    anomaly_threshold = 2 * np.std(residuals)
    anomalies = np.abs(residuals) > anomaly_threshold
    anomaly_times = time[anomalies]
    anomaly_temps = temp[anomalies]
    anomaly_residuals = residuals[anomalies]
    
    print(f"\nAnomalies detected (|residual| > {anomaly_threshold:.2f}°C):")
    if len(anomaly_times) > 0:
        for t, te, r in zip(anomaly_times, anomaly_temps, anomaly_residuals):
            print(f"  t={t} min: T={te:.2f}°C, residual={r:.2f}°C")
    else:
        print("  None detected")
    
    # Save anomaly data
    anomaly_df = pd.DataFrame({
        'time_min': anomaly_times,
        'temperature_c': anomaly_temps,
        'residual': anomaly_residuals
    })
    anomaly_df.to_csv('outputs/anomalies.csv', index=False)
    
except Exception as e:
    print(f"Error during fitting: {e}")
    import traceback
    traceback.print_exc()

print("\nAnalysis complete!")
