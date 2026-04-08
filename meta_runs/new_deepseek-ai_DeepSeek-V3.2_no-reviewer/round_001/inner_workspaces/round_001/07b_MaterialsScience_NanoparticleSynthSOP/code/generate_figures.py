import numpy as np
import matplotlib.pyplot as plt
import os

# Create output directory for images
os.makedirs('report/images', exist_ok=True)

# Figure 1: Temperature profile for nanoparticle synthesis
fig1, ax1 = plt.subplots(figsize=(10, 6))
time = np.linspace(0, 24, 100)  # 24 hours
temp_profile = np.zeros_like(time)

# Simulate temperature profile: ramp to 110°C, hold, cool
for i, t in enumerate(time):
    if t < 1:  # Ramp up phase
        temp_profile[i] = 25 + 85 * t
    elif t < 16:  # Hold at 110°C
        temp_profile[i] = 110
    else:  # Cool down
        temp_profile[i] = 110 - 5 * (t - 16)
        if temp_profile[i] < 25:
            temp_profile[i] = 25

ax1.plot(time, temp_profile, 'b-', linewidth=2)
ax1.axhline(y=110, color='r', linestyle='--', alpha=0.5, label='Target temp (110°C)')
ax1.fill_between(time, 105, 115, alpha=0.1, color='red', label='±5°C tolerance')
ax1.set_xlabel('Time (hours)', fontsize=12)
ax1.set_ylabel('Temperature (°C)', fontsize=12)
ax1.set_title('Temperature Profile for Copper Nanoparticle Synthesis', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_xlim(0, 24)
ax1.set_ylim(20, 120)

# Mark key phases
ax1.annotate('Ramp-up', xy=(0.5, 70), xytext=(2, 80),
             arrowprops=dict(arrowstyle='->', color='black'),
             fontsize=10)
ax1.annotate('Reaction (overnight)', xy=(8, 110), xytext=(8, 100),
             arrowprops=dict(arrowstyle='->', color='black'),
             fontsize=10)
ax1.annotate('Cool-down', xy=(18, 70), xytext=(18, 80),
             arrowprops=dict(arrowstyle='->', color='black'),
             fontsize=10)

plt.tight_layout()
plt.savefig('report/images/temperature_profile.png', dpi=300, bbox_inches='tight')
print("Saved temperature_profile.png")

# Figure 2: Color change during synthesis (simulated UV-Vis spectra)
fig2, ax2 = plt.subplots(figsize=(10, 6))
wavelength = np.linspace(400, 800, 200)

# Simulate UV-Vis spectra at different times
# Initial precursor (blue-green)
initial_spectrum = 0.5 * np.exp(-(wavelength - 650)**2 / (2 * 30**2)) + \
                   0.3 * np.exp(-(wavelength - 450)**2 / (2 * 40**2))

# Intermediate (mixed)
intermediate_spectrum = 0.7 * np.exp(-(wavelength - 600)**2 / (2 * 50**2)) + \
                       0.2 * np.exp(-(wavelength - 450)**2 / (2 * 40**2))

# Final nanoparticles (brown, plasmon resonance)
final_spectrum = 1.0 * np.exp(-(wavelength - 580)**2 / (2 * 40**2)) + \
                 0.3 * np.exp(-(wavelength - 700)**2 / (2 * 80**2))

ax2.plot(wavelength, initial_spectrum, 'b-', linewidth=2, label='Initial (blue-green)')
ax2.plot(wavelength, intermediate_spectrum, 'g-', linewidth=2, label='Intermediate (4 hr)')
ax2.plot(wavelength, final_spectrum, 'r-', linewidth=2, label='Final (brown, 16 hr)')
ax2.axvline(x=580, color='orange', linestyle='--', alpha=0.5, label='Cu NP plasmon (~580 nm)')

ax2.set_xlabel('Wavelength (nm)', fontsize=12)
ax2.set_ylabel('Absorbance (a.u.)', fontsize=12)
ax2.set_title('Simulated UV-Vis Spectra During Nanoparticle Formation', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_xlim(400, 800)
ax2.set_ylim(0, 1.2)

plt.tight_layout()
plt.savefig('report/images/uv_vis_spectra.png', dpi=300, bbox_inches='tight')
print("Saved uv_vis_spectra.png")

# Figure 3: Particle size distribution (simulated TEM results)
fig3, ax3 = plt.subplots(figsize=(10, 6))

# Generate simulated particle size data
np.random.seed(42)
size_mean = 12  # nm
size_std = 2.5  # nm
sizes = np.random.normal(size_mean, size_std, 200)
sizes = sizes[(sizes > 5) & (sizes < 25)]  # Filter reasonable sizes

n, bins, patches = ax3.hist(sizes, bins=20, alpha=0.7, color='steelblue', edgecolor='black')
ax3.axvline(x=size_mean, color='red', linestyle='--', linewidth=2, label=f'Mean: {size_mean:.1f} nm')
ax3.axvline(x=size_mean - size_std, color='orange', linestyle=':', linewidth=1.5, alpha=0.7, label=f'±1σ: {size_std:.1f} nm')
ax3.axvline(x=size_mean + size_std, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)

ax3.set_xlabel('Particle Diameter (nm)', fontsize=12)
ax3.set_ylabel('Frequency', fontsize=12)
ax3.set_title('Simulated Size Distribution of Copper Nanoparticles', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')
ax3.legend()

# Add text box with statistics
stats_text = f'Statistics:\nN = {len(sizes)}\nMean = {np.mean(sizes):.2f} nm\nStd = {np.std(sizes):.2f} nm\nCV = {100*np.std(sizes)/np.mean(sizes):.1f}%'
ax3.text(0.05, 0.95, stats_text, transform=ax3.transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('report/images/size_distribution.png', dpi=300, bbox_inches='tight')
print("Saved size_distribution.png")

# Figure 4: Process flowchart
fig4, ax4 = plt.subplots(figsize=(12, 8))
ax4.axis('off')

# Define process steps
steps = [
    '1. Preparation\nClean glassware\nSet up apparatus\nPurge with N₂',
    '2. Heating\nHeat oil bath to 110°C\nAdd solvent',
    '3. Precursor Addition\nDissolve Cu precursor\nAdd dropwise (1 drop/s)',
    '4. Surfactant Addition\nAdd oleylamine\n(2:1 molar ratio)',
    '5. Reaction\nStir at 300 rpm\n110°C for 12-16 hr',
    '6. Monitoring\nObserve color change\nBlue-green → Brown',
    '7. Quenching\nCool to 60°C\nAdd anti-solvent',
    '8. Workup\nCentrifuge\nWash 3×\nDry or disperse'
]

# Coordinates for steps
x_pos = np.linspace(0.1, 0.9, len(steps))
y_pos = [0.5] * len(steps)

# Draw connecting arrows
for i in range(len(steps)-1):
    ax4.annotate('', xy=(x_pos[i+1], y_pos[i]), xytext=(x_pos[i], y_pos[i]),
                 arrowprops=dict(arrowstyle='->', lw=2, color='gray'))

# Draw process boxes
for i, (step, x, y) in enumerate(zip(steps, x_pos, y_pos)):
    # Create rounded rectangle
    from matplotlib.patches import FancyBboxPatch
    bbox = FancyBboxPatch((x-0.08, y-0.15), 0.16, 0.3,
                          boxstyle="round,pad=0.02",
                          facecolor='lightblue', edgecolor='black', linewidth=1.5)
    ax4.add_patch(bbox)
    
    # Add step number
    ax4.text(x, y+0.1, f'Step {i+1}', ha='center', va='center', fontweight='bold', fontsize=10)
    
    # Add step description
    ax4.text(x, y-0.05, step, ha='center', va='center', fontsize=8, linespacing=1.5)

ax4.set_xlim(0, 1)
ax4.set_ylim(0, 1)
ax4.set_title('Copper Nanoparticle Synthesis Process Flowchart', fontsize=16, fontweight='bold', y=0.9)

plt.tight_layout()
plt.savefig('report/images/process_flowchart.png', dpi=300, bbox_inches='tight')
print("Saved process_flowchart.png")

plt.close('all')
print("All figures generated successfully!")