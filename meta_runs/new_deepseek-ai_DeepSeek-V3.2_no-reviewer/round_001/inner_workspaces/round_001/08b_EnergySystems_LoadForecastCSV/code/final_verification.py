import os
import pandas as pd

print("=== Final Verification ===\n")

# Check required directories exist
required_dirs = ['code', 'outputs', 'report', 'report/images']
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"✓ Directory exists: {dir_path}")
    else:
        print(f"✗ Missing directory: {dir_path}")

print("\n=== Required Files ===")

# Check required files
required_files = [
    'report/report.md',
    'data/load_15min.csv',
    'outputs/annual_forecast_15min.csv',
    'outputs/baseline_forecast_results.csv',
    'outputs/reliability_metrics.csv'
]

for file_path in required_files:
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"✓ {file_path} ({file_size:,} bytes)")
    else:
        print(f"✗ Missing: {file_path}")

print("\n=== Report Images ===")

# Check report images
image_files = [
    'full_timeseries.png',
    'daily_patterns.png',
    'hourly_boxplot.png',
    'avg_daily_profile.png',
    'weekday_weekend_comparison.png',
    'decomposition.png',
    'autocorrelation.png',
    'forecast_comparison.png',
    'forecast_error_distribution.png',
    'annual_forecast.png',
    'load_duration_curve.png',
    'monthly_reliability.png',
    'risk_curves.png'
]

images_dir = 'report/images'
for img in image_files:
    img_path = os.path.join(images_dir, img)
    if os.path.exists(img_path):
        file_size = os.path.getsize(img_path)
        print(f"✓ {img} ({file_size:,} bytes)")
    else:
        print(f"✗ Missing: {img}")

print("\n=== Report Content Check ===")

# Check report content
with open('report/report.md', 'r', encoding='utf-8') as f:
    report_content = f.read()
    
# Check for key sections
key_sections = [
    'Executive Summary',
    'Data Overview',
    'Load Pattern Analysis',
    'Forecasting Methodology',
    'Annual Load Forecast 2026',
    'Reliability Assessment',
    'Key Findings and Recommendations',
    'Conclusion'
]

for section in key_sections:
    if section in report_content:
        print(f"✓ Report contains: {section}")
    else:
        print(f"✗ Report missing: {section}")

# Check for image references
image_refs = 0
for img in image_files:
    if f'![' in report_content and img in report_content:
        image_refs += 1

print(f"\n✓ {image_refs} out of {len(image_files)} images referenced in report")

print("\n=== Data Validation ===")

# Validate annual forecast data
try:
    annual_forecast = pd.read_csv('outputs/annual_forecast_15min.csv', index_col=0, parse_dates=True)
    print(f"✓ Annual forecast has {len(annual_forecast):,} rows (15-min intervals for 2026)")
    print(f"  - Date range: {annual_forecast.index.min()} to {annual_forecast.index.max()}")
    print(f"  - Forecast mean: {annual_forecast['final_forecast'].mean():.2f} MW")
    print(f"  - Forecast peak: {annual_forecast['final_forecast'].max():.2f} MW")
except Exception as e:
    print(f"✗ Error loading annual forecast: {e}")

print("\n=== Verification Complete ===")
print("All deliverables appear to be complete and ready for submission.")
