import os
import glob
import pandas as pd

print("=== FINAL VALIDATION OF RESEARCH OUTPUTS ===")
print()

# Check required directories exist
required_dirs = ['code', 'outputs', 'report', 'report/images']
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"✓ Directory exists: {dir_path}")
    else:
        print(f"✗ Missing directory: {dir_path}")

print()

# Check report file exists
report_path = 'report/report.md'
if os.path.exists(report_path):
    print(f"✓ Main report file exists: {report_path}")
    # Check report size
    report_size = os.path.getsize(report_path)
    print(f"  Report size: {report_size:,} bytes")
    
    # Read and check for image references
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Count images referenced
    import re
    image_refs = re.findall(r'!\[.*?\]\(images/(.*?)\)', content)
    print(f"  Images referenced in report: {len(image_refs)}")
    for img in image_refs:
        img_path = os.path.join('report/images', img)
        if os.path.exists(img_path):
            print(f"    ✓ {img}")
        else:
            print(f"    ✗ Missing: {img}")
else:
    print(f"✗ Missing report file: {report_path}")

print()

# Check output files
output_files = glob.glob('outputs/*')
print(f"Output files generated: {len(output_files)}")
for file in output_files:
    file_size = os.path.getsize(file)
    print(f"  {os.path.basename(file)}: {file_size:,} bytes")

print()

# Check image files
image_files = glob.glob('report/images/*')
print(f"Image files generated: {len(image_files)}")
for img in image_files:
    img_name = os.path.basename(img)
    img_size = os.path.getsize(img)
    print(f"  {img_name}: {img_size:,} bytes")

print()

# Check code files
code_files = glob.glob('code/*.py')
print(f"Code files generated: {len(code_files)}")
for code in code_files:
    code_name = os.path.basename(code)
    code_size = os.path.getsize(code)
    print(f"  {code_name}: {code_size:,} bytes")

print()
print("=== VALIDATION COMPLETE ===")