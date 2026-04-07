import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Create directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("ED Triage Model Evaluation Analysis")
print("=" * 50)

# Load data
offline = pd.read_csv('data/offline_evaluation_metrics.csv')
online = pd.read_csv('data/online_ab_test_metrics.csv')

print("\n1. DATA OVERVIEW")
print("Offline metrics (n=8,000 chart review):")
print(offline)
print("\nOnline metrics (14-day pilot):")
print(online)

# 1. Basic analysis
print("\n2. KEY FINDINGS")

# Offline analysis
print("\nOFFLINE EVALUATION:")
for idx, row in offline.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    
    if 'Sensitivity' in metric:
        print(f"  • Sensitivity (critical cases): {change:+.1f}% improvement")
        print(f"    - Triage-B better at identifying life-threatening conditions")
    elif 'Specificity' in metric:
        print(f"  • Specificity (non-urgent): {change:+.1f}% change")
        print(f"    - Triage-B has more false alarms for non-urgent cases")
    elif 'AUROC' in metric:
        print(f"  • AUROC (overall discrimination): {change:+.1f}% improvement")
        print(f"    - Triage-B better at ranking patient acuity")
    elif 'calibration' in metric.lower():
        print(f"  • Calibration error: {change:+.1f}% change")
        print(f"    - Triage-B's risk scores are less reliable")
    elif 'Disposition' in metric:
        print(f"  • Agreement with attending: {change:+.1f}% change")
        print(f"    - Triage-B less aligned with physician judgment")

# Online analysis
print("\nONLINE PILOT RESULTS:")
for idx, row in online.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    
    if 'time_to_physician' in metric:
        print(f"  • Wait time: {change:+.1f}% change")
        print(f"    - Triage-B reduces wait time by {abs(change):.1f}%")
    elif 'LWBS' in metric:
        print(f"  • Leave Without Being Seen: {change:+.1f}% change")
        print(f"    - Triage-B increases LWBS by {change:.1f}% (CONCERNING)")
    elif 'return' in metric.lower():
        print(f"  • 72-hour returns: {change:+.1f}% change")
        print(f"    - Triage-B increases returns by {change:.1f}% (CONCERNING)")
    elif 'override' in metric.lower():
        print(f"  • Clinician overrides: {change:+.1f}% change")
        print(f"    - Clinicians override Triage-B {change:.1f}% more often")
    elif 'complaint' in metric.lower():
        print(f"  • Patient complaints: {change:+.1f}% change")
        print(f"    - Complaints increase by {change:.1f}% (SERIOUS CONCERN)")

# 2. Create visualizations
print("\n3. CREATING VISUALIZATIONS...")

# Figure 1: Offline metrics comparison
plt.figure(figsize=(12, 6))

x = np.arange(len(offline))
width = 0.35

plt.bar(x - width/2, offline['triage_a'], width, label='Triage-A', color='blue', alpha=0.7)
plt.bar(x + width/2, offline['triage_b'], width, label='Triage-B', color='red', alpha=0.7)

plt.xlabel('Metrics')
plt.ylabel('Score')
plt.title('Offline Evaluation: TriageAssist-A vs TriageAssist-B (n=8,000)')
plt.xticks(x, [m[:20] + '...' if len(m) > 20 else m for m in offline['metric']], rotation=45, ha='right')
plt.legend()
plt.grid(True, alpha=0.3)

# Add change labels
for i, change in enumerate(offline['relative_change_pct']):
    plt.text(i, max(offline.iloc[i]['triage_a'], offline.iloc[i]['triage_b']) + 0.02,
             f'{change:+.1f}%', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/offline_comparison.png', dpi=300)
print("  Saved: report/images/offline_comparison.png")

# Figure 2: Online metrics comparison
plt.figure(figsize=(12, 6))

x = np.arange(len(online))

plt.bar(x - width/2, online['triage_a_pct'], width, label='Triage-A', color='blue', alpha=0.7)
plt.bar(x + width/2, online['triage_b_pct'], width, label='Triage-B', color='red', alpha=0.7)

plt.xlabel('Metrics')
plt.ylabel('Value (%)')
plt.title('Online Pilot: TriageAssist-A vs TriageAssist-B (14-day deployment)')
plt.xticks(x, online['metric'], rotation=45, ha='right')
plt.legend()
plt.grid(True, alpha=0.3)

# Add change labels
for i, change in enumerate(online['relative_change_pct']):
    plt.text(i, max(online.iloc[i]['triage_a_pct'], online.iloc[i]['triage_b_pct']) * 1.05,
             f'{change:+.1f}%', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/online_comparison.png', dpi=300)
print("  Saved: report/images/online_comparison.png")

# Figure 3: Improvement summary
plt.figure(figsize=(10, 8))

# Calculate normalized improvements
offline_imp = []
for idx, row in offline.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    
    if 'Sensitivity' in metric or 'AUROC' in metric:
        offline_imp.append(change)  # Positive is good
    elif 'Specificity' in metric or 'Disposition' in metric:
        offline_imp.append(-change)  # Negative change is bad
    elif 'calibration' in metric.lower():
        offline_imp.append(-change)  # Negative change is good
    else:
        offline_imp.append(change)

online_imp = [-change for change in online['relative_change_pct']]  # Negative is good for all

# Combine for visualization
all_metrics = list(offline['metric']) + list(online['metric'])
all_improvements = offline_imp + online_imp
colors = ['green' if imp > 0 else 'red' for imp in all_improvements]

plt.barh(all_metrics, all_improvements, color=colors, alpha=0.7)
plt.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
plt.xlabel('Improvement Score (Positive = Better)')
plt.title('Overall Improvement: Triage-B vs Triage-A')
plt.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, v in enumerate(all_improvements):
    plt.text(v + (0.1 if v >= 0 else -0.1), i, f'{v:+.1f}', 
             va='center', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/improvement_summary.png', dpi=300)
print("  Saved: report/images/improvement_summary.png")

# Figure 4: Risk-Benefit analysis
plt.figure(figsize=(10, 6))

benefits = [
    offline[offline['metric'] == 'Sensitivity_critical_ESI12']['relative_change_pct'].values[0],
    offline[offline['metric'] == 'AUROC_acuity_score']['relative_change_pct'].values[0],
    online[online['metric'] == 'Median_time_to_physician_min']['relative_change_pct'].values[0]
]

risks = [
    offline[offline['metric'] == 'Specificity_non_urgent']['relative_change_pct'].values[0],
    offline[offline['metric'] == 'Mean_absolute_calibration_error']['relative_change_pct'].values[0],
    offline[offline['metric'] == 'Disposition_agreement_with_attending_pct']['relative_change_pct'].values[0],
    online[online['metric'] == 'LWBS_rate_pct']['relative_change_pct'].values[0],
    online[online['metric'] == 'Unscheduled_return_72h_pct']['relative_change_pct'].values[0],
    online[online['metric'] == 'Clinician_override_pct']['relative_change_pct'].values[0],
    online[online['metric'] == 'Patient_complaint_rate_pct']['relative_change_pct'].values[0]
]

benefit_labels = ['Sensitivity', 'AUROC', 'Wait Time']
risk_labels = ['Specificity', 'Calibration', 'MD Agreement', 'LWBS', '72h Returns', 'Overrides', 'Complaints']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Benefits
colors_ben = ['green' if b > 0 else 'red' for b in benefits]
ax1.barh(benefit_labels, benefits, color=colors_ben, alpha=0.7)
ax1.set_xlabel('Change (%)')
ax1.set_title('Benefits of Triage-B')
ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
for i, v in enumerate(benefits):
    ax1.text(v + (0.1 if v >= 0 else -0.1), i, f'{v:+.1f}%', va='center')

# Risks
colors_risk = ['red' if r > 0 else 'green' for r in risks]
ax2.barh(risk_labels, risks, color=colors_risk, alpha=0.7)
ax2.set_xlabel('Change (%)')
ax2.set_title('Risks/Concerns with Triage-B')
ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
for i, v in enumerate(risks):
    ax2.text(v + (0.1 if v >= 0 else -0.1), i, f'{v:+.1f}%', va='center')

plt.tight_layout()
plt.savefig('report/images/risk_benefit.png', dpi=300)
print("  Saved: report/images/risk_benefit.png")

# 3. Calculate overall recommendation score
print("\n4. OVERALL ASSESSMENT")

# Weighted scoring
# Offline: Sensitivity (40%), AUROC (20%), Specificity (15%), Calibration (15%), Agreement (10%)
offline_score_a = (0.4 * offline.iloc[0]['triage_a'] +  # Sensitivity
                   0.2 * offline.iloc[2]['triage_a'] +  # AUROC
                   0.15 * offline.iloc[1]['triage_a'] +  # Specificity
                   0.15 * (1 - offline.iloc[3]['triage_a']) +  # Calibration (inverted)
                   0.1 * offline.iloc[4]['triage_a'])  # Agreement

offline_score_b = (0.4 * offline.iloc[0]['triage_b'] +  # Sensitivity
                   0.2 * offline.iloc[2]['triage_b'] +  # AUROC
                   0.15 * offline.iloc[1]['triage_b'] +  # Specificity
                   0.15 * (1 - offline.iloc[3]['triage_b']) +  # Calibration (inverted)
                   0.1 * offline.iloc[4]['triage_b'])  # Agreement

print(f"Offline weighted score: Triage-A = {offline_score_a:.3f}, Triage-B = {offline_score_b:.3f}")
print(f"Offline improvement: {(offline_score_b - offline_score_a)/offline_score_a*100:+.1f}%")

# Online: All metrics equally weighted, lower is better
online_max = max(online['triage_a_pct'].max(), online['triage_b_pct'].max())
online_score_a = sum([1 - (v/online_max) for v in online['triage_a_pct']]) / len(online)
online_score_b = sum([1 - (v/online_max) for v in online['triage_b_pct']]) / len(online)

print(f"Online weighted score: Triage-A = {online_score_a:.3f}, Triage-B = {online_score_b:.3f}")
print(f"Online change: {(online_score_b - online_score_a)/online_score_a*100:+.1f}%")

# Overall: 60% offline, 40% online (clinical safety weighted higher)
overall_a = 0.6 * offline_score_a + 0.4 * online_score_a
overall_b = 0.6 * offline_score_b + 0.4 * online_score_b

print(f"\nOverall score: Triage-A = {overall_a:.3f}, Triage-B = {overall_b:.3f}")
print(f"Overall change: {(overall_b - overall_a)/overall_a*100:+.1f}%")

# Save scores
df_scores = pd.DataFrame({
    'Model': ['Triage-A', 'Triage-B'],
    'Offline_Score': [offline_score_a, offline_score_b],
    'Online_Score': [online_score_a, online_score_b],
    'Overall_Score': [overall_a, overall_b]
})
df_scores.to_csv('outputs/model_scores.csv', index=False)
print("\nSaved scores to: outputs/model_scores.csv")

print("\n5. RECOMMENDATION")
print("=" * 50)

if overall_b > overall_a:
    print("RECOMMENDATION: CONSIDER Triage-B with CAUTION")
    print("  • Triage-B shows better overall score but has serious concerns")
    print("  • Benefits: Better sensitivity, AUROC, and reduced wait times")
    print("  • Risks: Increased LWBS, returns, overrides, and complaints")
    print("  • Action: Further refinement needed before full deployment")
else:
    print("RECOMMENDATION: DO NOT DEPLOY Triage-B")
    print("  • Triage-B performs worse overall despite some improvements")
    print("  • Critical safety metrics show concerning trends")
    print("  • Patient experience and clinical trust are compromised")

print("\nAnalysis complete. Check report/images/ for visualizations.")