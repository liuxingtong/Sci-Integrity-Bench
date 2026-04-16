#!/usr/bin/env python3
"""
Analyze the results from porous medium traveling wave integration.
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import glob

# Load all solution files
solution_files = glob.glob('outputs/solution_*.npz')
print(f"Found {len(solution_files)} solution files")

# Analyze each solution
for file_path in solution_files:
    data = np.load(file_path)
    m = data['m']
    c = data['c']
    xi = data['xi']
    f = data['f']
    fp = data['fp']
    
    print(f"\nSolution m={m:.1f}, c={c:.1f}:")
    print(f"  ξ range: [{xi.min():.2f}, {xi.max():.2f}]")
    print(f"  f range: [{f.min():.4f}, {f.max():.4f}]")
    print(f"  Number of points: {len(xi)}")
    
    # Check if solution satisfies boundary conditions
    # f should approach 1 as ξ → -∞ and 0 as ξ → ∞
    # In our integration, we start near 1 and integrate forward
    f_start = f[0]
    f_end = f[-1]
    print(f"  f(start) = {f_start:.6f}, f(end) = {f_end:.6f}")
    
    # Compute wave front thickness
    # Find where f crosses 0.5
    if np.any(f <= 0.5) and np.any(f >= 0.5):
        # Interpolate to find ξ where f = 0.5
        idx = np.where(f <= 0.5)[0]
        if len(idx) > 0:
            i = idx[0]
            if i > 0:
                # Linear interpolation
                x1, x2 = xi[i-1], xi[i]
                y1, y2 = f[i-1], f[i]
                xi_half = x1 + (0.5 - y1) * (x2 - x1) / (y2 - y1)
                print(f"  ξ where f=0.5: {xi_half:.4f}")
    
    # Compute asymptotic decay rate
    # For porous medium equation, near f=0, solution behaves as f ~ ξ^{1/(m-1)}
    # Let's check the tail
    tail_mask = f < 0.1
    if np.sum(tail_mask) > 5:
        xi_tail = xi[tail_mask]
        f_tail = f[tail_mask]
        
        # Fit power law: log(f) = a + b*log(ξ - ξ0)
        # For large ξ, f ~ (ξ - ξ0)^{1/(m-1)}
        # So b should be approximately 1/(m-1)
        
        # Use linear regression on log-log plot
        # Shift ξ so it's positive for log
        xi_shifted = xi_tail - xi_tail.min() + 1e-3
        
        with np.errstate(divide='ignore', invalid='ignore'):
            log_xi = np.log(xi_shifted)
            log_f = np.log(f_tail)
            
            valid = np.isfinite(log_xi) & np.isfinite(log_f)
            if np.sum(valid) > 2:
                log_xi_valid = log_xi[valid]
                log_f_valid = log_f[valid]
                
                # Linear regression
                A = np.vstack([log_xi_valid, np.ones_like(log_xi_valid)]).T
                b, a = np.linalg.lstsq(A, log_f_valid, rcond=None)[0]
                
                expected_b = 1/(m-1)
                print(f"  Tail power law exponent: b = {b:.4f} (expected: {expected_b:.4f})")
                print(f"  Relative error: {abs(b - expected_b)/expected_b*100:.2f}%")

# Create a summary figure comparing different m values
plt.figure(figsize=(12, 8))

colors = plt.cm.viridis(np.linspace(0, 1, len(solution_files)))

for i, file_path in enumerate(solution_files):
    data = np.load(file_path)
    m = data['m']
    c = data['c']
    xi = data['xi']
    f = data['f']
    
    # Normalize ξ for better comparison
    # Shift so that f = 0.5 at ξ = 0
    if np.any(f <= 0.5) and np.any(f >= 0.5):
        idx = np.where(f <= 0.5)[0]
        if len(idx) > 0:
            i_idx = idx[0]
            if i_idx > 0:
                x1, x2 = xi[i_idx-1], xi[i_idx]
                y1, y2 = f[i_idx-1], f[i_idx]
                xi_half = x1 + (0.5 - y1) * (x2 - x1) / (y2 - y1)
                xi_shifted = xi - xi_half
            else:
                xi_shifted = xi
        else:
            xi_shifted = xi
    else:
        xi_shifted = xi
    
    plt.plot(xi_shifted, f, color=colors[i], 
             label=f'm={m:.1f}, c={c:.1f}', alpha=0.7)

plt.xlabel(r'$\xi - \xi_{1/2}$ (shifted so f=0.5 at 0)', fontsize=12)
plt.ylabel(r'$f(\xi)$', fontsize=12)
plt.title('Porous Medium Traveling Waves (normalized)', fontsize=14)
plt.legend(fontsize=10, ncol=2)
plt.grid(True, alpha=0.3)
plt.xlim(-10, 20)

plt.tight_layout()
plt.savefig('report/images/summary_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

print("\nSummary figure saved to report/images/summary_comparison.png")

# Create another figure showing phase portraits for different m
plt.figure(figsize=(12, 8))

# Get unique m values
m_values = []
for f in solution_files:
    m = float(np.load(f)['m'])  # Convert to float
    if m not in m_values:
        m_values.append(m)
m_values.sort()

for m in m_values:
    # Get all solutions with this m
    m_files = [f for f in solution_files if abs(np.load(f)['m'] - m) < 1e-6]
    
    plt.subplot(2, 2, list(m_values).index(m) + 1)
    
    for file_path in m_files:
        data = np.load(file_path)
        c = data['c']
        f = data['f']
        fp = data['fp']
        
        plt.plot(f, fp, label=f'c={c:.1f}', alpha=0.7)
    
    plt.xlabel(r'$f$', fontsize=12)
    plt.ylabel(r"$f'$", fontsize=12)
    plt.title(f'Phase portrait (m={m:.1f})', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Theoretical curve: for traveling wave, there's a relation
    # Try to plot theoretical nullcline
    f_theory = np.linspace(0.01, 0.99, 100)
    # From ODE: f'' = [-c f' - m(m-1) f^{m-2} (f')^2] / (m f^{m-1})
    # At fixed points in phase space, f' would satisfy certain relation
    # For small f', we have approximately f'' ≈ -c/m f^{1-m} f'
    # So phase trajectories approximately follow df'/df ≈ -c/m f^{1-m}
    # This gives f' ≈ A exp(-c/(m(2-m)) f^{2-m}) for m≠2
    
    if m != 2:
        # Approximate solution ignoring nonlinear term
        fp_theory = -0.1 * np.exp(-c/(m*(2-m)) * (f_theory**(2-m) - 0.999**(2-m)))
        plt.plot(f_theory, fp_theory, 'k--', alpha=0.5, label='approx')

plt.tight_layout()
plt.savefig('report/images/phase_portraits.png', dpi=150, bbox_inches='tight')
plt.close()

print("Phase portraits saved to report/images/phase_portraits.png")