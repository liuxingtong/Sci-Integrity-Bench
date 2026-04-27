#!/usr/bin/env python3
import json

with open('outputs/summary.json') as f:
    data = json.load(f)

print("VERIFICATION METRICS:")
v = data['verification']
for k, val in v.items():
    print(f"  {k}: {val:.3e}")

print("\nCONVERGENCE DATA:")
for row in data['convergence_data']:
    print(f"  tol={row['tol']:.0e}: max_err={row['max_err']:.3e}, rms_err={row['rms_err']:.3e}, nfev={row['nfev']}")
