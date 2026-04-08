#!/usr/bin/env python3
"""
Validation script for the variant calling pipeline.
"""

import os
import json
import pandas as pd
from pathlib import Path

def validate_outputs():
    """Validate that all expected output files exist and contain valid data."""
    print("Validating pipeline outputs...")
    
    required_files = [
        'outputs/variant_calling_metrics.csv',
        'outputs/pipeline_summary.json',
        'outputs/pipeline_execution_report.txt',
        'report/images/variant_qc_metrics.png',
        'report/images/coverage_distribution.png',
        'report/images/variant_type_distribution.png',
        'report/report.md'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (MISSING)")
            all_exist = False
    
    # Check data integrity
    if all_exist:
        print("\nChecking data integrity...")
        
        # Check JSON file
        try:
            with open('outputs/pipeline_summary.json', 'r') as f:
                summary = json.load(f)
            print(f"  ✓ pipeline_summary.json valid (version: {summary.get('pipeline_version', 'N/A')})")
        except Exception as e:
            print(f"  ✗ pipeline_summary.json invalid: {e}")
            all_exist = False
        
        # Check CSV file
        try:
            df = pd.read_csv('outputs/variant_calling_metrics.csv')
            print(f"  ✓ variant_calling_metrics.csv valid ({len(df)} rows)")
        except Exception as e:
            print(f"  ✗ variant_calling_metrics.csv invalid: {e}")
            all_exist = False
        
        # Check report file size
        report_size = os.path.getsize('report/report.md')
        if report_size > 1000:  # At least 1KB
            print(f"  ✓ report.md sufficient size ({report_size} bytes)")
        else:
            print(f"  ✗ report.md too small ({report_size} bytes)")
            all_exist = False
    
    return all_exist

def main():
    """Main validation function."""
    print("="*60)
    print("VARIANT CALLING PIPELINE VALIDATION")
    print("="*60)
    
    if validate_outputs():
        print("\n" + "="*60)
        print("VALIDATION PASSED")
        print("All outputs generated correctly.")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("VALIDATION FAILED")
        print("Some outputs are missing or invalid.")
        print("="*60)
        return 1

if __name__ == "__main__":
    exit(main())
