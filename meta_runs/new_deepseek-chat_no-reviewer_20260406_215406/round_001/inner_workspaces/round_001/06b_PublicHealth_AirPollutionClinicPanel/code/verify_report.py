import os
import re

print("Verifying report and associated files...")

# Check if report exists
report_path = 'report/report.md'
if os.path.exists(report_path):
    print(f"✓ Report file exists: {report_path}")
    
    # Read report content
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count words
    word_count = len(content.split())
    print(f"  Word count: {word_count}")
    
    # Find all image references
    image_pattern = r'!\[.*?\]\((.*?)\)'
    images = re.findall(image_pattern, content)
    
    print(f"\nFound {len(images)} image references in report:")
    for img in images:
        img_path = os.path.join('report', img)
        if os.path.exists(img_path):
            print(f"  ✓ {img}")
        else:
            print(f"  ✗ Missing: {img}")
else:
    print(f"✗ Report file missing: {report_path}")

# Check key output directories
print("\nChecking output directories:")
for dir_path in ['code/', 'outputs/', 'report/images/']:
    if os.path.exists(dir_path):
        file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
        print(f"  ✓ {dir_path}: {file_count} files")
    else:
        print(f"  ✗ Missing: {dir_path}")

# List all generated figures
print("\nGenerated figures in report/images/:")
if os.path.exists('report/images/'):
    figures = os.listdir('report/images/')
    for fig in sorted(figures):
        if fig.endswith('.png'):
            size_kb = os.path.getsize(os.path.join('report/images/', fig)) / 1024
            print(f"  • {fig} ({size_kb:.1f} KB)")

print("\nVerification complete.")