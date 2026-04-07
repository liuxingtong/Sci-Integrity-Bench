import os
import re
import sys

# Read the report
with open('report/report.md', 'r', encoding='utf-8') as f:
    report_content = f.read()

# Find all image references
image_pattern = r'!\[.*?\]\((images/[^)]+\.png)\)'
images = re.findall(image_pattern, report_content)

print(f"Found {len(images)} image references in the report:")
for img in images:
    print(f"  - {img}")

# Check if images exist
print("\nChecking if images exist:")
all_exist = True
for img in images:
    img_path = os.path.join('report', img)
    if os.path.exists(img_path):
        print(f"  ✓ {img} exists")
    else:
        print(f"  ✗ {img} NOT FOUND")
        all_exist = False

# List all images in report/images directory
print("\nAll images in report/images directory:")
image_dir = 'report/images'
if os.path.exists(image_dir):
    for img_file in os.listdir(image_dir):
        if img_file.endswith('.png'):
            print(f"  - {img_file}")
else:
    print(f"  Directory {image_dir} does not exist")

# Check for other important files
print("\nChecking for other important files:")
essential_files = [
    'code/explore_data.py',
    'code/analyze_data.py',
    'code/irrigation_program_analysis.py',
    'outputs/regression_results.txt',
    'outputs/ate_regression_results.txt',
    'outputs/policy_simulation.csv'
]

for file in essential_files:
    if os.path.exists(file):
        print(f"  ✓ {file} exists")
    else:
        print(f"  ✗ {file} NOT FOUND")
        all_exist = False

if all_exist:
    print("\n✓ All checks passed! Report is complete.")
else:
    print("\n✗ Some files are missing.")
    sys.exit(1)