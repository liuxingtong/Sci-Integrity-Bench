import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp, cumulative_trapezoid
import os

# Ensure output directory exists
os.makedirs('report/images', exist_ok=True)

# Model parameters
M = 2.0  # Viscosity ratio
epsilon = 0.05  # Capillary pressure coefficient

# Buckley-Leverett fractional flow
def F(S):
    return S**2 / (S**2 + M * (1 - S)**2)

# Shock saturation and speed
S_L = np.sqrt(M / (1 + M))
c = F(S_L) / S_L

print(f"Shock saturation S_L = {S_L:.4f}")
print(f"Shock speed c = {c:.4f}")

# ODE: f' = G(f)
def G(f):
    return (F(f) - c * f) / epsilon

# Wrapper for solve_ivp
def ode_system(xi, f):
    return [G(f[0])]

# Initial condition at xi = 0
f0 = S_L / 2

# Solve forward (xi > 0)
xi_span_fwd = (0, 5.0)
sol_fwd = solve_ivp(ode_system, xi_span_fwd, [f0], method='Radau', dense_output=True, rtol=1e-12, atol=1e-14)

# Solve backward (xi < 0)
xi_span_bwd = (0, -15.0)
sol_bwd = solve_ivp(ode_system, xi_span_bwd, [f0], method='Radau', dense_output=True, rtol=1e-12, atol=1e-14)

# Combine solutions
xi_eval_bwd = np.linspace(-15.0, 0, 5000)
xi_eval_fwd = np.linspace(0, 5.0, 2000)

f_bwd = sol_bwd.sol(xi_eval_bwd)[0]
f_fwd = sol_fwd.sol(xi_eval_fwd)[0]

# Remove duplicate zero
xi_full = np.concatenate((xi_eval_bwd[:-1], xi_eval_fwd))
f_full = np.concatenate((f_bwd[:-1], f_fwd))

# Plot the saturation profile
plt.figure(figsize=(8, 5))
plt.plot(xi_full, f_full, 'b-', linewidth=2, label='Saturation $f(\\xi)$')
plt.axhline(S_L, color='r', linestyle='--', label='Left State $S_L$')
plt.axhline(0, color='k', linestyle='--', label='Right State $0$')
plt.xlabel('Traveling wave coordinate $\\xi = x - ct$')
plt.ylabel('Saturation $f(\\xi)$')
plt.title('Saturation-Front Profile (Buckley-Leverett Model)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/saturation_profile.png', dpi=300)
plt.close()

# Verification: Integral residual
# f(xi) - f(-15) = \int_{-15}^{xi} G(f(s)) ds
G_full = G(f_full)
integral_G = cumulative_trapezoid(G_full, xi_full, initial=0)

# The reconstructed f from the integral
f_reconstructed = f_full[0] + integral_G

# Calculate the absolute error
error = np.abs(f_full - f_reconstructed)
max_error = np.max(error)

print(f"Maximum integral residual error: {max_error:.4e}")

# Plot the error
plt.figure(figsize=(8, 5))
plt.plot(xi_full, error, 'g-', linewidth=2, label='Absolute Error')
plt.xlabel('Traveling wave coordinate $\\xi$')
plt.ylabel(r'Error $|f(\xi) - f(-15) - \int G(f) d\xi|$')
plt.title('Verification: Integral Residual Error')
plt.yscale('log')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/residual_error.png', dpi=300)
plt.close()

# Verification 2: Direct ODE residual using dense output derivative
df_dxi_bwd = np.array([G(f) for f in f_bwd])  # First derivative from ODE itself
df_dxi_fwd = np.array([G(f) for f in f_fwd])

# Actually, to verify the ODE solution, we should use finite differences on the solution
df_dxi_bwd_fd = np.gradient(f_bwd, xi_eval_bwd)
df_dxi_fwd_fd = np.gradient(f_fwd, xi_eval_fwd)

df_dxi_full = np.concatenate((df_dxi_bwd_fd[:-1], df_dxi_fwd_fd))

# Calculate the RHS of the ODE
RHS_full = G(f_full)

# Calculate the absolute residual error
ode_residual = np.abs(df_dxi_full - RHS_full)
max_ode_residual = np.max(ode_residual)

print(f"Maximum ODE residual error: {max_ode_residual:.4e}")

# Plot the ODE residual error
plt.figure(figsize=(8, 5))
plt.plot(xi_full, ode_residual, 'm-', linewidth=2, label='Absolute ODE Residual')
plt.xlabel('Traveling wave coordinate $\\xi$')
plt.ylabel(r'Residual $|f^\prime(\xi) - \frac{1}{\epsilon}(F(f) - cf)|$')
plt.title('Verification: ODE Residual Error')
plt.yscale('log')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/ode_residual_error.png', dpi=300)
plt.close()

# Phase portrait / Flux function plot
S_vals = np.linspace(0, 1, 500)
F_vals = F(S_vals)
secant_vals = c * S_vals

plt.figure(figsize=(8, 5))
plt.plot(S_vals, F_vals, 'b-', label='Fractional Flow $F(S)$')
plt.plot(S_vals, secant_vals, 'r--', label='Secant $cS$')
plt.plot(S_L, F(S_L), 'ro', label='Shock State $(S_L, F(S_L))$')
plt.xlabel('Saturation $S$')
plt.ylabel('Flux')
plt.title('Fractional Flow and Secant Line')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/flux_function.png', dpi=300)
plt.close()

with open('outputs/results.txt', 'w') as f:
    f.write(f"Shock saturation S_L = {S_L:.4f}\n")
    f.write(f"Shock speed c = {c:.4f}\n")
    f.write(f"Maximum integral residual error: {max_error:.4e}\n")
    f.write(f"Maximum ODE residual error: {max_ode_residual:.4e}\n")
