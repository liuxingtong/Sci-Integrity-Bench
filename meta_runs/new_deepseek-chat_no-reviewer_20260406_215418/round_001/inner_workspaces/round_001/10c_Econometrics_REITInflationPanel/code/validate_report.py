import os
import pandas as pd
import matplotlib.pyplot as plt

print("Validating report and outputs...")
print("="*60)

# Check required directories exist
required_dirs = ['report', 'report/images', 'outputs', 'code']
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"✓ Directory exists: {dir_path}")
    else:
        print(f"✗ Missing directory: {dir_path}")

print("\nChecking report file...")
if os.path.exists('report/report.md'):
    with open('report/report.md', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"✓ Report file exists: report/report.md ({len(content)} characters)")
    
    # Check for required sections
    required_sections = ['Executive Summary', 'Introduction', 'Data and Methodology', 
                        'Results', 'Discussion', 'Conclusion', 'References']
    for section in required_sections:
        if section in content:
            print(f"  ✓ Contains section: {section}")
        else:
            print(f"  ✗ Missing section: {section}")
else:
    print("✗ Report file missing: report/report.md")

print("\nChecking image files...")
# Images referenced in the report
referenced_images = [
    'images/impulse_response_functions.png',
    'images/variance_decomposition.png',
    'images/regime_analysis.png',
    'images/time_series_plots.png',
    'images/scatter_reit_vs_inflation.png'
]

for img in referenced_images:
    img_path = os.path.join('report', img)
    if os.path.exists(img_path):
        print(f"✓ Image exists: {img_path}")
    else:
        print(f"✗ Missing image: {img_path}")

print("\nChecking output files...")
required_outputs = [
    'outputs/processed_data.csv',
    'outputs/regression_results.txt',
    'outputs/granger_causality_results.csv',
    'outputs/var_model_summary.txt'
]

for output in required_outputs:
    if os.path.exists(output):
        print(f"✓ Output exists: {output}")
    else:
        print(f"✗ Missing output: {output}")

print("\nChecking data file...")
if os.path.exists('data/reit_macro_quarterly.csv'):
    df = pd.read_csv('data/reit_macro_quarterly.csv')
    print(f"✓ Data file exists: data/reit_macro_quarterly.csv ({len(df)} rows, {len(df.columns)} columns)")
    print(f"  Columns: {list(df.columns)}")
else:
    print("✗ Data file missing: data/reit_macro_quarterly.csv")

print("\n" + "="*60)
print("Validation complete.")
print("If all checks pass with ✓, the report should be complete and ready.")