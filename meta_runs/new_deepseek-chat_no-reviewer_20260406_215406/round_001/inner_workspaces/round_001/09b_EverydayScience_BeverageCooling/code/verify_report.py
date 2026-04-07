import os
import re

# Read the report
with open('../report/report.md', 'r') as f:
    content = f.read()

# Find all image references
image_pattern = r'!\[.*?\]\((.*?)\)'
images = re.findall(image_pattern, content)

print(f"Found {len(images)} image references in report:")
for img in images:
    print(f"  {img}")
    
# Check if images exist
print("\nChecking image files:")
all_exist = True
for img in images:
    img_path = os.path.join('../report', img)
    if os.path.exists(img_path):
        print(f"  ✓ {img} exists")
    else:
        print(f"  ✗ {img} NOT FOUND")
        all_exist = False

# List all images in report/images
print("\nAll images in report/images:")
image_dir = '../report/images'
if os.path.exists(image_dir):
    for fname in os.listdir(image_dir):
        if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            print(f"  {fname}")
else:
    print(f"Directory {image_dir} does not exist")

print(f"\nAll images referenced in report exist: {all_exist}")

# Check report structure
print("\nReport sections:")
sections = ['Abstract', 'Introduction', 'Methodology', 'Results', 'Discussion', 'Conclusion', 'References']
for section in sections:
    if f'## {section}' in content or f'# {section}' in content:
        print(f"  ✓ {section}")
    else:
        print(f"  ✗ {section} not found")
