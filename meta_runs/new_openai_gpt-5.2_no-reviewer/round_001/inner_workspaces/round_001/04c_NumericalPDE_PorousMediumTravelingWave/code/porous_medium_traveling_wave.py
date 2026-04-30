"""Numerical integration of a porous-medium traveling-wave ODE.

Model (convection–diffusion porous medium / generalized Burgers):
    u_t + (u^m)_x = (u^m)_{xx},     m>1.

Traveling wave u(x,t)=f(\xi), \xi=x-ct gives
    -c f' + (f^m)' = (f^m)''
or
    (f^m)'' - (f^m)' + c f' = 0.

Integrating once and choosing the integration constant using boundary states
f(-\infty)=1, f(+\infty)=0 implies c = (1^m-0)/(1-0)=1 and constant A=0:
    (f^m)' - f^m + f = 0.

We integrate the equivalent first-order ODE for f(\xi) on (0,1):
    f' = (f^m - f) / (m f^{m-1}).

For m=3 an explicit solution exists:
    f(\xi) = sqrt(1 - A exp(2\xi/3)) for \xi <= \xi_front,
    f(\xi)=0 for \xi>\xi_front,
with A determined by a phase condition, e.g. f(0)=1/2.

This script:
  * integrates the ODE with solve_ivp (RK45), using an event to stop at f=floor;
  * compares to the m=3 explicit solution;
  * computes discrete residuals of the first- and second-order ODEs.

Outputs:
  outputs/solution.csv
  report/images/profile.png
  report/images/residuals.png

Run:
  python -m code.porous_medium_traveling_wave
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from dataclasses import dataclass
from scipy.integrate import solve_ivp


@dataclass
class Params:
    m: float = 3.0
    c: float = 1.0
    f0: float = 0.5
    xi0: float = 0.0
    xi_left: float = -12.0
    xi_right: float = 2.0
    f_floor: float = 1e-8
    rtol: float = 1e-10
    atol: float = 1e-12
    max_step: float = 0.01
    n_grid: int = 4000


def rhs_first_order(xi: float, y: np.ndarray, p: Params) -> np.ndarray:
    f = float(y[0])
    # Enforce f>=0 for numerical safety.
    f = max(f, 0.0)
    if f <= 0:
        return np.array([0.0])
    m = p.m
    return np.array([(f**p.m - p.c * f) / (m * f ** (m - 1.0))])


def event_hit_floor(xi: float, y: np.ndarray, p: Params) -> float:
    # stop when f reaches the floor (approaching the sharp front)
    return float(y[0] - p.f_floor)


event_hit_floor.terminal = True
event_hit_floor.direction = -1


def integrate_profile(p: Params) -> dict:
    """Integrate forward and backward from (xi0,f0)."""

    # Backward integration (toward -infty plateau)
    sol_left = solve_ivp(
        fun=lambda xi, y: rhs_first_order(xi, y, p),
        t_span=(p.xi0, p.xi_left),
        y0=np.array([p.f0], dtype=float),
        dense_output=True,
        rtol=p.rtol,
        atol=p.atol,
        max_step=p.max_step,
    )

    # Forward integration (toward the front at f=0)
    sol_right = solve_ivp(
        fun=lambda xi, y: rhs_first_order(xi, y, p),
        t_span=(p.xi0, p.xi_right),
        y0=np.array([p.f0], dtype=float),
        events=lambda xi, y: event_hit_floor(xi, y, p),
        dense_output=True,
        rtol=p.rtol,
        atol=p.atol,
        max_step=p.max_step,
    )

    xi_front = None
    if sol_right.t_events and len(sol_right.t_events[0]) > 0:
        xi_front = float(sol_right.t_events[0][0])

    return {
        "sol_left": sol_left,
        "sol_right": sol_right,
        "xi_front": xi_front,
    }


def f_exact_m3(xi: np.ndarray, f_at_xi0: float = 0.5, xi0: float = 0.0) -> tuple[np.ndarray, float]:
    """Exact traveling wave for m=3, c=1 satisfying f(xi0)=f_at_xi0.

    For xi <= xi_front: f = sqrt(1 - A exp(2(xi-xi0)/3)), else 0.
    """
    A = 1.0 - f_at_xi0**2
    s = 1.0 - A * np.exp(2.0 * (xi - xi0) / 3.0)
    f = np.where(s > 0, np.sqrt(s), 0.0)
    xi_front = xi0 + 1.5 * np.log(1.0 / A)
    return f, float(xi_front)


def compute_residuals(xi: np.ndarray, f: np.ndarray, p: Params) -> dict:
    """Compute discrete residuals for the integrated first- and second-order ODEs."""
    m, c = p.m, p.c
    q = f**m

    # Use second-order accurate gradients on a uniform xi grid.
    q_xi = np.gradient(q, xi, edge_order=2)
    q_xixi = np.gradient(q_xi, xi, edge_order=2)
    f_xi = np.gradient(f, xi, edge_order=2)

    # First integral residual: q' - q + c f = 0 (c=1 here)
    r1 = q_xi - q + c * f

    # Second-order residual: q'' - q' + c f' = 0
    r2 = q_xixi - q_xi + c * f_xi

    # L2 norms and relative measures
    def l2(x: np.ndarray) -> float:
        return float(np.sqrt(np.trapz(x * x, xi)))

    denom1 = l2(q) + l2(c * f) + 1e-30
    denom2 = l2(q_xi) + l2(c * f_xi) + 1e-30

    return {
        "r1": r1,
        "r2": r2,
        "l2_r1": l2(r1),
        "l2_r2": l2(r2),
        "rel_l2_r1": l2(r1) / denom1,
        "rel_l2_r2": l2(r2) / denom2,
    }


def main():
    p = Params()
    if abs(p.m - 3.0) > 1e-12:
        raise ValueError("This demo/report is set up for m=3 to allow an exact solution.")

    out = integrate_profile(p)
    sol_left, sol_right = out["sol_left"], out["sol_right"]

    # Build a uniform grid spanning the computed part of the wave.
    # We stop at the event for the forward integration; beyond that we can extend as f=0.
    xi_stop = out["xi_front"] if out["xi_front"] is not None else p.xi_right
    xi = np.linspace(p.xi_left, xi_stop, p.n_grid)

    f = np.empty_like(xi)
    left_mask = xi <= p.xi0
    right_mask = ~left_mask
    f[left_mask] = sol_left.sol(xi[left_mask])[0]
    f[right_mask] = sol_right.sol(xi[right_mask])[0]

    # Clip very small negative numerical noise.
    f = np.clip(f, 0.0, 1.5)

    fex, xi_front_exact = f_exact_m3(xi, f_at_xi0=p.f0, xi0=p.xi0)

    res = compute_residuals(xi, f, p)

    # Save solution table
    df = pd.DataFrame({
        "xi": xi,
        "f_num": f,
        "f_exact": fex,
        "r1": res["r1"],
        "r2": res["r2"],
    })
    df.to_csv("outputs/solution.csv", index=False)

    # Plot profile
    plt.figure(figsize=(7.2, 4.2))
    plt.plot(xi, f, lw=2.0, label="numerical")
    plt.plot(xi, fex, lw=2.0, ls="--", label="exact (m=3)")
    plt.axvline(out["xi_front"] if out["xi_front"] is not None else np.nan, color="k", alpha=0.2)
    plt.xlabel(r"$\\xi=x-ct$")
    plt.ylabel(r"$f(\\xi)$")
    plt.title(r"Porous-medium traveling wave ($u_t+(u^3)_x=(u^3)_{xx}$, $c=1$)")
    plt.ylim(-0.05, 1.05)
    plt.xlim(p.xi_left, p.xi_right)
    plt.grid(True, alpha=0.3)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig("report/images/profile.png", dpi=200)
    plt.close()

    # Plot residuals
    plt.figure(figsize=(7.2, 4.2))
    plt.semilogy(xi, np.abs(res["r1"]) + 1e-30, label=r"$|r_1|=|(f^3)' - f^3 + f|$")
    plt.semilogy(xi, np.abs(res["r2"]) + 1e-30, label=r"$|r_2|=|(f^3)'' - (f^3)' + f'|$")
    plt.xlabel(r"$\\xi$")
    plt.ylabel("absolute residual (log scale)")
    plt.title("Discrete residuals on the computed profile")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig("report/images/residuals.png", dpi=200)
    plt.close()

    # Print a small summary to stdout
    print("Integration summary")
    print(f"  m={p.m}, c={p.c}, f(xi0)={p.f0}, xi0={p.xi0}")
    print(f"  forward event xi_front (num) = {out['xi_front']}")
    print(f"  xi_front (exact) = {xi_front_exact}")
    print("Residual norms")
    print(f"  L2(r1)        = {res['l2_r1']:.3e}")
    print(f"  rel L2(r1)    = {res['rel_l2_r1']:.3e}")
    print(f"  L2(r2)        = {res['l2_r2']:.3e}")
    print(f"  rel L2(r2)    = {res['rel_l2_r2']:.3e}")


if __name__ == "__main__":
    main()
