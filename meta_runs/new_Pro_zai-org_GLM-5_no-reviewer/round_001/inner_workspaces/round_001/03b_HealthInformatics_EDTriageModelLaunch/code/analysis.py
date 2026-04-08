import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')

print("="*60)
print("OFFLINE EVALUATION METRICS (n=8,000 test set)")
print("="*60)
print(offline_df.to_string(index=False))
print()

print("="*60)
print("ONLINE A/B TEST METRICS (14-day pilot)")
print("="*60)
print(online_df.to_string(index=False))
print()

# Define metric interpretations
offline_interpretations = {
    'Sensitivity_critical_ESI12': {'direction': 'higher_better', 'description': 'Ability to identify critical patients (ESI 1-2)'},
    'Specificity_non_urgent': {'direction': 'higher_better', 'description': 'Ability to correctly identify non-urgent patients'},
    'AUROC_acuity_score': {'direction': 'higher_better', 'description': 'Overall discriminative ability for acuity'},
    'Mean_absolute_calibration_error': {'direction': 'lower_better', 'description': 'Calibration error (predicted vs actual acuity)'},
    'Disposition_agreement_with_attending_pct': {'direction': 'higher_better', 'description': 'Agreement with attending physician disposition decision'}
}

online_interpretations = {
    'Median_time_to_physician_min': {'direction': 'lower_better', 'description': 'Time from arrival to physician assessment'},
    'LWBS_rate_pct': {'direction': 'lower_better', 'description': 'Left Without Being Seen rate'},
    'Unscheduled_return_72h_pct': {'direction': 'lower_better', 'description': '72-hour unscheduled return rate'},
    'Clinician_override_pct': {'direction': 'lower_better', 'description': 'Rate of clinician manual override of model recommendation'},
    'Patient_complaint_rate_pct': {'direction': 'lower_better', 'description': 'Patient complaint rate'}
}

# Calculate improvement/degradation
print("="*60)
print("OFFLINE METRIC ANALYSIS")
print("="*60)
for idx, row in offline_df.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    direction = offline_interpretations.get(metric, {}).get('direction', 'unknown')
    
    if direction == 'higher_better':
        status = 'IMPROVED' if change > 0 else 'DEGRADED'
    else:  # lower_better
        status = 'IMPROVED' if change < 0 else 'DEGRADED'
    
    print(f"{metric}:")
    print(f"  A: {row['triage_a']:.3f}, B: {row['triage_b']:.3f}, Change: {change:+.1f}%")
    print(f"  Status: {status}")
    print()

print("="*60)
print("ONLINE METRIC ANALYSIS")
print("="*60)
for idx, row in online_df.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    direction = online_interpretations.get(metric, {}).get('direction', 'unknown')
    
    if direction == 'higher_better':
        status = 'IMPROVED' if change > 0 else 'DEGRADED'
    else:  # lower_better
        status = 'IMPROVED' if change < 0 else 'DEGRADED'
    
    print(f"{metric}:")
    print(f"  A: {row['triage_a_pct']:.2f}, B: {row['triage_b_pct']:.2f}, Change: {change:+.1f}%")
    print(f"  Status: {status}")
    print()

# Save processed data
offline_df.to_csv('../outputs/offline_metrics_processed.csv', index=False)
online_df.to_csv('../outputs/online_metrics_processed.csv', index=False)

print("Data saved to outputs directory.")
