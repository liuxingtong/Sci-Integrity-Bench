from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def main():
    out_npz = Path("outputs/tw_solution.npz")
    if not out_npz.exists():
        raise FileNotFoundError("Run porous_medium_traveling_wave.py first to generate outputs/tw_solution.npz")

    data = np.load(out_npz)
    xi = data["xi"]
    f = data["f"]
    f_ref = data["f_ref"]
    err = data["err"]
    R = data["residual"]
    fp_ivp = data["fp_ivp"]

    params = json.loads(str(data["params"]))
    m = float(params["m"])
    c = float(params["c"])

    img_dir = Path("report/images")
    img_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: Profile vs analytic
    plt.figure(figsize=(7.2, 4.2))
    plt.plot(xi, f, lw=2.0, label="numerical (2nd-order ODE)")
    plt.plot(xi, f_ref, lw=2.0, ls="--", label="analytic (K=0)")
    plt.xlabel(r"$\xi$")
    plt.ylabel(r"$f(\xi)$")
    plt.title(f"Porous-medium traveling wave (m={m:g}, c={c:g})")
    plt.grid(True, alpha=0.3)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(img_dir / "f_profile.png", dpi=200)
    plt.close()

    # Figure 2: Absolute error vs analytic
    plt.figure(figsize=(7.2, 4.2))
    plt.plot(xi, np.abs(err), lw=1.8)
    plt.yscale("log")
    plt.xlabel(r"$\xi$")
    plt.ylabel(r"$|f - f_{\mathrm{ref}}|$")
    plt.title("Pointwise error vs analytic reference")
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(img_dir / "error_vs_analytic.png", dpi=200)
    plt.close()

    # Figure 3: ODE residual
    plt.figure(figsize=(7.2, 4.2))
    plt.plot(xi, np.abs(R), lw=1.8)
    plt.yscale("log")
    plt.xlabel(r"$\xi$")
    plt.ylabel(r"$|(f^m)'' + c f'|$")
    plt.title("Discrete residual of the traveling-wave ODE")
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(img_dir / "ode_residual.png", dpi=200)
    plt.close()

    # Figure 4: Phase-plane: f' vs f
    # Reference first-order slope from integrated relation: f' = -(c/m) f^{2-m}
    fpos = np.maximum(f, 1e-16)
    fp_ref = -(c / m) * (fpos ** (2.0 - m))

    plt.figure(figsize=(5.2, 4.6))
    plt.plot(f, fp_ivp, lw=2.0, label="numerical")
    plt.plot(f, fp_ref, lw=2.0, ls="--", label=r"ref: $-(c/m)f^{2-m}$")
    plt.xlabel(r"$f$")
    plt.ylabel(r"$f'$")
    plt.title("Phase-plane check")
    plt.grid(True, alpha=0.3)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(img_dir / "phase_plane.png", dpi=200)
    plt.close()


if __name__ == "__main__":
    main()
