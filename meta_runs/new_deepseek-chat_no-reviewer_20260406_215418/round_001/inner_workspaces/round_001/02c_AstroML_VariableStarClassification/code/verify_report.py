import os
import matplotlib.pyplot as plt
import numpy as np

# Check that all referenced images exist
report_dir = '../report'
images_dir = os.path.join(report_dir, 'images')

# List of images referenced in the report
referenced_images = [
    'symbol_frequencies.png',
    'position_patterns.png',
    'model_comparison.png',
    'confusion_matrix.png',
    'feature_importance.png',
    'final_confusion_matrix.png',
    'final_feature_importance.png',
    'final_model_comparison.png'
]

print("Checking image files...")
for img in referenced_images:
    img_path = os.path.join(images_dir, img)
    if os.path.exists(img_path):
        print(f"✓ {img} exists")
    else:
        print(f"✗ {img} is missing")

# Check report file
report_path = os.path.join(report_dir, 'report.md')
if os.path.exists(report_path):
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"\nReport file size: {len(content)} characters")
    line_count = content.count('\n')
    print(f"Report has {line_count} lines")
    
    # Check for key sections (with numbering)
    sections = ['Abstract', '1. Introduction', '2. Data Description', '3. Methodology', '4. Results', '5. Discussion', '6. Conclusion']
    for section in sections:
        if section in content:
            print(f"✓ {section} section found")
        else:
            print(f"✗ {section} section missing")
else:
    print("Report file not found!")
