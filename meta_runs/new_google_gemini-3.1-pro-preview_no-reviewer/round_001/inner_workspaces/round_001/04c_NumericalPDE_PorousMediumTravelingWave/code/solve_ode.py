import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp, cumulative_trapezoid
import os

# Ensure output directory exists
os.makedirs('report/images', exist_ok=True)

# Model parameters
M = 1.0
epsilon = 0.05

# Buckley-Leverett fractional flow
def F(S):
    return S**2 / (S**2 + M * (1 - S)**2)

# Shock saturation and speed
S_star = 1 / np.sqrt(2)
c = (np.sqrt(2) + 1) / 2

print(f"Shock saturation S* = {S_star:.4f}")
print(f"Shock speed c = {c:.4f}")

# ODE: f' = G(f)
def G(f):
    return (F(f) - c * f) / epsilon

# Wrapper for solve_ivp
def ode_system(xi, f):
    return [G(f[0])]

# Initial condition at xi = 0
f0 = S_star / 2

# Solve forward (xi > 0)
xi_span_fwd = (0, 2.0)
sol_fwd = solve_ivp(ode_system, xi_span_fwd, [f0], method='RK45', dense_output=True, rtol=1e-8, atol=1e-10)

# Solve backward (xi < 0)
xi_span_bwd = (0, -2.0)
sol_bwd = solve_ivp(ode_system, xi_span_bwd, [f0], method='RK45', dense_output=True, rtol=1e-8, atol=1e-10)

# Combine solutions
xi_eval_bwd = np.linspace(-2.0, 0, 200)
xi_eval_fwd = np.linspace(0, 2.0, 200)

f_bwd = sol_bwd.sol(xi_eval_bwd)[0]
f_fwd = sol_fwd.sol(xi_eval_fwd)[0]

# Remove duplicate zero
xi_full = np.concatenate((xi_eval_bwd[:-1], xi_eval_fwd))
f_full = np.concatenate((f_bwd[:-1], f_fwd))

# Plot the saturation profile
plt.figure(figsize=(8, 5))
plt.plot(xi_full, f_full, 'b-', label='Saturation $f(\\xi)$')
plt.axhline(S_star, color='r', linestyle='--', label='Shock Saturation $S^*$')
plt.axhline(0, color='k', linestyle='--', label='Zero Saturation')
plt.xlabel('Traveling wave coordinate $\\xi = x - ct$')
plt.ylabel('Saturation $f(\\xi)$')
plt.title('Saturation-Front Profile (Buckley-Leverett Model)')
plt.legend()
plt.grid(True)
plt.savefig('report/images/saturation_profile.png', dpi=300)
plt.close()

# Verification: Integral residual
# f(xi) - f(-2) = \int_{-2}^{xi} G(f(s)) ds
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
plt.plot(xi_full, error, 'g-', label='Absolute Error')
plt.xlabel('Traveling wave coordinate $\\xi$')
plt.ylabel('Error $|f(\\xi) - f(-2) - \\int G(f) d\\xi|$')
plt.title('Verification: Integral Residual Error')
plt.yscale('log')
plt.legend()
plt.grid(True)
plt.savefig('report/images/residual_error.png', dpi=300)
plt.close()

# Also verify using finite differences
df_dxi_fd = np.gradient(f_full, xi_full)
fd_error = np.abs(df_dxi_fd - G_full)
max_fd_error = np.max(fd_error)
print(f"Maximum finite difference residual error: {max_fd_error:.4e}")

with open('outputs/results.txt', 'w') as f:
    f.write(f"Shock saturation S* = {S_star:.4f}\n")
    f.write(f"Shock speed c = {c:.4f}\n")
    f.write(f"Maximum integral residual error: {max_error:.4e}\n")
    f.write(f"Maximum finite difference residual error: {max_fd_error:.4e}\n")
