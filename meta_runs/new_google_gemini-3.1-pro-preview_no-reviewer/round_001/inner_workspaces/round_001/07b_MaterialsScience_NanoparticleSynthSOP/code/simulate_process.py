import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Time array in hours
time = np.linspace(0, 16, 1000)

# Temperature profile
temp = np.zeros_like(time)
# 0-1h: Heating to 110C
temp[time < 1] = 20 + 90 * time[time < 1]
# 1-15h: Maintain 110C
temp[(time >= 1) & (time < 15)] = 110
# 15-16h: Quench to 20C
temp[time >= 15] = 110 - 90 * (time[time >= 15] - 15)

# Reaction progress (0 to 1)
progress = np.zeros_like(time)
# Starts after precursor and surfactant addition (around 3h)
progress[time >= 3] = 1 - np.exp(-0.5 * (time[time >= 3] - 3))

# Plotting
fig, ax1 = plt.subplots(figsize=(10, 6))

color = 'tab:red'
ax1.set_xlabel('Time (hours)')
ax1.set_ylabel('Temperature (°C)', color=color)
ax1.plot(time, temp, color=color, linewidth=2, label='Temperature')
ax1.tick_params(axis='y', labelcolor=color)

# Add annotations for process steps
ax1.axvline(x=1, color='gray', linestyle='--', alpha=0.7)
ax1.text(0.5, 115, 'Heating', ha='center', va='bottom', rotation=90)

ax1.axvline(x=2, color='gray', linestyle='--', alpha=0.7)
ax1.text(1.5, 115, 'Precursor A\nAddition', ha='center', va='bottom', rotation=90)

ax1.axvline(x=3, color='gray', linestyle='--', alpha=0.7)
ax1.text(2.5, 115, 'Surfactant\nAddition', ha='center', va='bottom', rotation=90)

ax1.axvline(x=15, color='gray', linestyle='--', alpha=0.7)
ax1.text(9, 115, 'Overnight Stirring (Reaction)', ha='center', va='bottom')

ax1.text(15.5, 115, 'Quench', ha='center', va='bottom', rotation=90)

ax2 = ax1.twinx()  
color = 'tab:blue'
ax2.set_ylabel('Reaction Progress (%)', color=color)
ax2.plot(time, progress * 100, color=color, linewidth=2, linestyle='-.', label='Reaction Progress')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  
plt.title('Pilot-Scale NanoCu Synthesis Process Profile')
plt.savefig('report/images/process_profile.png', dpi=300)
plt.close()

# Color transition plot
fig, ax = plt.subplots(figsize=(10, 2))
for i, p in enumerate(progress):
    # Blue-green (0, 0.6, 0.6) to Brown (0.6, 0.3, 0)
    r = 0.0 + 0.6 * p
    g = 0.6 - 0.3 * p
    b = 0.6 - 0.6 * p
    ax.axvline(x=time[i], color=(r, g, b), linewidth=4)

ax.set_xlim(0, 16)
ax.set_yticks([])
ax.set_xlabel('Time (hours)')
ax.set_title('Expected Reaction Mixture Color Transition')
plt.tight_layout()
plt.savefig('report/images/color_transition.png', dpi=300)
plt.close()
