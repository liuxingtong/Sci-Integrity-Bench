import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches

# Figure 1: Temperature Profile
time_hours = np.array([0, 1, 2, 3, 15, 16, 17, 18])
temperature = np.array([25, 110, 110, 110, 110, 25, 25, 25])

plt.figure(figsize=(10, 6))
plt.plot(time_hours, temperature, marker='o', linestyle='-', color='red', linewidth=2)
plt.title('Temperature Profile for Pilot-Scale NanoCu Synthesis', fontsize=14)
plt.xlabel('Time (hours)', fontsize=12)
plt.ylabel('Temperature (°C)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.axvspan(1, 15, color='yellow', alpha=0.2, label='Reaction Phase (Stirred Overnight)')
plt.axvspan(15, 18, color='blue', alpha=0.1, label='Quench / Workup Phase')
plt.legend()
plt.tight_layout()
plt.savefig('report/images/temperature_profile.png')
plt.close()

# Figure 2: Color Change Timeline
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, 16)
ax.set_ylim(0, 1)
ax.axis('off')

# Create a gradient or distinct color blocks
colors = ['#008080', '#2E8B57', '#556B2F', '#8B4513', '#654321']
positions = [0, 4, 8, 12, 16]

for i in range(len(colors) - 1):
    rect = patches.Rectangle((positions[i], 0), positions[i+1] - positions[i], 1, color=colors[i])
    ax.add_patch(rect)

# Add final color
rect = patches.Rectangle((positions[-2], 0), positions[-1] - positions[-2], 1, color=colors[-1])
ax.add_patch(rect)

ax.text(2, 0.5, 'Blue-Green\n(Precursor)', color='white', ha='center', va='center', fontsize=12, fontweight='bold')
ax.text(14, 0.5, 'Brown\n(NanoCu)', color='white', ha='center', va='center', fontsize=12, fontweight='bold')

plt.title('Expected Color Change During Synthesis', fontsize=14)
plt.tight_layout()
plt.savefig('report/images/color_change.png')
plt.close()
