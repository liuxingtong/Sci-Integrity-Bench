import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import os

# Load the data
df = pd.read_csv("../data/pick_place_metrics.csv")

print("Simulation-to-Real-World Correlation Analysis\n")
print("=" * 60)

# Create pivot tables
pivot_sim = df.pivot(index='metric', columns='arm', values='simulation')
pivot_real = df.pivot(index='metric', columns='arm', values='real_world')

# Calculate differences
diff_sim = pivot_sim['pi_new'] - pivot_sim['pi_base']
diff_real = pivot_real['pi_new'] - pivot_real['pi_base']

# Calculate percentage changes
pct_sim = (diff_sim / pivot_sim['pi_base']) * 100
pct_real = (diff_real / pivot_real['pi_base']) * 100

# 1. Correlation analysis
print("1. Correlation between Simulation and Real-World Performance Changes\n")

# Calculate correlation coefficients
pearson_corr, pearson_p = stats.pearsonr(pct_sim, pct_real)
spearman_corr, spearman_p = stats.spearmanr(pct_sim, pct_real)

print(f"Pearson correlation (linear): r = {pearson_corr:.3f}, p = {pearson_p:.4f}")
print(f"Spearman correlation (monotonic): ρ = {spearman_corr:.3f}, p = {spearman_p:.4f}")

if pearson_p < 0.05:
    print("  → Significant linear correlation (p < 0.05)")
else:
    print("  → No significant linear correlation")

if spearman_p < 0.05:
    print("  → Significant monotonic correlation (p < 0.05)")
else:
    print("  → No significant monotonic correlation")

print("\n" + "=" * 60)
print("\n2. Simulation Fidelity Analysis\n")

# Calculate absolute differences between simulation and real-world
abs_diff_sim_real_base = np.abs(pivot_sim['pi_base'] - pivot_real['pi_base'])
abs_diff_sim_real_new = np.abs(pivot_sim['pi_new'] - pivot_real['pi_new'])

# Calculate relative errors
rel_error_base = (abs_diff_sim_real_base / pivot_real['pi_base']) * 100
rel_error_new = (abs_diff_sim_real_new / pivot_real['pi_new']) * 100

print("Absolute differences between simulation and real-world:")
print(f"  pi_base: Mean = {abs_diff_sim_real_base.mean():.4f}, Std = {abs_diff_sim_real_base.std():.4f}")
print(f"  pi_new:  Mean = {abs_diff_sim_real_new.mean():.4f}, Std = {abs_diff_sim_real_new.std():.4f}")

print("\nRelative errors (% difference from real-world):")
print(f"  pi_base: Mean = {rel_error_base.mean():.1f}%, Std = {rel_error_base.std():.1f}%")
print(f"  pi_new:  Mean = {rel_error_new.mean():.1f}%, Std = {rel_error_new.std():.1f}%")

# Test if simulation fidelity differs between policies
t_stat, t_p = stats.ttest_rel(abs_diff_sim_real_base, abs_diff_sim_real_new)
print(f"\nPaired t-test for simulation fidelity difference:")
print(f"  t = {t_stat:.3f}, p = {t_p:.4f}")
if t_p < 0.05:
    print(f"  → Significant difference in simulation fidelity between policies")
else:
    print(f"  → No significant difference in simulation fidelity")

print("\n" + "=" * 60)
print("\n3. Performance Gap Analysis (Simulation vs Real-World)\n")

# Calculate performance gaps
performance_gap_base = pivot_sim['pi_base'] - pivot_real['pi_base']
performance_gap_new = pivot_sim['pi_new'] - pivot_real['pi_new']

# For metrics where higher is better, positive gap means simulation overestimates
# For metrics where lower is better, we need to adjust interpretation
positive_metrics = ['success_rate', 'human_rating_1_5']
negative_metrics = ['cycle_time_s', 'collision_count', 'energy_kwh', 
                    'line_stop_events', 'safety_intervention_rate', 'edge_case_fail_rate']

print("Performance gaps (Simulation - Real-World):")
print("Positive values indicate simulation overestimates performance")
print("Negative values indicate simulation underestimates performance\n")

for metric in pivot_sim.index:
    gap_base = performance_gap_base[metric]
    gap_new = performance_gap_new[metric]
    
    if metric in positive_metrics:
        interpretation_base = "overestimates" if gap_base > 0 else "underestimates"
        interpretation_new = "overestimates" if gap_new > 0 else "underestimates"
    else:
        # For negative metrics, flip interpretation
        interpretation_base = "underestimates" if gap_base > 0 else "overestimates"
        interpretation_new = "underestimates" if gap_new > 0 else "overestimates"
    
    print(f"{metric.replace('_', ' ').title()}:")
    print(f"  pi_base: {gap_base:+.3f} (simulation {interpretation_base} performance)")
    print(f"  pi_new:  {gap_new:+.3f} (simulation {interpretation_new} performance)")

print("\n" + "=" * 60)
print("\n4. Deployment Risk Assessment\n")

# Identify metrics with concerning patterns
concerning_patterns = []

for metric in pivot_sim.index:
    sim_base = pivot_sim.loc[metric, 'pi_base']
    sim_new = pivot_sim.loc[metric, 'pi_new']
    real_base = pivot_real.loc[metric, 'pi_base']
    real_new = pivot_real.loc[metric, 'pi_new']
    
    higher_better = metric in positive_metrics
    
    # Check if simulation predicts improvement but real-world shows degradation
    sim_improves = (sim_new > sim_base) if higher_better else (sim_new < sim_base)
    real_improves = (real_new > real_base) if higher_better else (real_new < real_base)
    
    if sim_improves != real_improves:
        concerning_patterns.append((metric, "Prediction mismatch"))
    
    # Check if real-world performance is significantly worse than simulation
    sim_to_real_ratio = real_new / sim_new if sim_new != 0 else 0
    if metric in positive_metrics and sim_to_real_ratio < 0.9:
        concerning_patterns.append((metric, f"Real-world underperforms simulation by {(1-sim_to_real_ratio)*100:.1f}%"))
    elif metric in negative_metrics and sim_to_real_ratio > 1.1:
        concerning_patterns.append((metric, f"Real-world worse than simulation by {(sim_to_real_ratio-1)*100:.1f}%"))

if concerning_patterns:
    print("Concerning patterns identified:")
    for metric, issue in concerning_patterns:
        print(f"  - {metric.replace('_', ' ').title()}: {issue}")
else:
    print("No concerning patterns identified.")

# Calculate overall risk score
risk_factors = []

# Factor 1: Correlation between sim and real
risk_factors.append(1 - abs(pearson_corr))  # Lower correlation = higher risk

# Factor 2: Average simulation error
avg_error = (rel_error_base.mean() + rel_error_new.mean()) / 2
risk_factors.append(min(avg_error / 50, 1.0))  # Normalize to 0-1

# Factor 3: Number of concerning patterns
risk_factors.append(min(len(concerning_patterns) / len(pivot_sim.index), 1.0))

overall_risk = np.mean(risk_factors)

print(f"\nOverall deployment risk score: {overall_risk:.3f} (0 = low risk, 1 = high risk)")
print(f"Risk factors:")
print(f"  1. Simulation-real correlation: {risk_factors[0]:.3f}")
print(f"  2. Average simulation error: {risk_factors[1]:.3f}")
print(f"  3. Concerning patterns: {risk_factors[2]:.3f}")

# Create visualization
os.makedirs("../report/images", exist_ok=True)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Simulation-to-Real-World Correlation Analysis', fontsize=16, fontweight='bold')

# Plot 1: Percentage changes correlation
ax1 = axes[0, 0]
ax1.scatter(pct_sim, pct_real, s=100, alpha=0.7)
ax1.set_xlabel('Percentage Change in Simulation (%)')
ax1.set_ylabel('Percentage Change in Real-World (%)')
ax1.set_title('Correlation of Performance Changes')
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

# Add metric labels
for metric, x, y in zip(pct_sim.index, pct_sim.values, pct_real.values):
    ax1.annotate(metric.replace('_', '\n'), (x, y), 
                 xytext=(5, 5), textcoords='offset points', fontsize=8)

# Add regression line
if len(pct_sim) > 1:
    z = np.polyfit(pct_sim, pct_real, 1)
    p = np.poly1d(z)
    x_range = np.linspace(min(pct_sim), max(pct_sim), 100)
    ax1.plot(x_range, p(x_range), 'r--', alpha=0.7, label=f'Fit: y={z[0]:.3f}x+{z[1]:.3f}')
    ax1.legend()

# Plot 2: Simulation vs Real-world values
ax2 = axes[0, 1]
metrics = pivot_sim.index
x_pos = np.arange(len(metrics))
width = 0.35

sim_base_vals = pivot_sim['pi_base'].values
real_base_vals = pivot_real['pi_base'].values

ax2.bar(x_pos - width/2, sim_base_vals, width, label='Simulation', alpha=0.7)
ax2.bar(x_pos + width/2, real_base_vals, width, label='Real-World', alpha=0.7)
ax2.set_xlabel('Metric')
ax2.set_ylabel('Value (pi_base)')
ax2.set_title('Simulation vs Real-World Values (pi_base)')
ax2.set_xticks(x_pos)
ax2.set_xticklabels([m.replace('_', '\n') for m in metrics], rotation=45, ha='right')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Simulation errors
ax3 = axes[1, 0]
error_data = pd.DataFrame({
    'Metric': list(metrics) * 2,
    'Policy': ['pi_base'] * len(metrics) + ['pi_new'] * len(metrics),
    'Relative_Error': list(rel_error_base.values) + list(rel_error_new.values)
})

sns.boxplot(x='Policy', y='Relative_Error', data=error_data, ax=ax3)
sns.stripplot(x='Policy', y='Relative_Error', data=error_data, ax=ax3, 
              color='black', alpha=0.5, size=6)
ax3.set_xlabel('Policy')
ax3.set_ylabel('Relative Error (%)')
ax3.set_title('Simulation Fidelity by Policy')
ax3.grid(True, alpha=0.3)

# Plot 4: Risk assessment visualization
ax4 = axes[1, 1]
risk_labels = ['Correlation\nRisk', 'Simulation\nError Risk', 'Pattern\nRisk']
risk_values = risk_factors

bars = ax4.bar(risk_labels, risk_values, alpha=0.7)
ax4.set_ylabel('Risk Score (0-1)')
ax4.set_title('Deployment Risk Assessment')
ax4.set_ylim(0, 1)
ax4.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, value in zip(bars, risk_values):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height + 0.02,
             f'{value:.3f}', ha='center', va='bottom')

# Add overall risk
ax4.text(0.5, 0.95, f'Overall Risk: {overall_risk:.3f}', 
         transform=ax4.transAxes, ha='center', va='top',
         fontsize=12, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

plt.tight_layout()
plt.savefig('../report/images/simulation_real_correlation.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n" + "=" * 60)
print("Visualization saved to report/images/simulation_real_correlation.png")
print("Analysis complete.")