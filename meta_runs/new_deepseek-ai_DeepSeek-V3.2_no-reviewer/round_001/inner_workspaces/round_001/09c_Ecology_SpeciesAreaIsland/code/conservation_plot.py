import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load conservation implications data
data = pd.read_csv('outputs/conservation_implications.csv')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Species loss from area reduction
area_loss = np.array(data['area_loss_proportion'])
species_loss = np.array(data['expected_species_loss'])

ax1.plot(area_loss * 100, species_loss * 100, 'b-o', linewidth=3, markersize=8)
ax1.fill_between(area_loss * 100, 0, species_loss * 100, alpha=0.2, color='blue')

# Add specific points mentioned in report
for loss_prop, loss_val in zip([0.5, 0.75, 0.9], [0.164, 0.265, 0.361]):
    ax1.plot(loss_prop * 100, loss_val * 100, 'ro', markersize=10)
    ax1.text(loss_prop * 100 + 2, loss_val * 100 + 2, 
             f'{loss_val*100:.1f}%', fontsize=10, fontweight='bold')

ax1.set_xlabel('Habitat Loss (%)', fontsize=14)
ax1.set_ylabel('Expected Species Loss (%)', fontsize=14)
ax1.set_title('Extinction Risk from Habitat Loss', fontsize=16)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 50)

# Plot 2: Area needed to preserve species
target_prop = np.array(data['target_species_proportion'])
area_needed = np.array(data['required_area_proportion'])

ax2.plot(target_prop * 100, area_needed * 100, 'g-s', linewidth=3, markersize=8)
ax2.fill_between(target_prop * 100, 0, area_needed * 100, alpha=0.2, color='green')

# Add specific points mentioned in report
for target, area_req in zip([0.5, 0.75, 0.9, 0.95], [0.121, 0.396, 0.685, 0.823]):
    ax2.plot(target * 100, area_req * 100, 'ro', markersize=10)
    ax2.text(target * 100 + 2, area_req * 100 + 2, 
             f'{area_req*100:.1f}%', fontsize=10, fontweight='bold')

ax2.set_xlabel('Target Species Preservation (%)', fontsize=14)
ax2.set_ylabel('Minimum Area Required (% of original)', fontsize=14)
ax2.set_title('Reserve Sizing for Conservation Targets', fontsize=16)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(40, 100)
ax2.set_ylim(0, 100)

# Add equation text
fig.text(0.5, 0.02, 
         'Based on power law model: S = 14.31 × A^0.272 | Remaining species proportion = (Remaining area proportion)^0.272',
         ha='center', fontsize=12, style='italic')

plt.tight_layout(rect=[0, 0.05, 1, 0.98])
plt.savefig('report/images/conservation_implications.png', dpi=300, bbox_inches='tight')
plt.close()

print("Conservation implications plot saved to report/images/conservation_implications.png")
