#!/usr/bin/env python3
"""
Analyze email thread draft to extract requirements for cold-chain SOP.
"""

import re
from collections import defaultdict

def read_email_file(filepath):
    """Read and parse email content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def extract_requirements(email_content):
    """Extract key requirements from email."""
    requirements = {
        'purpose': [],
        'equipment': [],
        'procedures': [],
        'responsibilities': [],
        'documentation': []
    }
    
    # Analyze content for key phrases
    lines = email_content.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        
        # Extract purpose
        if 'need' in line_lower and 'sop' in line_lower:
            requirements['purpose'].append(line.strip())
        
        # Extract equipment
        if 'truck' in line_lower or 'logger' in line_lower or 'calibration' in line_lower:
            requirements['equipment'].append(line.strip())
        
        # Extract procedures
        if 'packaging' in line_lower or 'follow' in line_lower:
            requirements['procedures'].append(line.strip())
        
        # Extract responsibilities
        if 'vendor' in line_lower or 'team' in line_lower:
            requirements['responsibilities'].append(line.strip())
    
    return requirements

def generate_sop_outline(requirements):
    """Generate SOP outline based on extracted requirements."""
    outline = {
        'title': 'Cold-Chain Shipment Standard Operating Procedure for Biologics',
        'sections': [
            '1.0 PURPOSE AND SCOPE',
            '2.0 RESPONSIBILITIES',
            '3.0 DEFINITIONS',
            '4.0 EQUIPMENT AND MATERIALS',
            '5.0 PROCEDURES',
            '5.1 Pre-Shipment Preparation',
            '5.2 Packaging Requirements',
            '5.3 Temperature Monitoring',
            '5.4 Transportation',
            '5.5 Receiving and Verification',
            '6.0 DOCUMENTATION AND RECORDS',
            '7.0 TRAINING',
            '8.0 REFERENCES',
            '9.0 REVISION HISTORY'
        ],
        'key_points': {}
    }
    
    # Map requirements to sections
    outline['key_points']['1.0 PURPOSE AND SCOPE'] = requirements['purpose']
    outline['key_points']['4.0 EQUIPMENT AND MATERIALS'] = requirements['equipment']
    outline['key_points']['5.0 PROCEDURES'] = requirements['procedures']
    outline['key_points']['2.0 RESPONSIBILITIES'] = requirements['responsibilities']
    
    return outline

def main():
    """Main analysis function."""
    email_file = '../data/email_thread_draft.txt'
    
    print("Analyzing email thread draft...")
    email_content = read_email_file(email_file)
    print(f"Email content:\n{email_content}\n")
    
    requirements = extract_requirements(email_content)
    
    print("Extracted Requirements:")
    for category, items in requirements.items():
        print(f"\n{category.upper()}:")
        for item in items:
            print(f"  - {item}")
    
    outline = generate_sop_outline(requirements)
    
    print("\n" + "="*60)
    print("GENERATED SOP OUTLINE:")
    print("="*60)
    print(f"\nTitle: {outline['title']}")
    print("\nSections:")
    for section in outline['sections']:
        print(f"  {section}")
    
    print("\nKey Points by Section:")
    for section, points in outline['key_points'].items():
        if points:
            print(f"\n{section}:")
            for point in points:
                print(f"  - {point}")
    
    # Save analysis results
    with open('../outputs/requirements_analysis.txt', 'w') as f:
        f.write("EMAIL CONTENT ANALYSIS\n")
        f.write("="*60 + "\n\n")
        f.write(f"Email content:\n{email_content}\n\n")
        f.write("EXTRACTED REQUIREMENTS:\n")
        f.write("="*60 + "\n")
        for category, items in requirements.items():
            f.write(f"\n{category.upper()}:\n")
            for item in items:
                f.write(f"  - {item}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("GENERATED SOP OUTLINE:\n")
        f.write("="*60 + "\n\n")
        f.write(f"Title: {outline['title']}\n\n")
        f.write("Sections:\n")
        for section in outline['sections']:
            f.write(f"  {section}\n")
        
        f.write("\nKey Points by Section:\n")
        for section, points in outline['key_points'].items():
            if points:
                f.write(f"\n{section}:\n")
                for point in points:
                    f.write(f"  - {point}\n")
    
    print("\nAnalysis saved to outputs/requirements_analysis.txt")
    
    return requirements, outline

if __name__ == "__main__":
    main()