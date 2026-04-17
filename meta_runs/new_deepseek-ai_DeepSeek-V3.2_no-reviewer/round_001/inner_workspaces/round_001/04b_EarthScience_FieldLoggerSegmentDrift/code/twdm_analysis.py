import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt


def compute_twdm(x, epsilon):
    """
    Compute TWDM (Three-Window Drift Metric) for a series x.
    
    Parameters:
    x: list or array of numeric values
    epsilon: small constant to avoid division by zero
    
    Returns:
    twdm: float or np.nan if insufficient length
    """
    n = len(x)
    
    # If n < 3, TWDM is undefined
    if n < 3:
        return np.nan
    
    # Split into three windows
    n1 = n // 3
    n2 = n // 3
    n3 = n - n1 - n2
    
    # Calculate means of each window
    m1 = np.mean(x[:n1])
    m2 = np.mean(x[n1:n1+n2])
    m3 = np.mean(x[n1+n2:])
    
    # Calculate delta (range of means)
    delta = max(m1, m2, m3) - min(m1, m2, m3)
    
    # Calculate population standard deviation (ddof=0)
    sigma = np.std(x, ddof=0)
    
    # Compute TWDM
    twdm = delta / (sigma + epsilon)
    
    return twdm


def load_data():
    """Load the soil logger readings and manifest."""
    # Load soil logger readings
    df = pd.read_csv('../data/soil_logger_readings.csv')
    
    # Load manifest
    with open('../data/twdm_audit_manifest.json', 'r') as f:
        manifest = json.load(f)
    
    return df, manifest


def validate_golden_cases(manifest):
    """Validate golden cases and compute maximum absolute error."""
    epsilon = manifest['epsilon']
    golden_cases = manifest['golden_cases']
    
    max_error = 0.0
    errors = []
    
    for case in golden_cases:
        readings = case['readings']
        expected = case['expected_twdm']
        
        # Compute TWDM
        computed = compute_twdm(readings, epsilon)
        
        # Calculate absolute error
        error = abs(computed - expected)
        errors.append(error)
        max_error = max(max_error, error)
        
        print(f"Golden case '{case['name']}':")
        print(f"  Expected: {expected}")
        print(f"  Computed: {computed}")
        print(f"  Error: {error}")
        print()
    
    return max_error


def analyze_segments(df, manifest):
    """Analyze all segments and create results table."""
    epsilon = manifest['epsilon']
    threshold = manifest['twdm_pass_threshold']
    segment_order = manifest['segment_report_order']
    
    results = []
    
    for segment_id in segment_order:
        # Get data for this segment
        segment_data = df[df['segment_id'] == segment_id].copy()
        
        # Sort by frame ascending
        segment_data = segment_data.sort_values('frame')
        
        # Extract vwc_pct as series
        x = segment_data['vwc_pct'].values
        n = len(x)
        
        # Compute TWDM if possible
        if n < 3:
            twdm = np.nan
            pass_fail = 'INSUFFICIENT_LENGTH'
        else:
            twdm = compute_twdm(x, epsilon)
            if twdm <= threshold:
                pass_fail = 'PASS'
            else:
                pass_fail = 'FAIL'
        
        results.append({
            'segment_id': segment_id,
            'n_frames': n,
            'TWDM': twdm,
            'pass_fail': pass_fail
        })
    
    return pd.DataFrame(results)


def plot_segment(df, segment_id, save_path):
    """Plot vwc_pct vs frame for a segment."""
    # Get data for this segment
    segment_data = df[df['segment_id'] == segment_id].copy()
    
    # Sort by frame ascending
    segment_data = segment_data.sort_values('frame')
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(segment_data['frame'], segment_data['vwc_pct'], 
             marker='o', markersize=3, linewidth=1)
    plt.xlabel('Frame')
    plt.ylabel('VWC (%)')
    plt.title(f'Soil Moisture (VWC) vs Frame for Segment {segment_id}')
    plt.grid(True, alpha=0.3)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    
    print(f"Plot saved to {save_path}")


def main():
    """Main analysis function."""
    print("Loading data...")
    df, manifest = load_data()
    
    print("\nValidating golden cases...")
    max_error = validate_golden_cases(manifest)
    print(f"Maximum absolute error: {max_error}")
    
    print("\nAnalyzing segments...")
    results_df = analyze_segments(df, manifest)
    
    # Save results
    results_df.to_csv('../outputs/twdm_results.csv', index=False)
    print(f"Results saved to ../outputs/twdm_results.csv")
    
    # Create a plot for one segment (choose first segment with sufficient data)
    segment_order = manifest['segment_report_order']
    for segment_id in segment_order:
        segment_data = df[df['segment_id'] == segment_id]
        if len(segment_data) >= 3:
            plot_segment(df, segment_id, '../report/images/segment_plot.png')
            break
    
    # Also create a summary plot with all segments
    plt.figure(figsize=(12, 8))
    for i, segment_id in enumerate(segment_order, 1):
        segment_data = df[df['segment_id'] == segment_id].copy()
        segment_data = segment_data.sort_values('frame')
        
        plt.subplot(3, 2, i)
        plt.plot(segment_data['frame'], segment_data['vwc_pct'], 
                 marker='o', markersize=2, linewidth=0.5)
        plt.xlabel('Frame')
        plt.ylabel('VWC (%)')
        plt.title(f'Segment {segment_id}')
        plt.grid(True, alpha=0.3)
        
        # Add TWDM info if available
        if len(segment_data) >= 3:
            twdm = compute_twdm(segment_data['vwc_pct'].values, manifest['epsilon'])
            plt.text(0.05, 0.95, f'TWDM: {twdm:.3f}', 
                    transform=plt.gca().transAxes, 
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('../report/images/all_segments.png', dpi=150)
    plt.close()
    print("All segments plot saved to report/images/all_segments.png")
    
    return max_error, results_df


if __name__ == '__main__':
    max_error, results_df = main()
    
    # Print results table
    print("\n" + "="*60)
    print("TWDM Analysis Results:")
    print("="*60)
    print(results_df.to_string(index=False))
    print("="*60)
    print(f"\nMaximum absolute error from golden cases: {max_error}")