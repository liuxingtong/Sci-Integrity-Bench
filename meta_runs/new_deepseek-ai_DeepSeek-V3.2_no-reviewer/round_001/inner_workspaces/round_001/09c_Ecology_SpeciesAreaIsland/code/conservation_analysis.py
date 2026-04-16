import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Load the data and model results
df = pd.read_csv('../data/island_species.csv')
model_results = pd.read_csv('../outputs/model_predictions.csv')

# Load model parameters from the summary file
with open('../outputs/model_summary.txt', 'r') as f:
    content = f.read()
    # Extract c and z values
    import re
    c_match = re.search(r'c = (\d+\.\d+)', content)
    z_match = re.search(r'z = (\d+\.\d+)', content)
    
    if c_match and z_match:
        c = float(c_match.group(1))
        z = float(z_match.group(1))
    else:
        # Default values if extraction fails
        c = 10.0
        z = 0.25
        print("Warning: Could not extract model parameters, using defaults")

print(f"Using power law model: S = {c:.4f} * A^{z:.4f}")

# 1. Analyze habitat loss scenarios
print("\n=== Habitat Loss Scenarios ===")

# Current total area and species (sum across islands)
total_area = df['area_km2'].sum()
total_species_observed = len(set(range(1, df['species_richness'].max() + 1)))  # Approximate

print(f"Total island area: {total_area:.2f} km²")
print(f"Approximate total species pool: {total_species_observed}")

# Create habitat loss scenarios
loss_scenarios = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]  # Proportion of habitat lost

scenario_results = []
for loss_prop in loss_scenarios:
    remaining_area = total_area * (1 - loss_prop)
    # Estimate species remaining using power law
    # Assuming a single large habitat vs. fragmented
    
    # Scenario A: Single large habitat (SLOSS - Single Large Or Several Small)
    species_single = c * remaining_area**z
    
    # Scenario B: Fragmented (using typical z value for fragmented habitats ~0.35)
    z_fragmented = 0.35  # Higher z value for fragmented habitats
    species_fragmented = c * remaining_area**z_fragmented
    
    scenario_results.append({
        'habitat_loss': loss_prop * 100,
        'remaining_area_km2': remaining_area,
        'species_single_large': species_single,
        'species_fragmented': species_fragmented,
        'species_loss_single': 100 * (1 - species_single / (c * total_area**z)),
        'species_loss_fragmented': 100 * (1 - species_fragmented / (c * total_area**z))
    })

scenario_df = pd.DataFrame(scenario_results)
print("\nHabitat loss scenarios:")
print(scenario_df.to_string())

# Save scenarios
scenario_df.to_csv('../outputs/habitat_loss_scenarios.csv', index=False)

# 2. SLOSS analysis (Single Large Or Several Small)
print("\n=== SLOSS Analysis ===")

# Sort islands by area
df_sorted = df.sort_values('area_km2', ascending=False).reset_index(drop=True)

# Calculate cumulative area and species for different strategies
cumulative_area = df_sorted['area_km2'].cumsum()
cumulative_species = []

# For each cumulative area, estimate species using power law
for area in cumulative_area:
    cumulative_species.append(c * area**z)

df_sorted['cumulative_area'] = cumulative_area
df_sorted['cumulative_species_pred'] = cumulative_species

# Alternative: several small islands (reverse order)
df_sorted_small = df.sort_values('area_km2', ascending=True).reset_index(drop=True)
cumulative_area_small = df_sorted_small['area_km2'].cumsum()
cumulative_species_small = []

for area in cumulative_area_small:
    cumulative_species_small.append(c * area**z)

df_sorted_small['cumulative_area'] = cumulative_area_small
df_sorted_small['cumulative_species_pred'] = cumulative_species_small

print("\nTop 5 largest islands:")
print(df_sorted[['island_id', 'area_km2', 'species_richness']].head())
print(f"\nTotal species predicted from all islands: {cumulative_species[-1]:.1f}")

# 3. Create conservation visualizations
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Plot 1: Habitat loss impact
axes[0, 0].plot(scenario_df['habitat_loss'], scenario_df['species_loss_single'], 
                'b-', linewidth=2, marker='o', label='Single large habitat')
axes[0, 0].plot(scenario_df['habitat_loss'], scenario_df['species_loss_fragmented'], 
                'r--', linewidth=2, marker='s', label='Fragmented habitat')
axes[0, 0].set_xlabel('Habitat Loss (%)')
axes[0, 0].set_ylabel('Species Loss (%)')
axes[0, 0].set_title('Impact of Habitat Loss on Species Richness')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].set_ylim(0, 100)

# Add text about z-value implications
text = f'z = {z:.3f} (estimated)\nHigher z → greater species loss\nwith habitat fragmentation'
axes[0, 0].text(0.05, 0.95, text, transform=axes[0, 0].transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Plot 2: SLOSS analysis
axes[0, 1].plot(df_sorted['cumulative_area'], df_sorted['cumulative_species_pred'], 
                'g-', linewidth=2, label='Largest to smallest')
axes[0, 1].plot(df_sorted_small['cumulative_area'], df_sorted_small['cumulative_species_pred'], 
                'm--', linewidth=2, label='Smallest to largest')
axes[0, 1].set_xlabel('Cumulative Area (km²)')
axes[0, 1].set_ylabel('Predicted Species Richness')
axes[0, 1].set_title('SLOSS Analysis: Conservation Strategy Comparison')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Mark key points
max_area = df_sorted['cumulative_area'].iloc[-1]
max_species = df_sorted['cumulative_species_pred'].iloc[-1]
axes[0, 1].axvline(x=max_area/2, color='k', linestyle=':', alpha=0.5)
axes[0, 1].axhline(y=max_species, color='k', linestyle=':', alpha=0.5)

# Plot 3: Area distribution and conservation priority
# Calculate conservation priority score (species per unit area)
df['species_per_area'] = df['species_richness'] / df['area_km2']
df['conservation_priority'] = df['species_per_area'].rank(ascending=False)

# Sort by priority
df_priority = df.sort_values('conservation_priority').head(10)

bars = axes[1, 0].barh(range(len(df_priority)), df_priority['species_per_area'][::-1])
axes[1, 0].set_yticks(range(len(df_priority)))
axes[1, 0].set_yticklabels([f'Island {i}' for i in df_priority['island_id'][::-1]])
axes[1, 0].set_xlabel('Species per km²')
axes[1, 0].set_title('Top 10 Islands by Conservation Priority (Species/Area)')
axes[1, 0].grid(True, alpha=0.3, axis='x')

# Color bars by area
for i, (idx, row) in enumerate(df_priority[::-1].iterrows()):
    bars[i].set_color(plt.cm.viridis(row['area_km2'] / df['area_km2'].max()))

# Add colorbar for area
sm = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(vmin=df['area_km2'].min(), 
                                                              vmax=df['area_km2'].max()))
sm.set_array([])
cbar = plt.colorbar(sm, ax=axes[1, 0])
cbar.set_label('Island Area (km²)')

# Plot 4: Minimum area requirements
# Calculate area needed for different species richness targets
species_targets = [10, 15, 20, 25, 30, 35, 40]
area_requirements = []

for target in species_targets:
    # From S = c*A^z, solve for A: A = (S/c)^(1/z)
    area_required = (target / c) ** (1/z)
    area_requirements.append(area_required)

axes[1, 1].plot(species_targets, area_requirements, 'b-', linewidth=2, marker='o')
axes[1, 1].set_xlabel('Target Species Richness')
axes[1, 1].set_ylabel('Minimum Area Required (km²)')
axes[1, 1].set_title('Minimum Area Requirements for Species Targets')
axes[1, 1].grid(True, alpha=0.3)

# Add current islands as points
axes[1, 1].scatter(df['species_richness'], df['area_km2'], 
                   alpha=0.6, color='red', edgecolors='k', label='Current islands')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('../report/images/conservation_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nConservation analysis visualizations saved to report/images/conservation_analysis.png")

# 4. Generate conservation recommendations
print("\n=== Conservation Recommendations ===")

# Identify key islands for conservation
high_priority = df.nlargest(5, 'species_per_area')[['island_id', 'area_km2', 'species_richness', 'species_per_area']]
large_islands = df.nlargest(3, 'area_km2')[['island_id', 'area_km2', 'species_richness']]

print("\nHigh priority islands (highest species per unit area):")
print(high_priority.to_string(index=False))

print("\nLargest islands (important for SLOSS strategy):")
print(large_islands.to_string(index=False))

# Calculate area needed to protect 50% of current species
current_max_species = c * total_area**z
target_species = 0.5 * current_max_species
area_for_50pct = (target_species / c) ** (1/z)
area_proportion = area_for_50pct / total_area

print(f"\nTo protect 50% of estimated species richness:")
print(f"  Required area: {area_for_50pct:.2f} km²")
print(f"  Proportion of total area: {area_proportion:.2%}")

# Save recommendations
with open('../outputs/conservation_recommendations.txt', 'w') as f:
    f.write("Conservation Planning Recommendations\n")
    f.write("="*60 + "\n\n")
    
    f.write("1. KEY FINDINGS:\n")
    f.write(f"   - Power law exponent (z) = {z:.4f}\n")
    f.write(f"   - Total island area = {total_area:.2f} km²\n")
    f.write(f"   - Estimated species pool = {current_max_species:.1f} species\n\n")
    
    f.write("2. HABITAT LOSS IMPACT:\n")
    f.write("   - Each 10% habitat loss leads to ~{:.1f}% species loss\n".format(
        scenario_df.loc[scenario_df['habitat_loss'] == 10, 'species_loss_single'].values[0]))
    f.write("   - Fragmentation increases species loss due to higher z-value\n\n")
    
    f.write("3. CONSERVATION PRIORITIES:\n")
    f.write("   High priority islands (species/area efficiency):\n")
    for _, row in high_priority.iterrows():
        f.write(f"   - Island {row['island_id']}: {row['species_richness']} species on {row['area_km2']:.2f} km² ")
        f.write(f"({row['species_per_area']:.2f} species/km²)\n")
    
    f.write("\n   Key large islands (SLOSS strategy):\n")
    for _, row in large_islands.iterrows():
        f.write(f"   - Island {row['island_id']}: {row['area_km2']:.2f} km² with {row['species_richness']} species\n")
    
    f.write("\n4. AREA REQUIREMENTS:\n")
    f.write(f"   - To protect 50% of species: {area_for_50pct:.2f} km² ({area_proportion:.1%} of total)\n")
    f.write("   - Minimum areas for target richness:\n")
    for target, area in zip(species_targets, area_requirements):
        f.write(f"     {target} species: {area:.2f} km²\n")
    
    f.write("\n5. RECOMMENDATIONS:\n")
    f.write("   a) Protect high-priority small islands for cost-effectiveness\n")
    f.write("   b) Maintain connectivity between habitats to reduce fragmentation effects\n")
    f.write("   c) Prioritize protection of largest islands for maximum species preservation\n")
    f.write("   d) Aim for at least {:.1f} km² protected area to conserve 50% of species\n".format(area_for_50pct))

print("\nConservation recommendations saved to outputs/conservation_recommendations.txt")
print("\nConservation analysis complete!")