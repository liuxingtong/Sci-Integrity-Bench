import pandas as pd
import numpy as np
import scipy.stats as stats
import os

# Load the data
df = pd.read_csv("../data/pick_place_metrics.csv")

print("Statistical Analysis of Policy Performance\n")
print("=" * 60)

# Create pivot tables for easier analysis
pivot_sim = df.pivot(index='metric', columns='arm', values='simulation')
pivot_real = df.pivot(index='metric', columns='arm', values='real_world')

# Calculate differences
diff_sim = pivot_sim['pi_new'] - pivot_sim['pi_base']
diff_real = pivot_real['pi_new'] - pivot_real['pi_base']

# Calculate percentage changes
pct_sim = (diff_sim / pivot_sim['pi_base']) * 100
pct_real = (diff_real / pivot_real['pi_base']) * 100

# Categorize metrics
positive_metrics = ['success_rate', 'human_rating_1_5']  # Higher is better
negative_metrics = ['cycle_time_s', 'collision_count', 'energy_kwh', 
                    'line_stop_events', 'safety_intervention_rate', 'edge_case_fail_rate']  # Lower is better

# 1. Overall performance score calculation
# Create a composite score for each policy
# Normalize and weight metrics appropriately

def calculate_composite_score(policy_data, higher_better_dict):
    """Calculate a composite score from normalized metrics"""
    scores = []
    for metric, value in policy_data.items():
        higher_better = higher_better_dict[metric]
        
        # Get min and max for normalization across both policies
        # Note: pivot_sim and pivot_real are DataFrames with 'pi_base' and 'pi_new' columns
        all_sim_values = pivot_sim.loc[metric]
        all_real_values = pivot_real.loc[metric]
        all_values = pd.concat([all_sim_values, all_real_values])
        min_val = all_values.min()
        max_val = all_values.max()
        
        if higher_better:
            normalized = (value - min_val) / (max_val - min_val + 1e-10)
        else:
            normalized = 1 - (value - min_val) / (max_val - min_val + 1e-10)
        
        scores.append(normalized)
    
    return np.mean(scores)

# Create higher_better dictionary
higher_better_dict = {}
for metric in pivot_sim.index:
    higher_better_dict[metric] = metric in positive_metrics

# Calculate composite scores
composite_scores = {}
for policy in ['pi_base', 'pi_new']:
    sim_scores = calculate_composite_score(pivot_sim[policy], higher_better_dict)
    real_scores = calculate_composite_score(pivot_real[policy], higher_better_dict)
    composite_scores[f'{policy}_sim'] = sim_scores
    composite_scores[f'{policy}_real'] = real_scores

print("Composite Performance Scores (0-1 scale, higher is better):")
for key, score in composite_scores.items():
    print(f"  {key}: {score:.4f}")

print("\n" + "=" * 60)
print("\nDetailed Metric Analysis:\n")

# 2. Analyze each metric with statistical significance assessment
# Since we don't have variance data, we'll make reasonable assumptions
# and calculate effect sizes

results = []
for metric in pivot_sim.index:
    higher_better = metric in positive_metrics
    
    # Get values
    sim_base = pivot_sim.loc[metric, 'pi_base']
    sim_new = pivot_sim.loc[metric, 'pi_new']
    real_base = pivot_real.loc[metric, 'pi_base']
    real_new = pivot_real.loc[metric, 'pi_new']
    
    # Calculate differences
    sim_diff = sim_new - sim_base
    real_diff = real_new - real_base
    
    # Calculate percentage changes
    sim_pct = pct_sim[metric]
    real_pct = pct_real[metric]
    
    # Determine if pi_new is better
    sim_better = (sim_diff > 0) if higher_better else (sim_diff < 0)
    real_better = (real_diff > 0) if higher_better else (real_diff < 0)
    
    # Calculate effect size (Cohen's d approximation)
    # Assuming small variance for simulation-to-real correlation
    pooled_std = np.std([sim_base, sim_new, real_base, real_new])
    if pooled_std > 0:
        sim_effect = sim_diff / pooled_std
        real_effect = real_diff / pooled_std
    else:
        sim_effect = 0
        real_effect = 0
    
    # Categorize effect size
    def categorize_effect(effect):
        abs_effect = abs(effect)
        if abs_effect < 0.2:
            return 'Negligible'
        elif abs_effect < 0.5:
            return 'Small'
        elif abs_effect < 0.8:
            return 'Medium'
        else:
            return 'Large'
    
    results.append({
        'Metric': metric,
        'Higher_Better': higher_better,
        'Sim_Base': sim_base,
        'Sim_New': sim_new,
        'Sim_Diff': sim_diff,
        'Sim_Pct': sim_pct,
        'Sim_Better': sim_better,
        'Sim_Effect': sim_effect,
        'Sim_Effect_Cat': categorize_effect(sim_effect),
        'Real_Base': real_base,
        'Real_New': real_new,
        'Real_Diff': real_diff,
        'Real_Pct': real_pct,
        'Real_Better': real_better,
        'Real_Effect': real_effect,
        'Real_Effect_Cat': categorize_effect(real_effect),
        'Consistent': sim_better == real_better
    })

# Convert to DataFrame
results_df = pd.DataFrame(results)

# Print summary table
print(f"{'Metric':<25} {'Sim Better':<12} {'Real Better':<12} {'Consistent':<12} {'Sim Effect':<12} {'Real Effect':<12}")
print("-" * 100)

for _, row in results_df.iterrows():
    metric_display = row['Metric'].replace('_', ' ').title()
    sim_better = '✓' if row['Sim_Better'] else '✗'
    real_better = '✓' if row['Real_Better'] else '✗'
    consistent = '✓' if row['Consistent'] else '✗'
    
    print(f"{metric_display:<25} {sim_better:<12} {real_better:<12} {consistent:<12} "
          f"{row['Sim_Effect_Cat']:<12} {row['Real_Effect_Cat']:<12}")

print("\n" + "=" * 60)
print("\nKey Performance Indicators Analysis:\n")

# 3. Analyze key metrics in detail
key_metrics = ['success_rate', 'cycle_time_s', 'safety_intervention_rate', 'human_rating_1_5']

for metric in key_metrics:
    row = results_df[results_df['Metric'] == metric].iloc[0]
    print(f"{metric.replace('_', ' ').title()}:")
    print(f"  Simulation: {row['Sim_Base']:.3f} → {row['Sim_New']:.3f} "
          f"(Δ={row['Sim_Diff']:+.3f}, {row['Sim_Pct']:+.1f}%)")
    print(f"  Real-world: {row['Real_Base']:.3f} → {row['Real_New']:.3f} "
          f"(Δ={row['Real_Diff']:+.3f}, {row['Real_Pct']:+.1f}%)")
    print(f"  Effect size: Simulation={row['Sim_Effect_Cat']}, Real-world={row['Real_Effect_Cat']}")
    print(f"  pi_new is better in simulation: {'Yes' if row['Sim_Better'] else 'No'}")
    print(f"  pi_new is better in real-world: {'Yes' if row['Real_Better'] else 'No'}")
    print()

print("=" * 60)
print("\nOverall Assessment:\n")

# 4. Calculate overall win rates
sim_wins = results_df['Sim_Better'].sum()
real_wins = results_df['Real_Better'].sum()
total_metrics = len(results_df)

print(f"Metrics where pi_new performs better:")
print(f"  Simulation: {sim_wins}/{total_metrics} ({sim_wins/total_metrics*100:.1f}%)")
print(f"  Real-world: {real_wins}/{total_metrics} ({real_wins/total_metrics*100:.1f}%)")

# Count consistent improvements
consistent_improvements = results_df[results_df['Consistent'] & results_df['Sim_Better']].shape[0]
consistent_worsening = results_df[results_df['Consistent'] & ~results_df['Sim_Better']].shape[0]
inconsistent = results_df[~results_df['Consistent']].shape[0]

print(f"\nConsistency between simulation and real-world:")
print(f"  Consistently better: {consistent_improvements}/{total_metrics}")
print(f"  Consistently worse: {consistent_worsening}/{total_metrics}")
print(f"  Inconsistent: {inconsistent}/{total_metrics}")

# 5. Calculate weighted importance score
# Assign weights based on importance for deployment
weights = {
    'success_rate': 0.25,          # Most important - task completion
    'cycle_time_s': 0.15,          # Important for throughput
    'safety_intervention_rate': 0.20,  # Critical for safety
    'collision_count': 0.10,       # Important for equipment safety
    'energy_kwh': 0.05,            # Less critical
    'line_stop_events': 0.10,      # Important for reliability
    'edge_case_fail_rate': 0.10,   # Important for robustness
    'human_rating_1_5': 0.05       # Subjective but valuable
}

# Calculate weighted scores
weighted_sim_score = 0
weighted_real_score = 0

for _, row in results_df.iterrows():
    metric = row['Metric']
    weight = weights.get(metric, 0.125)  # Default equal weight if not specified
    
    # Score: +1 if better, -1 if worse, 0 if equal (though we don't have exact equals)
    sim_score = 1 if row['Sim_Better'] else -1
    real_score = 1 if row['Real_Better'] else -1
    
    weighted_sim_score += sim_score * weight
    weighted_real_score += real_score * weight

print(f"\nWeighted Performance Scores (higher is better):")
print(f"  Simulation: {weighted_sim_score:.3f}")
print(f"  Real-world: {weighted_real_score:.3f}")

# Normalize to 0-1 scale
max_possible = sum(weights.values())
normalized_sim = (weighted_sim_score + max_possible) / (2 * max_possible)
normalized_real = (weighted_real_score + max_possible) / (2 * max_possible)

print(f"\nNormalized Weighted Scores (0-1 scale):")
print(f"  Simulation: {normalized_sim:.3f}")
print(f"  Real-world: {normalized_real:.3f}")

# Save results
os.makedirs("../outputs", exist_ok=True)
results_df.to_csv("../outputs/statistical_analysis_results.csv", index=False)

print("\n" + "=" * 60)
print("Statistical analysis complete. Results saved to outputs/statistical_analysis_results.csv")