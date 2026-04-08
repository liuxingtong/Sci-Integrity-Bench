import os
import sys

# Check that all referenced images exist
images_required = [
    'scatter_raw.png',
    'scatter_loglog.png',
    'power_law_fit.png',
    'power_law_original_scale.png',
    'model_comparison.png',
    'residual_diagnostics.png'
]

print("Checking report images...")
all_exist = True
for img in images_required:
    path = os.path.join('report', 'images', img)
    if os.path.exists(path):
        print(f"  ✓ {img}")
    else:
        print(f"  ✗ {img} MISSING")
        all_exist = False

# Check report exists
report_path = 'report/report.md'
if os.path.exists(report_path):
    print(f"\n✓ Report exists: {report_path}")
    with open(report_path, 'r') as f:
        content = f.read()
        print(f"  Report length: {len(content)} characters")
        print(f"  Number of lines: {len(content.split('\n'))}")
else:
    print(f"\n✗ Report missing: {report_path}")
    all_exist = False

# Check outputs
output_files = [
    'summary_statistics.csv',
    'power_law_regression.csv',
    'model_comparison.csv',
    'conservation_implications.csv'
]

print("\nChecking output files...")
for file in output_files:
    path = os.path.join('outputs', file)
    if os.path.exists(path):
        print(f"  ✓ {file}")
    else:
        print(f"  ✗ {file} MISSING")
        all_exist = False

if all_exist:
    print("\n✅ All deliverables verified successfully!")
    sys.exit(0)
else:
    print("\n❌ Some deliverables are missing.")
    sys.exit(1)
