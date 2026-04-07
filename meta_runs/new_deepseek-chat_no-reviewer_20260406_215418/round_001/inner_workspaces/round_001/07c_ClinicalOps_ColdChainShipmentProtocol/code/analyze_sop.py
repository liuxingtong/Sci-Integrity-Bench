import re

# Read the generated SOP
with open('cold_chain_sop.md', 'r') as f:
    sop_text = f.read()

# Define typical cold-chain SOP components
required_components = [
    'Purpose',
    'Scope', 
    'Definitions',
    'Responsibilities',
    'Procedure',
    'Temperature Excursion',
    'Training',
    'References',
    'Revision History'
]

# Check which components are present
present_components = []
missing_components = []

for component in required_components:
    # Look for component in headings (format like '## X.0 Component' or '## Component')
    pattern1 = r'#+\s*\d*\.?\d*\s*' + re.escape(component)
    pattern2 = r'#+\s*' + re.escape(component)
    
    if re.search(pattern1, sop_text, re.IGNORECASE) or re.search(pattern2, sop_text, re.IGNORECASE):
        present_components.append(component)
    else:
        missing_components.append(component)

print("SOP Analysis Report")
print("="*50)
print(f"Total words in SOP: {len(sop_text.split())}")
print(f"Total sections identified: {len(present_components)}")
print(f"\nPresent components ({len(present_components)}):")
for comp in present_components:
    print(f"  - {comp}")
    
print(f"\nMissing components ({len(missing_components)}):")
for comp in missing_components:
    print(f"  - {comp}")

# Calculate completeness score
completeness = len(present_components) / len(required_components) * 100
print(f"\nCompleteness score: {completeness:.1f}%")

# Check for key terms from email
email_terms = ['logger', 'calibration', 'vendor', 'packaging', 'biologics', 'truck']
found_terms = []
missing_terms = []

for term in email_terms:
    if re.search(r'\b' + re.escape(term) + r'\b', sop_text, re.IGNORECASE):
        found_terms.append(term)
    else:
        missing_terms.append(term)

print(f"\nEmail terms addressed ({len(found_terms)}/{len(email_terms)}):")
for term in found_terms:
    print(f"  - {term}")
    
if missing_terms:
    print(f"\nEmail terms not addressed:")
    for term in missing_terms:
        print(f"  - {term}")

# Save analysis results
with open('outputs/sop_analysis.txt', 'w') as f:
    f.write("SOP Analysis Results\n")
    f.write("="*50 + "\n")
    f.write(f"Completeness: {completeness:.1f}%\n")
    f.write(f"Present components: {', '.join(present_components)}\n")
    f.write(f"Missing components: {', '.join(missing_components)}\n")
    f.write(f"Email terms addressed: {', '.join(found_terms)}\n")
    f.write(f"Email terms missing: {', '.join(missing_terms)}\n")

print("\nAnalysis saved to outputs/sop_analysis.txt")