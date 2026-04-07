#!/usr/bin/env python3
"""
Analysis and validation tools for Copper Nanoparticle Synthesis SOP.
This script provides calculations and simulations for pilot-scale synthesis.
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# Create outputs directory if it doesn't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

def calculate_reagent_amounts(target_mass_g=1.0, precursor_mw=261.76):
    """
    Calculate reagent amounts for copper nanoparticle synthesis.
    
    Parameters:
    target_mass_g: Target mass of copper nanoparticles in grams
    precursor_mw: Molecular weight of copper precursor (Cu(acac)₂ = 261.76 g/mol)
    
    Returns:
    Dictionary with calculated amounts
    """
    # Copper atomic weight
    cu_mw = 63.55  # g/mol
    
    # Calculate moles of copper needed
    moles_cu = target_mass_g / cu_mw
    
    # Calculate mass of precursor needed (assuming 1:1 Cu:precursor)
    precursor_mass = moles_cu * precursor_mw
    
    # Typical surfactant volume (5-10 mL per 100 mg precursor)
    surfactant_ratio = 7.5  # mL per 100 mg, average
    surfactant_ml = (precursor_mass * 1000) * (surfactant_ratio / 100)
    
    # Solvent volume for 0.1-0.2 M concentration
    concentration = 0.15  # M, average
    solvent_volume_l = moles_cu / concentration
    solvent_volume_ml = solvent_volume_l * 1000
    
    return {
        'target_nanoparticles_g': target_mass_g,
        'precursor_mass_g': precursor_mass,
        'surfactant_volume_ml': surfactant_ml,
        'solvent_volume_ml': solvent_volume_ml,
        'moles_copper': moles_cu,
        'concentration_M': concentration
    }

def simulate_temperature_profile(duration_hours=16, setpoint=110, ambient=25):
    """
    Simulate temperature profile during synthesis.
    Simple first-order response to setpoint.
    """
    # Time array in minutes
    time_min = np.linspace(0, duration_hours * 60, 1000)
    
    # Simple thermal model: T = T_set - (T_set - T_amb) * exp(-t/tau)
    tau = 30  # time constant in minutes
    
    temperature = setpoint - (setpoint - ambient) * np.exp(-time_min / tau)
    
    # Add some noise to simulate real conditions
    noise = np.random.normal(0, 0.5, len(time_min))
    temperature += noise
    
    return time_min, temperature

def simulate_uv_vis_spectrum(particle_size_nm=10):
    """
    Simulate UV-Vis spectrum for copper nanoparticles.
    Copper nanoparticles show plasmon resonance around 570-600 nm.
    """
    wavelength = np.linspace(400, 800, 400)
    
    # Gaussian peak for plasmon resonance
    # Peak position depends on size: smaller particles = blue shift
    peak_position = 580 + (particle_size_nm - 10) * 2  # nm
    
    # Peak width depends on size distribution
    peak_width = 30 + (particle_size_nm - 10) * 1  # nm
    
    intensity = np.exp(-(wavelength - peak_position)**2 / (2 * peak_width**2))
    
    # Add baseline and noise
    baseline = 0.1 * np.exp(-(wavelength - 500) / 100)
    noise = np.random.normal(0, 0.02, len(wavelength))
    
    spectrum = intensity + baseline + noise
    spectrum = spectrum / np.max(spectrum)  # Normalize
    
    return wavelength, spectrum

def simulate_color_change(reaction_time_hours=16):
    """
    Simulate color change during reaction.
    From blue-green (copper precursor) to brown (copper nanoparticles).
    """
    time_points = np.linspace(0, reaction_time_hours, 100)
    
    # Color transition modeled as sigmoid function
    # RGB values for start (blue-green) and end (brown)
    start_color = np.array([0, 0.5, 0.5])  # Blue-green
    end_color = np.array([0.4, 0.2, 0.0])  # Brown
    
    # Sigmoid transition
    transition = 1 / (1 + np.exp(-(time_points - reaction_time_hours/2) / 2))
    
    colors = start_color[np.newaxis, :] + transition[:, np.newaxis] * (end_color - start_color)
    
    return time_points, colors

def generate_figures():
    """Generate all analysis figures for the report."""
    
    # Figure 1: Reagent calculation for different scales
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    scales = [0.1, 0.5, 1.0, 2.0, 5.0]  # Target masses in grams
    precursor_masses = []
    surfactant_volumes = []
    
    for scale in scales:
        calc = calculate_reagent_amounts(target_mass_g=scale)
        precursor_masses.append(calc['precursor_mass_g'])
        surfactant_volumes.append(calc['surfactant_volume_ml'])
    
    ax1.plot(scales, precursor_masses, 'o-', linewidth=2, markersize=8)
    ax1.set_xlabel('Target Nanoparticle Mass (g)')
    ax1.set_ylabel('Precursor Mass Required (g)')
    ax1.set_title('Precursor Scaling')
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(scales, surfactant_volumes, 's-', linewidth=2, markersize=8, color='orange')
    ax2.set_xlabel('Target Nanoparticle Mass (g)')
    ax2.set_ylabel('Surfactant Volume Required (mL)')
    ax2.set_title('Surfactant Scaling')
    ax2.grid(True, alpha=0.3)
    
    fig1.tight_layout()
    fig1.savefig('../report/images/figure1_reagent_scaling.png', dpi=300, bbox_inches='tight')
    
    # Figure 2: Temperature profile
    fig2, ax = plt.subplots(figsize=(10, 6))
    time_min, temperature = simulate_temperature_profile()
    ax.plot(time_min/60, temperature, linewidth=2)
    ax.axhline(y=110, color='r', linestyle='--', alpha=0.5, label='Setpoint (110°C)')
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Temperature (°C)')
    ax.set_title('Simulated Temperature Profile During Synthesis')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_xlim(0, 16)
    ax.set_ylim(20, 120)
    fig2.savefig('../report/images/figure2_temperature_profile.png', dpi=300, bbox_inches='tight')
    
    # Figure 3: UV-Vis spectra for different particle sizes
    fig3, ax = plt.subplots(figsize=(10, 6))
    sizes = [5, 10, 15, 20]  # nm
    colors = ['blue', 'green', 'orange', 'red']
    
    for size, color in zip(sizes, colors):
        wavelength, spectrum = simulate_uv_vis_spectrum(particle_size_nm=size)
        ax.plot(wavelength, spectrum, color=color, linewidth=2, label=f'{size} nm')
    
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Normalized Absorbance')
    ax.set_title('Simulated UV-Vis Spectra for Different Particle Sizes')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_xlim(400, 800)
    fig3.savefig('../report/images/figure3_uv_vis_spectra.png', dpi=300, bbox_inches='tight')
    
    # Figure 4: Color change during reaction
    fig4, ax = plt.subplots(figsize=(12, 4))
    time_points, colors = simulate_color_change()
    
    # Create a color bar showing the transition
    for i in range(len(time_points)-1):
        ax.fill_between([time_points[i], time_points[i+1]], 
                         [0, 0], [1, 1], 
                         color=colors[i], 
                         edgecolor='none')
    
    ax.set_xlabel('Reaction Time (hours)')
    ax.set_title('Color Transition During Synthesis: Blue-green → Brown')
    ax.set_yticks([])
    ax.set_xlim(0, 16)
    ax.text(1, 0.5, 'Start: Copper precursor\n(Blue-green)', 
            verticalalignment='center', fontweight='bold')
    ax.text(12, 0.5, 'End: Copper nanoparticles\n(Brown)', 
            verticalalignment='center', fontweight='bold')
    fig4.savefig('../report/images/figure4_color_transition.png', dpi=300, bbox_inches='tight')
    
    # Figure 5: Process flowchart
    fig5, ax = plt.subplots(figsize=(10, 8))
    ax.axis('off')
    
    # Draw process flowchart
    steps = [
        ('Preparation', 0.5, 0.9),
        ('Heat to 110°C', 0.5, 0.75),
        ('Add Precursor\nDropwise', 0.5, 0.6),
        ('Add Surfactant', 0.5, 0.45),
        ('Stir Overnight\n(12-16 hr)', 0.5, 0.3),
        ('Quench & Workup', 0.5, 0.15)
    ]
    
    for i, (text, x, y) in enumerate(steps):
        # Draw box
        box = plt.Rectangle((x-0.15, y-0.05), 0.3, 0.1, 
                           facecolor='lightblue', edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontweight='bold')
        
        # Draw arrow to next step
        if i < len(steps)-1:
            ax.arrow(x, y-0.05, 0, -0.1, head_width=0.03, head_length=0.02, 
                    fc='black', ec='black', linewidth=1.5)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('Copper Nanoparticle Synthesis Process Flow', fontsize=14, fontweight='bold')
    fig5.savefig('../report/images/figure5_process_flowchart.png', dpi=300, bbox_inches='tight')
    
    plt.close('all')
    print("Generated 5 figures in ../report/images/")

def main():
    """Main function to run all analyses."""
    print("Copper Nanoparticle SOP Analysis Tool")
    print("=" * 40)
    
    # Example calculation
    calc = calculate_reagent_amounts(target_mass_g=1.0)
    print("\nExample calculation for 1.0 g nanoparticles:")
    for key, value in calc.items():
        print(f"  {key}: {value:.3f}")
    
    # Generate figures
    print("\nGenerating analysis figures...")
    generate_figures()
    
    # Save calculation results
    import json
    with open('../outputs/calculations.json', 'w') as f:
        json.dump(calc, f, indent=2)
    
    print("\nAnalysis complete. Results saved to outputs/ and report/images/")

if __name__ == "__main__":
    main()