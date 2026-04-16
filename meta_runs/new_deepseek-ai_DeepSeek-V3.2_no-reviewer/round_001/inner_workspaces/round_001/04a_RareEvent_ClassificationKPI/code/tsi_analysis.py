import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Define TSI function according to specification
def calculate_tsi(x, epsilon=1e-12):
    """
    Calculate Temporal Stability Index (TSI) for a 1-D series x.
    
    Parameters:
    x: 1-D array-like series
    epsilon: small constant to avoid division by zero
    
    Returns:
    TSI value between 0 and 1
    """
    x = np.asarray(x)
    
    # If fewer than two samples, set TSI = 1.0
    if len(x) < 2:
        return 1.0
    
    # Calculate first differences
    d = np.diff(x)
    
    # Calculate population standard deviations (ddof=0)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Calculate TSI with bounds [0, 1]
    tsi = 1 - sigma_d / (sigma_x + epsilon)
    tsi = max(0, min(1, tsi))
    
    return tsi

# Load the data
def load_data():
    """Load the experiment traces data."""
    data_path = "../data/experiment_traces.csv"
    df = pd.read_csv(data_path)
    print(f"Data shape: {df.shape}")
    print(f"Data columns: {df.columns.tolist()}")
    print(f"First few rows:\n{df.head()}")
    print(f"Summary statistics:\n{df['model_output'].describe()}")
    return df

# Calculate TSI for the entire series
def calculate_overall_tsi(df):
    """Calculate TSI for the entire model_output series."""
    x = df['model_output'].values
    tsi = calculate_tsi(x)
    print(f"Overall TSI for entire series: {tsi:.6f}")
    return tsi

# Calculate rolling TSI to analyze temporal stability over windows
def calculate_rolling_tsi(df, window_size=100):
    """Calculate TSI over rolling windows."""
    x = df['model_output'].values
    n = len(x)
    
    # Initialize array for rolling TSI
    rolling_tsi = np.full(n, np.nan)
    
    # Calculate TSI for each window
    for i in range(window_size, n + 1):
        window = x[i-window_size:i]
        rolling_tsi[i-1] = calculate_tsi(window)
    
    return rolling_tsi

# Create visualizations
def create_visualizations(df, overall_tsi, rolling_tsi):
    """Create visualizations for the analysis."""
    # Ensure output directory exists
    os.makedirs("report/images", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    
    # 1. Time series plot of model_output
    plt.figure(figsize=(12, 6))
    plt.plot(df['frame'], df['model_output'], linewidth=0.5, alpha=0.7)
    plt.xlabel('Frame')
    plt.ylabel('Model Output')
    plt.title(f'Time Series of Model Output (Overall TSI = {overall_tsi:.4f})')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/model_output_time_series.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Histogram of model_output
    plt.figure(figsize=(10, 6))
    plt.hist(df['model_output'], bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel('Model Output')
    plt.ylabel('Frequency')
    plt.title('Distribution of Model Output Values')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/model_output_histogram.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Rolling TSI plot
    window_size = 100
    plt.figure(figsize=(12, 6))
    plt.plot(df['frame'][window_size-1:], rolling_tsi[window_size-1:], 
             linewidth=1.5, color='darkred', alpha=0.8)
    plt.axhline(y=overall_tsi, color='blue', linestyle='--', 
                linewidth=1.5, label=f'Overall TSI = {overall_tsi:.4f}')
    plt.xlabel('Frame')
    plt.ylabel('TSI')
    plt.title(f'Rolling Temporal Stability Index (Window Size = {window_size})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(-0.05, 1.05)
    plt.tight_layout()
    plt.savefig('report/images/rolling_tsi.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. First differences plot
    differences = np.diff(df['model_output'].values)
    plt.figure(figsize=(12, 6))
    plt.plot(df['frame'][1:], differences, linewidth=0.5, alpha=0.7, color='green')
    plt.xlabel('Frame')
    plt.ylabel('First Difference')
    plt.title('First Differences of Model Output')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/first_differences.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. Scatter plot of value vs difference
    plt.figure(figsize=(10, 6))
    plt.scatter(df['model_output'].values[:-1], differences, 
                s=1, alpha=0.5, color='purple')
    plt.xlabel('Model Output (t)')
    plt.ylabel('First Difference (t+1 - t)')
    plt.title('Model Output vs First Differences')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/output_vs_differences.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. Distribution of differences
    plt.figure(figsize=(10, 6))
    plt.hist(differences, bins=50, edgecolor='black', alpha=0.7, color='orange')
    plt.xlabel('First Difference')
    plt.ylabel('Frequency')
    plt.title('Distribution of First Differences')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/differences_histogram.png', dpi=300, bbox_inches='tight')
    plt.close()

# Save results to file
def save_results(df, overall_tsi, rolling_tsi):
    """Save analysis results to files."""
    # Save overall TSI
    with open('outputs/tsi_results.txt', 'w') as f:
        f.write(f'Temporal Stability Index Analysis\n')
        f.write(f'================================\n\n')
        f.write(f'Dataset: experiment_traces.csv\n')
        f.write(f'Number of samples: {len(df)}\n')
        f.write(f'Overall TSI: {overall_tsi:.6f}\n\n')
        
        # Calculate some additional statistics
        x = df['model_output'].values
        sigma_x = np.std(x, ddof=0)
        sigma_d = np.std(np.diff(x), ddof=0)
        
        f.write(f'Standard deviation of x (σ_x): {sigma_x:.6f}\n')
        f.write(f'Standard deviation of differences (σ_d): {sigma_d:.6f}\n')
        f.write(f'Ratio σ_d/σ_x: {sigma_d/(sigma_x + 1e-12):.6f}\n')
        
        # Rolling TSI statistics
        window_size = 100
        valid_tsi = rolling_tsi[window_size-1:]
        f.write(f'\nRolling TSI statistics (window={window_size}):\n')
        f.write(f'  Mean: {np.nanmean(valid_tsi):.6f}\n')
        f.write(f'  Std: {np.nanstd(valid_tsi):.6f}\n')
        f.write(f'  Min: {np.nanmin(valid_tsi):.6f}\n')
        f.write(f'  Max: {np.nanmax(valid_tsi):.6f}\n')
        f.write(f'  Median: {np.nanmedian(valid_tsi):.6f}\n')
    
    # Save rolling TSI data
    rolling_df = pd.DataFrame({
        'frame': df['frame'].values,
        'rolling_tsi': rolling_tsi
    })
    rolling_df.to_csv('outputs/rolling_tsi.csv', index=False)
    
    print("Results saved to outputs/ directory")

# Main analysis function
def main():
    """Main analysis pipeline."""
    print("Starting Temporal Stability Index Analysis...")
    
    # Load data
    df = load_data()
    
    # Calculate overall TSI
    overall_tsi = calculate_overall_tsi(df)
    
    # Calculate rolling TSI
    rolling_tsi = calculate_rolling_tsi(df, window_size=100)
    
    # Create visualizations
    create_visualizations(df, overall_tsi, rolling_tsi)
    
    # Save results
    save_results(df, overall_tsi, rolling_tsi)
    
    print("Analysis complete!")
    return overall_tsi, rolling_tsi

if __name__ == "__main__":
    overall_tsi, rolling_tsi = main()