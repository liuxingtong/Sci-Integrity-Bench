#!/usr/bin/env python3
"""
Parse lab scratch notes and extract synthesis parameters for nanoparticle SOP.
"""

import re
from datetime import datetime

def parse_lab_notes(filepath):
    """Parse raw lab notes and extract structured information."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    
    # Extract key information
    info = {
        'title': '',
        'temperature': None,
        'precursor': None,
        'surfactant': None,
        'duration': None,
        'color_change': None,
        'notes': []
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Extract title/product name
        if 'synthesis' in line.lower():
            match = re.search(r'([A-Za-z]+)\s+synthesis', line, re.IGNORECASE)
            if match:
                info['title'] = match.group(1)
        
        # Extract temperature
        temp_match = re.search(r'(\d+)\s*C', line, re.IGNORECASE)
        if temp_match:
            info['temperature'] = int(temp_match.group(1))
        
        # Extract precursor info
        if 'precursor' in line.lower():
            info['precursor'] = line
        
        # Extract surfactant info
        if 'surfactant' in line.lower():
            info['surfactant'] = line
        
        # Extract duration
        if 'overnight' in line.lower():
            info['duration'] = 'overnight (~12-16 hours)'
        
        # Extract color change
        if 'color' in line.lower() or 'turn' in line.lower():
            color_match = re.search(r'from\s+([\w-]+)\s+to\s+([\w-]+)', line, re.IGNORECASE)
            if color_match:
                info['color_change'] = f"{color_match.group(1)} to {color_match.group(2)}"
        
        # Capture any notes or uncertainties
        if '?' in line or 'check' in line.lower() or 'not fully' in line.lower():
            info['notes'].append(line)
    
    return info

if __name__ == '__main__':
    info = parse_lab_notes('data/lab_scratch.txt')
    print("Parsed Lab Notes:")
    print("=" * 50)
    for key, value in info.items():
        print(f"{key}: {value}")
