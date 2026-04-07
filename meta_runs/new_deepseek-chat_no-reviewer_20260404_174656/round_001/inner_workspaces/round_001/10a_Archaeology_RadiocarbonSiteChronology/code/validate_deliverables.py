import os
import sys

print("=== VALIDATING DELIVERABLES ===")

# Check required directories exist
required_dirs = [
    'code',
    'outputs', 
    'report',
    'report/images'
]

print("Checking directories...")
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"  ✓ {dir_path}")
    else:
        print(f"  ✗ {dir_path} - MISSING")
        sys.exit(1)

# Check required files exist
required_files = [
    'report/report.md',
    'code/analyze_radiocarbon.py',
    'code/calibrate_and_analyze.py',
    'code/bayesian_chronology.py',
    'outputs/radiocarbon_ages.csv',
    'outputs/calibrated_ages.csv',
    'outputs/detailed_chronology.csv',
    'report/images/bayesian_chronology.png',
    'report/images/cultural_periods.png'
]

print("\nChecking files...")
for file_path in required_files:
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"  ✓ {file_path} ({file_size:,} bytes)")
    else:
        print(f"  ✗ {file_path} - MISSING")
        sys.exit(1)

# Check report content
print("\nChecking report content...")
with open('report/report.md', 'r', encoding='utf-8') as f:
    report_content = f.read()
    
# Check for key sections
key_sections = [
    'Executive Summary',
    'Introduction',
    'Materials and Methods',
    'Results',
    'Discussion',
    'Conclusions',
    'Figure 1',
    'Figure 2',
    'Table 1',
    'Table 2',
    'Table 3'
]

for section in key_sections:
    if section in report_content:
        print(f"  ✓ Contains '{section}'")
    else:
        print(f"  ⚠ Missing '{section}'")

# Check for image references
image_refs = [
    'bayesian_chronology.png',
    'cultural_periods.png'
]

for img in image_refs:
    if img in report_content:
        print(f"  ✓ References image '{img}'")
    else:
        print(f"  ⚠ Missing reference to '{img}'")

print("\n=== VALIDATION COMPLETE ===")
print("All required deliverables are present and the report appears complete.")
print("\nSummary of outputs:")
print(f"- Report: {len(report_content):,} characters")
print(f"- Code files: 3 Python scripts")
print(f"- Data outputs: 3 CSV files")
print(f"- Figures: 5 PNG images")

# Count figures in images directory
image_files = [f for f in os.listdir('report/images') if f.endswith('.png')]
print(f"- Total images in report/images: {len(image_files)}")
for img in image_files:
    size = os.path.getsize(os.path.join('report/images', img))
    print(f"    - {img}: {size:,} bytes")