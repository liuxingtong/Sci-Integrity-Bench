import os
import sys

print("Verifying deliverables for Island Biogeography Research Task\n")
print("="*60)

# Check required directories
dirs_to_check = ['code', 'outputs', 'report', 'report/images']
print("\n1. Directory structure:")
for dir_path in dirs_to_check:
    if os.path.exists(dir_path):
        print(f"   ✓ {dir_path}")
    else:
        print(f"   ✗ {dir_path} - MISSING")
        sys.exit(1)

# Check required files
required_files = [
    'report/report.md',
    'report/images/species_area_analysis.png',
    'report/images/conservation_analysis.png',
    'code/explore_data.py',
    'code/analyze_species_area.py',
    'code/conservation_analysis.py',
    'outputs/model_summary.txt',
    'outputs/model_predictions.csv',
    'outputs/habitat_loss_scenarios.csv',
    'outputs/conservation_recommendations.txt'
]

print("\n2. Required files:")
all_files_present = True
for file_path in required_files:
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"   ✓ {file_path} ({file_size} bytes)")
    else:
        print(f"   ✗ {file_path} - MISSING")
        all_files_present = False

# Check report content
print("\n3. Report content check:")
if os.path.exists('report/report.md'):
    with open('report/report.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Abstract section', '## Abstract' in content),
        ('Methods section', '## 2. Methods' in content),
        ('Results section', '## 3. Results' in content),
        ('Discussion section', '## 4. Discussion' in content),
        ('Conclusions section', '## 5. Conclusions' in content),
        ('Figure references', '![' in content),
        ('Power law equation', 'S = ' in content and 'A^' in content),
        ('z-value reported', 'z = ' in content or 'z-value' in content)
    ]
    
    for check_name, check_result in checks:
        if check_result:
            print(f"   ✓ {check_name}")
        else:
            print(f"   ✗ {check_name}")
            all_files_present = False

print("\n" + "="*60)
if all_files_present:
    print("SUCCESS: All deliverables are complete and verified!")
    
    # Count lines of code
    code_files = ['code/explore_data.py', 'code/analyze_species_area.py', 'code/conservation_analysis.py']
    total_lines = 0
    for code_file in code_files:
        if os.path.exists(code_file):
            with open(code_file, 'r') as f:
                total_lines += len(f.readlines())
    
    print(f"\nSummary:")
    print(f"- Report: {len(content.split())} words")
    print(f"- Code: {total_lines} lines across {len(code_files)} files")
    print(f"- Outputs: {len([f for f in os.listdir('outputs') if os.path.isfile(os.path.join('outputs', f))])} files")
    print(f"- Figures: {len([f for f in os.listdir('report/images') if f.endswith('.png')])} PNG images")
    
else:
    print("FAILURE: Some deliverables are missing or incomplete.")
    sys.exit(1)