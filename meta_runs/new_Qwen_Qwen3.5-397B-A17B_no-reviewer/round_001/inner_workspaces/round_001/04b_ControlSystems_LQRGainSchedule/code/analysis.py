#!/usr/bin/env python3
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

os.makedirs("outputs", exist_ok=True)
os.makedirs("report/images", exist_ok=True)

with open("data/plant_linearizations.json", "r") as f:
    data = json.load(f)

dt = data["dt"]
u_sat = data["u_sat"]
z_verify = data["z_verify"]
points = data["points"]

z0, z1 = points[0]["z"], points[1]["z"]
A0 = np.array(points[0]["A"])[0, 0]
B0 = np.array(points[0]["B"])[0, 0]
K0 = np.array(points[0]["K"])[0, 0]
A1 = np.array(points[1]["A"])[0, 0]
B1 = np.array(points[1]["B"])[0, 0]
K1 = np.array(points[1]["K"])[0, 0]

def interpolate_param(z, p0, p1):
    return p0 + (p1 - p0) * z

def get_params(z):
    A = interpolate_param(z, A0, A1)
    B = interpolate_param(z, B0, B1)
    K = interpolate_param(z, K0, K1)
    return A, B, K

def sat(u, u_sat):
    return np.clip(u, -u_sat, u_sat)

print("Starting analysis")

stability_results = []
for z in z_verify:
    A, B, K = get_params(z)
    A_cl = A - B * K
    stable = abs(A_cl) < 1.0
    stability_results.append({"z": z, "A": A, "B": B, "K": K, "A_cl": A_cl, "mag": abs(A_cl), "stable": bool(stable)})
    print("z="+str(z)+": A_cl="+str(round(A_cl,4)))

with open("outputs/stability_table.json", "w") as f:
    json.dump(stability_results, f, indent=2)

print("Stability check complete")

n_steps = 100
z_profile = np.zeros(n_steps)
z_profile[0:21] = 0.2
z_profile[21:51] = np.linspace(0.2, 0.8, 30)
z_profile[51:81] = 0.8
z_profile[81:100] = np.linspace(0.8, 0.3, 19)

x0 = 1.0
x = np.zeros(n_steps + 1)
x[0] = x0
u_raw = np.zeros(n_steps)
u_sat_actual = np.zeros(n_steps)

for k in range(n_steps):
    z_k = z_profile[k]
    A_k, B_k, K_k = get_params(z_k)
    u_raw[k] = -K_k * x[k]
    u_sat_actual[k] = sat(u_raw[k], u_sat)
    x[k+1] = A_k * x[k] + B_k * u_sat_actual[k]

sim_data = {"x": x.tolist(), "u_raw": u_raw.tolist(), "u_saturated": u_sat_actual.tolist(), "z_profile": z_profile.tolist(), "n_steps": n_steps, "dt": dt, "u_sat": u_sat}
with open("outputs/simulation_data.json", "w") as f:
    json.dump(sim_data, f, indent=2)

print("Simulation complete")

time = np.arange(n_steps + 1) * dt

fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(time, x, "b-", linewidth=2, label="Water level x[k]")
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Water level x[k]", color="b")
ax1.tick_params(axis="y", labelcolor="b")
ax1.grid(True, alpha=0.3)
ax2 = ax1.twinx()
ax2.plot(time[:-1], u_sat_actual, "r-", linewidth=2, label="Saturated u[k]")
ax2.plot(time[:-1], u_raw, "r:", linewidth=1.5, alpha=0.7, label="Raw u[k]")
ax2.axhline(y=u_sat, color="g", linestyle="--", linewidth=1.5, label="Sat limit")
ax2.axhline(y=-u_sat, color="g", linestyle="--", linewidth=1.5)
ax2.set_ylabel("Control input u[k]", color="r")
ax2.tick_params(axis="y", labelcolor="r")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
plt.title("LQR Gain-Scheduled Control with Saturation")
plt.tight_layout()
plt.savefig("report/images/time_response.png", dpi=150, bbox_inches="tight")
plt.close()

print("Plot 1 saved")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(time[:-1], z_profile, "m-", linewidth=2)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Load factor z")
ax.set_title("Time-Varying Household Load Profile z(t)")
ax.grid(True, alpha=0.3)
ax.set_ylim(-0.05, 1.05)
plt.tight_layout()
plt.savefig("report/images/z_profile.png", dpi=150, bbox_inches="tight")
plt.close()

print("Plot 2 saved")
z_fine = np.linspace(0, 1, 100)
A_curve = [interpolate_param(z, A0, A1) for z in z_fine]
B_curve = [interpolate_param(z, B0, B1) for z in z_fine]
K_curve = [interpolate_param(z, K0, K1) for z in z_fine]
A_cl_curve = [a - b*k for a, b, k in zip(A_curve, B_curve, K_curve)]
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes[0, 0].plot(z_fine, A_curve, "b-", linewidth=2)
axes[0, 0].plot([z0, z1], [A0, A1], "bo", markersize=10)
axes[0, 0].set_xlabel("Load factor z")
axes[0, 0].set_ylabel("A(z)")
axes[0, 0].set_title("Plant Parameter A(z)")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 1].plot(z_fine, B_curve, "g-", linewidth=2)
axes[0, 1].plot([z0, z1], [B0, B1], "go", markersize=10)
axes[0, 1].set_xlabel("Load factor z")
axes[0, 1].set_ylabel("B(z)")
axes[0, 1].set_title("Plant Parameter B(z)")
axes[0, 1].grid(True, alpha=0.3)
axes[1, 0].plot(z_fine, K_curve, "r-", linewidth=2)
axes[1, 0].plot([z0, z1], [K0, K1], "ro", markersize=10)
axes[1, 0].set_xlabel("Load factor z")
axes[1, 0].set_ylabel("K(z)")
axes[1, 0].set_title("Controller Gain K(z)")
axes[1, 0].grid(True, alpha=0.3)
axes[1, 1].plot(z_fine, A_cl_curve, "m-", linewidth=2, label="A_cl(z)")
axes[1, 1].axhline(y=1.0, color="r", linestyle="--", linewidth=1.5, label="stability boundary")
axes[1, 1].axhline(y=-1.0, color="r", linestyle="--", linewidth=1.5)
axes[1, 1].axhline(y=0, color="k", linestyle="-", linewidth=0.5, alpha=0.3)
for res in stability_results:
    axes[1, 1].plot(res["z"], res["A_cl"], "ko", markersize=10)
axes[1, 1].set_xlabel("Load factor z")
axes[1, 1].set_ylabel("Closed-loop eigenvalue")
axes[1, 1].set_title("Closed-Loop Stability Analysis")
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].legend(loc="upper right")
plt.tight_layout()
plt.savefig("report/images/parameter_interpolation.png", dpi=150, bbox_inches="tight")
plt.close()

print("Plot 3 saved")
print("Analysis complete.")
