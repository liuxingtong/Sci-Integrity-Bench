#!/usr/bin/env python3
"""Generate all figures needed for the report."""

import numpy as np
import matplotlib.pyplot as plt
import os

# Create directory
os.makedirs('report/images', exist_ok=True)

# 1. Exact solutions for different m
xi = np.linspace(-5, 2, 1000)
xi_star = 0
c = 1.0

plt.figure(figsize=(10, 6))

m_values = [1.5, 2.0, 3.0, 4.0]
colors = ['b', 'r', 'g', 'm']

for i, m in enumerate(m_values):
    p = 1.0/(m-1)
    A = (c*(m-1)/m) ** p
    
    # Exact solution
    arg = c * (m-1) / m * (xi_star - xi)
    arg = np.maximum(arg, 0)
    f = arg ** p
    
    plt.plot(xi, f, color=colors[i], linewidth=2, label=f'm={m}')

plt.xlabel(r'$\xi = x - ct$', fontsize=12)
plt.ylabel(r'$f(\xi)$', fontsize=12)
plt.title('Exact Traveling Wave Solutions', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.ylim(-0.1, 1.5)
plt.tight_layout()
plt.savefig('report/images/exact_solutions_all_m.png', dpi=150, bbox_inches='tight')
plt.close()

# 2. Numerical vs exact for m=2
from scipy.integrate import solve_ivp

def porous_ode(xi, y, m, c):
    f, fp = y
    if f < 1e-12:
        f = 1e-12
    fpp = (-c*fp - m*(m-1)*f**(m-2)*fp**2) / (m*f**(m-1))
    return [fp, fpp]

m_test = 2.0
c_test = 1.0
p_test = 1.0/(m_test-1)
A_test = (c_test*(m_test-1)/m_test) ** p_test

epsilon = 1e-4
xi_start = -epsilon
f_start = A_test * epsilon**p_test
fp_start = -A_test * p_test * epsilon**(p_test-1)

sol = solve_ivp(
    lambda t, y: porous_ode(t, y, m_test, c_test),
    [xi_start, -10.0],
    [f_start, fp_start],
    method='DOP853',
    rtol=1e-8,
    atol=1e-10,
    dense_output=True
)

plt.figure(figsize=(10, 6))
plt.plot(sol.t, sol.y[0], 'bo', markersize=3, label='Numerical')

xi_exact = np.linspace(-10, 0, 1000)
arg_exact = c_test * (m_test-1) / m_test * (0 - xi_exact)
arg_exact = np.maximum(arg_exact, 0)
f_exact = arg_exact ** (1.0/(m_test-1))
plt.plot(xi_exact, f_exact, 'r-', label='Exact')

plt.xlabel(r'$\xi$', fontsize=12)
plt.ylabel(r'$f(\xi)$', fontsize=12)
plt.title(f'Numerical vs Exact Solution (m={m_test}, c={c_test})', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/numerical_vs_exact.png', dpi=150, bbox_inches='tight')
plt.close()

# 3. Phase portraits
plt.figure(figsize=(12, 8))

for i, m in enumerate([1.5, 2.0, 3.0]):
    plt.subplot(2, 2, i+1)
    
    for c in [1.0, 2.0]:
        p = 1.0/(m-1)
        A = (c*(m-1)/m) ** p
        
        # Generate trajectory
        xi_vals = np.linspace(-5, -0.01, 1000)
        arg = c * (m-1) / m * (0 - xi_vals)
        f = arg ** p
        fp = -A * p * (-xi_vals)**(p-1)
        
        plt.plot(f, fp, linewidth=1.5, label=f'c={c}')
    
    plt.xlabel(r'$f$', fontsize=12)
    plt.ylabel(r"$f'$", fontsize=12)
    plt.title(f'Phase Portrait (m={m})', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/final_phase_portraits.png', dpi=150, bbox_inches='tight')
plt.close()

# 4. Asymptotic behavior check
plt.figure(figsize=(12, 8))

for i, m in enumerate([1.5, 2.0, 3.0]):
    plt.subplot(2, 2, i+1)
    
    c = 1.0
    p = 1.0/(m-1)
    A = (c*(m-1)/m) ** p
    
    # Generate solution
    xi_vals = np.linspace(-2, -0.001, 1000)
    dist = -xi_vals  # distance from front at 0
    f = A * dist ** p
    
    plt.loglog(dist, f, 'bo', markersize=3, label='Solution')
    
    # Theoretical line
    dist_fit = np.logspace(-3, 1, 100)
    f_fit = A * dist_fit ** p
    plt.loglog(dist_fit, f_fit, 'r-', linewidth=2, label=f'~dist$^{{{p:.2f}}}$')
    
    plt.xlabel(r'$\xi^* - \xi$', fontsize=12)
    plt.ylabel(r'$f(\xi)$', fontsize=12)
    plt.title(f'Asymptotic Check (m={m})', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/final_asymptotic_check.png', dpi=150, bbox_inches='tight')
plt.close()

# 5. Scaled profiles
plt.figure(figsize=(10, 6))

m_fixed = 2.0
colors = ['b', 'r', 'g']

for i, c in enumerate([0.5, 1.0, 2.0]):
    p = 1.0/(m_fixed-1)
    A = (c*(m_fixed-1)/m_fixed) ** p
    
    xi_vals = np.linspace(-10, 0, 1000)
    arg = c * (m_fixed-1) / m_fixed * (0 - xi_vals)
    arg = np.maximum(arg, 0)
    f = arg ** p
    
    # Scale for comparison
    xi_scaled = xi_vals * c
    
    plt.plot(xi_scaled, f, color=colors[i], linewidth=2, label=f'c={c}')

plt.xlabel(r'$c(\xi - \xi^*)$', fontsize=12)
plt.ylabel(r'$f(\xi)$', fontsize=12)
plt.title(f'Scaled Profiles (m={m_fixed})', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.xlim(-20, 5)
plt.ylim(-0.1, 1.5)
plt.tight_layout()
plt.savefig('report/images/final_profiles_scaled.png', dpi=150, bbox_inches='tight')
plt.close()

print("Generated all report figures in report/images/")