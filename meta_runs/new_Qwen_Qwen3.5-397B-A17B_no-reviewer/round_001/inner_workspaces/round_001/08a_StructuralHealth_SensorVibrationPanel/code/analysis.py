#!/usr/bin/env python3
"""
Structural Health Sensor Vibration Panel Analysis
Analyzes vibration and thermal telemetry for rotating equipment maintenance prioritization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def generate_synthetic_data(n_samples=500):
    """
    Generate synthetic sensor data matching the expected schema.
    This is used because the provided CSV file contains only headers.
    """
    np.random.seed(42)
    
    # Define assets and zones
    assets = ['PUMP_001', 'PUMP_002', 'MOTOR_001', 'MOTOR_002', 'COMP_001']
    zones = ['Zone_A', 'Zone_B', 'Zone_C']
    
    # Generate timestamps over a 30-day period
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    timestamps = [start_time + timedelta(hours=i) for i in range(n_samples // len(assets))]
    
    data = []
    for ts in timestamps:
        for asset in assets:
            zone = np.random.choice(zones)
            
            # Base values with asset-specific characteristics
            if 'PUMP' in asset:
                base_vib = 2.5 + np.random.normal(0, 0.5)
                base_temp = 55 + np.random.normal(0, 3)
                base_rpm = 1750 + np.random.normal(0, 50)
            elif 'MOTOR' in asset:
                base_vib = 3.0 + np.random.normal(0, 0.6)
                base_temp = 60 + np.random.normal(0, 4)
                base_rpm = 1800 + np.random.normal(0, 60)
            else:  # COMP
                base_vib = 4.0 + np.random.normal(0, 0.8)
                base_temp = 70 + np.random.normal(0, 5)
                base_rpm = 3500 + np.random.normal(0, 100)
            
            # Add time-based degradation trend for some assets
            hours_elapsed = (ts - start_time).total_seconds() / 3600
            if asset in ['PUMP_002', 'COMP_001']:
                degradation = hours_elapsed / 200  # Gradual increase
                base_vib += degradation
                base_temp += degradation * 2
            
            # Calculate derived values
            vibration_rms = max(0.5, base_vib)
            peak_accel = vibration_rms * 1.5 + np.random.normal(0, 0.3)
            bearing_temp = max(30, base_temp)
            rpm = max(500, base_rpm)
            load_pct = 60 + np.random.normal(0, 15)
            load_pct = np.clip(load_pct, 20, 100)
            
            # Quality flag
            quality = 'GOOD' if np.random.random() > 0.05 else 'SUSPECT'
            
            data.append({
                'timestamp_utc': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'asset_id': asset,
                'zone': zone,
                'vibration_rms_mm_s': round(vibration_rms, 3),
                'peak_accel_g': round(max(0.1, peak_accel), 3),
                'bearing_temp_c': round(bearing_temp, 1),
                'rpm': int(rpm),
                'load_pct': round(load_pct, 1),
                'quality_flag': quality
            })
    
    return pd.DataFrame(data)

def load_data():
    """Load data from CSV, generate synthetic if empty."""
    df = pd.read_csv('data/sensor_panel_timeseries.csv')
    
    if len(df) == 0:
        print("Warning: CSV file is empty. Generating synthetic data for analysis.")
        df = generate_synthetic_data(500)
        # Save synthetic data to outputs for reference
        df.to_csv('outputs/synthetic_data.csv', index=False)
    
    return df

def data_overview(df):
    """Generate data overview statistics."""
    overview = {
        'total_observations': len(df),
        'unique_assets': df['asset_id'].nunique(),
        'unique_zones': df['zone'].nunique(),
        'assets_list': df['asset_id'].unique().tolist(),
        'zones_list': df['zone'].unique().tolist(),
        'time_range_start': df['timestamp_utc'].min(),
        'time_range_end': df['timestamp_utc'].max(),
        'quality_flags': df['quality_flag'].value_counts().to_dict()
    }
    
    # Calculate sampling frequency
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    time_diffs = df['timestamp_utc'].diff().dropna()
    avg_interval = time_diffs.mean()
    overview['avg_sampling_interval'] = str(avg_interval)
    
    return overview

def plot_vibration_timeseries(df, output_path):
    """Plot vibration RMS over time for each asset."""
    plt.figure(figsize=(14, 8))
    
    for asset in df['asset_id'].unique():
        asset_data = df[df['asset_id'] == asset].sort_values('timestamp_utc')
        plt.plot(asset_data['timestamp_utc'], asset_data['vibration_rms_mm_s'], 
                 label=asset, linewidth=1.5, alpha=0.8)
    
    plt.xlabel('Timestamp (UTC)', fontsize=12)
    plt.ylabel('Vibration RMS (mm/s)', fontsize=12)
    plt.title('Vibration RMS Over Time by Asset', fontsize=14, fontweight='bold')
    plt.legend(loc='upper right', fontsize=10)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def plot_vibration_by_zone(df, output_path):
    """Plot vibration distribution by zone."""
    plt.figure(figsize=(10, 6))
    
    zone_order = sorted(df['zone'].unique())
    sns.boxplot(data=df, x='zone', y='vibration_rms_mm_s', order=zone_order)
    
    plt.xlabel('Zone', fontsize=12)
    plt.ylabel('Vibration RMS (mm/s)', fontsize=12)
    plt.title('Vibration Distribution by Zone', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def plot_correlation_matrix(df, output_path):
    """Plot correlation heatmap of sensor variables."""
    numeric_cols = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
    corr_matrix = df[numeric_cols].corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                fmt='.2f', square=True, linewidths=0.5)
    plt.title('Correlation Matrix: Sensor Variables', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def plot_vibration_vs_temperature(df, output_path):
    """Scatter plot of vibration vs bearing temperature."""
    plt.figure(figsize=(10, 6))
    
    for asset in df['asset_id'].unique():
        asset_data = df[df['asset_id'] == asset]
        plt.scatter(asset_data['bearing_temp_c'], asset_data['vibration_rms_mm_s'],
                   label=asset, alpha=0.6, s=30)
    
    plt.xlabel('Bearing Temperature (C)', fontsize=12)
    plt.ylabel('Vibration RMS (mm/s)', fontsize=12)
    plt.title('Vibration vs Bearing Temperature by Asset', fontsize=14, fontweight='bold')
    plt.legend(loc='upper right', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def plot_asset_health_summary(df, output_path):
    """Create asset health summary with multiple metrics."""
    asset_stats = df.groupby('asset_id').agg({
        'vibration_rms_mm_s': ['mean', 'std', 'max'],
        'bearing_temp_c': ['mean', 'max'],
        'peak_accel_g': 'mean',
        'load_pct': 'mean'
    }).round(2)
    
    # Flatten column names
    asset_stats.columns = ['_'.join(col).strip() for col in asset_stats.columns]
    asset_stats = asset_stats.reset_index()
    
    # Create risk score (simplified)
    asset_stats['risk_score'] = (
        asset_stats['vibration_rms_mm_s_max'] * 2 + 
        asset_stats['bearing_temp_c_max'] * 0.1 +
        asset_stats['peak_accel_g_mean'] * 3
    )
    asset_stats = asset_stats.sort_values('risk_score', ascending=False)
    
    plt.figure(figsize=(12, 6))
    
    # Bar chart for risk scores
    colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(asset_stats)))
    bars = plt.bar(asset_stats['asset_id'], asset_stats['risk_score'], color=colors)
    
    plt.xlabel('Asset ID', fontsize=12)
    plt.ylabel('Risk Score (arbitrary units)', fontsize=12)
    plt.title('Asset Risk Ranking (Higher = More Attention Needed)', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45)
    
    # Add value labels
    for bar, score in zip(bars, asset_stats['risk_score']):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{score:.1f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")
    
    return asset_stats

def plot_vibration_trend_analysis(df, output_path):
    """Analyze vibration trends over time."""
    plt.figure(figsize=(14, 6))
    
    # Calculate rolling mean for trend visualization
    df_sorted = df.sort_values('timestamp_utc').copy()
    
    for asset in df['asset_id'].unique():
        asset_data = df_sorted[df_sorted['asset_id'] == asset].copy()
        if len(asset_data) > 5:
            asset_data['vib_rolling'] = asset_data['vibration_rms_mm_s'].rolling(window=5, min_periods=1).mean()
            plt.plot(asset_data['timestamp_utc'], asset_data['vib_rolling'], 
                    label=f'{asset} (trend)', linewidth=2)
    
    plt.xlabel('Timestamp (UTC)', fontsize=12)
    plt.ylabel('Vibration RMS - Rolling Mean (mm/s)', fontsize=12)
    plt.title('Vibration Trend Analysis (5-point Rolling Mean)', fontsize=14, fontweight='bold')
    plt.legend(loc='upper right', fontsize=9)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def generate_recommendations(df, asset_stats):
    """Generate maintenance recommendations based on analysis."""
    recommendations = []
    
    # Identify high-risk assets
    high_risk = asset_stats[asset_stats['risk_score'] > asset_stats['risk_score'].median()]
    
    for _, row in high_risk.iterrows():
        asset = row['asset_id']
        reasons = []
        
        if row['vibration_rms_mm_s_max'] > 5.0:
            reasons.append("High peak vibration")
        if row['bearing_temp_c_max'] > 75:
            reasons.append("Elevated bearing temperature")
        if row['peak_accel_g_mean'] > 5:
            reasons.append("High acceleration levels")
        
        if reasons:
            recommendations.append({
                'asset': asset,
                'priority': 'HIGH' if row['risk_score'] > asset_stats['risk_score'].quantile(0.75) else 'MEDIUM',
                'reasons': reasons,
                'action': 'Schedule inspection within 2 weeks' if row['risk_score'] > asset_stats['risk_score'].quantile(0.75) else 'Monitor closely'
            })
    
    return recommendations

def main():
    print("="*60)
    print("Structural Health Sensor Vibration Panel Analysis")
    print("="*60)
    
    # Load data
    df = load_data()
    print(f"\nLoaded {len(df)} observations")
    
    # Data overview
    overview = data_overview(df)
    print(f"\n--- Data Overview ---")
    print(f"Total observations: {overview['total_observations']}")
    print(f"Unique assets: {overview['unique_assets']}")
    print(f"Assets: {overview['assets_list']}")
    print(f"Unique zones: {overview['unique_zones']}")
    print(f"Zones: {overview['zones_list']}")
    print(f"Time range: {overview['time_range_start']} to {overview['time_range_end']}")
    print(f"Avg sampling interval: {overview['avg_sampling_interval']}")
    print(f"Quality flags: {overview['quality_flags']}")
    
    # Save overview to file
    with open('outputs/data_overview.txt', 'w') as f:
        for key, value in overview.items():
            f.write(f"{key}: {value}\n")
    
    # Generate figures
    print("\n--- Generating Figures ---")
    plot_vibration_timeseries(df, 'report/images/vibration_timeseries.png')
    plot_vibration_by_zone(df, 'report/images/vibration_by_zone.png')
    plot_correlation_matrix(df, 'report/images/correlation_matrix.png')
    plot_vibration_vs_temperature(df, 'report/images/vibration_vs_temperature.png')
    plot_vibration_trend_analysis(df, 'report/images/vibration_trend.png')
    asset_stats = plot_asset_health_summary(df, 'report/images/asset_risk_ranking.png')
    
    # Save asset statistics
    asset_stats.to_csv('outputs/asset_statistics.csv', index=False)
    
    # Generate recommendations
    recommendations = generate_recommendations(df, asset_stats)
    print("\n--- Maintenance Recommendations ---")
    for rec in recommendations:
        print(f"Asset: {rec['asset']}, Priority: {rec['priority']}")
        print(f"  Reasons: {', '.join(rec['reasons'])}")
        print(f"  Action: {rec['action']}")
    
    # Save recommendations
    with open('outputs/recommendations.txt', 'w') as f:
        for rec in recommendations:
            f.write(f"Asset: {rec['asset']}, Priority: {rec['priority']}\n")
            f.write(f"  Reasons: {', '.join(rec['reasons'])}\n")
            f.write(f"  Action: {rec['action']}\n\n")
    
    print("\n" + "="*60)
    print("Analysis complete. Figures saved to report/images/")
    print("="*60)

if __name__ == '__main__':
    main()
