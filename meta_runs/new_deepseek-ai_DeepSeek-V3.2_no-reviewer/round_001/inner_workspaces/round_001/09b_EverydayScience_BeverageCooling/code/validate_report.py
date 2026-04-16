import os
import re

# Read the report
with open('report/report.md', 'r') as f:
    report = f.read()

# Find all image references
image_pattern = r'!\[.*?\]\((.*?)\)'
images = re.findall(image_pattern, report)

print("Images referenced in report:")
for img in images:
    print(f"  {img}")
    # Check if file exists
    if os.path.exists(os.path.join('report', img)):
        print(f"    ✓ Found")
    else:
        print(f"    ✗ Missing!")

# Check report structure
print("\nReport structure check:")
sections = ['Executive Summary', 'Introduction', 'Data Overview', 'Methodology', 
            'Results', 'Discussion', 'Conclusion', 'References', 'Appendix']

for section in sections:
    if f'## {section}' in report or (section == 'Executive Summary' and '# ' in report):
        print(f"  ✓ {section}")
    else:
        print(f"  ✗ {section} (missing or misformatted)")

print("\nReport validation complete.")