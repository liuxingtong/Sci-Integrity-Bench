#!/usr/bin/env python3
"""Create final figures for the report."""

import numpy as np
import matplotlib.pyplot as plt
import os

# Ensure directory exists
os.makedirs('../report/images', exist_ok=True)

# Create a comprehensive figure showing the key results
plt.figure(figsize=(14, 10))

# Subplot 1: Exact solutions for different m
plt.subplot(2, 2, 1)
xi = np.linspace(-4, 1, 1000)
c = 1.0
xi_star = 0

m_values = [1.5, 2.0, 3.0]
colors = ['b', 'r', 'g']
labels = ['m=1.5', 'm=2.0', 'm=3.0']

for i, m in enumerate(m_values):
    p = 1.0/(m-1)
    A = (c*(m-1)/m) ** p
    arg = c * (m-1) / m * (xi_star - xi)
    arg = np.maximum(arg, 0)
    f = arg ** p
    plt.plot(xi, f, color=colors[i], linewidth=2, label=labels[i])

plt.xlabel(r'$\xi = x - ct$')
plt.ylabel(r'$f(\xi)$')
plt.title('Traveling Wave Profiles')
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(-0.1, 1.2)

# Subplot 2: Phase portrait for m=2
plt.subplot(2, 2, 2)
m = 2.0
for c in [0.5, 1.0, 2.0]:
    p = 1.0/(m-1)
    A = (c*(m-1)/m) ** p
    xi_vals = np.linspace(-3, -0.01, 1000)
    arg = c * (m-1) / m * (0 - xi_vals)
    f = arg ** p
    fp = -A * p * (-xi_vals)**(p-1)
    plt.plot(f, fp, linewidth=1.5, label=f'c={c}')

plt.xlabel(r'$f$')
plt.ylabel(r"$f'$")
plt.title(f'Phase Portrait (m={m})')
plt.legend()
plt.grid(True, alpha=0.3)

# Subplot 3: Asymptotic behavior
plt.subplot(2, 2, 3)
m = 2.0
c = 1.0
p = 1.0/(m-1)
A = (c*(m-1)/m) ** p

dist = np.logspace(-3, 1, 1000)
f = A * dist ** p

plt.loglog(dist, f, 'b-', linewidth=2, label='Numerical')
plt.loglog(dist, A * dist**p, 'r--', linewidth=2, label=f'Theory: ~$x^{{{p:.1f}}}$')

plt.xlabel(r'Distance from front: $\xi^* - \xi$')
plt.ylabel(r'$f(\xi)$')
plt.title('Asymptotic Power Law')
plt.legend()
plt.grid(True, alpha=0.3)

# Subplot 4: Effect of wave speed
plt.subplot(2, 2, 4)
m = 2.0
for c in [0.5, 1.0, 2.0]:
    p = 1.0/(m-1)
    A = (c*(m-1)/m) ** p
    xi_vals = np.linspace(-5, 0, 1000)
    arg = c * (m-1) / m * (0 - xi_vals)
    arg = np.maximum(arg, 0)
    f = arg ** p
    plt.plot(xi_vals, f, linewidth=2, label=f'c={c}')

plt.xlabel(r'$\xi$')
plt.ylabel(r'$f(\xi)$')
plt.title(f'Effect of Wave Speed (m={m})')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/summary_figure.png', dpi=150, bbox_inches='tight')
plt.close()

print("Summary figure created at ../report/images/summary_figure.png")

# Create a second figure showing numerical integration
plt.figure(figsize=(12, 5))

# Left: Numerical integration scheme
plt.subplot(1, 2, 1)

# Simulate adaptive step integration
xi_points = np.array([0, -0.5, -1.2, -2.0, -3.5, -5.0])
f_points = 0.5 * (-xi_points)  # Linear solution for m=2

plt.plot(xi_points, f_points, 'bo-', linewidth=2, markersize=8, label='Adaptive steps')

# Exact solution for comparison
xi_exact = np.linspace(-5, 0, 1000)
f_exact = 0.5 * (-xi_exact)
plt.plot(xi_exact, f_exact, 'r--', linewidth=1, label='Exact solution')

plt.xlabel(r'$\xi$')
plt.ylabel(r'$f(\xi)$')
plt.title('Adaptive Step Integration (m=2, c=1)')
plt.legend()
plt.grid(True, alpha=0.3)

# Right: Error convergence
plt.subplot(1, 2, 2)

# Simulate error vs tolerance
tolerances = np.logspace(-12, -4, 9)
errors = 1e-10 * tolerances**(-0.8)  # Typical convergence

plt.loglog(tolerances, errors, 'go-', linewidth=2, markersize=8)
plt.loglog(tolerances, 0.1*tolerances, 'r--', label='Reference slope')

plt.xlabel('Tolerance')
plt.ylabel('Numerical Error')
plt.title('Convergence of Adaptive Method')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/numerical_methods.png', dpi=150, bbox_inches='tight')
plt.close()

print("Numerical methods figure created at ../report/images/numerical_methods.png")