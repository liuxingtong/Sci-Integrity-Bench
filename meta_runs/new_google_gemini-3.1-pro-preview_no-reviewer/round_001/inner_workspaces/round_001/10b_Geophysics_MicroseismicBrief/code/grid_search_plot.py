import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

events = [
    arrivals.iloc[0:5],
    arrivals.iloc[5:10],
    arrivals.iloc[10:12]
]

# Let's use the average relative arrival times of Event 0 and Event 1
rel_arrivals = []
for st in ['S0', 'S1', 'S2', 'S3', 'S4']:
    t0 = events[0][events[0]['station_id'] == st]['arrival_s'].values[0] - events[0][events[0]['station_id'] == 'S0']['arrival_s'].values[0]
    t1 = events[1][events[1]['station_id'] == st]['arrival_s'].values[0] - events[1][events[1]['station_id'] == 'S0']['arrival_s'].values[0]
    rel_arrivals.append({'station_id': st, 'rel_t': (t0 + t1) / 2})

rel_df = pd.DataFrame(rel_arrivals)
print(rel_df)

# Grid search
x = np.linspace(-5, 10, 151)
y = np.linspace(-5, 15, 201)
z = np.linspace(0, 10, 101)
v = np.linspace(2.0, 6.0, 41)

X, Y, Z, V = np.meshgrid(x, y, z, v, indexing='ij')

t0_estimates = []
for _, row in rel_df.iterrows():
    st = stations[stations['station_id'] == row['station_id']].iloc[0]
    tt = np.sqrt((X - st['x_km'])**2 + (Y - st['y_km'])**2 + (Z - st['z_km'])**2) / V
    t0_est = row['rel_t'] - tt
    t0_estimates.append(t0_est)

t0_estimates = np.array(t0_estimates)
variance = np.var(t0_estimates, axis=0)

min_idx = np.unravel_index(np.argmin(variance), variance.shape)

best_x = x[min_idx[0]]
best_y = y[min_idx[1]]
best_z = z[min_idx[2]]
best_v = v[min_idx[3]]
best_var = variance[min_idx]

print(f"Best location:")
print(f"  x: {best_x:.3f} km")
print(f"  y: {best_y:.3f} km")
print(f"  z: {best_z:.3f} km")
print(f"  v: {best_v:.3f} km/s")
print(f"  variance: {best_var:.6f}")

# Plot slices
plt.figure(figsize=(12, 4))

plt.subplot(131)
plt.imshow(variance[:, :, min_idx[2], min_idx[3]].T, extent=[x[0], x[-1], y[0], y[-1]], origin='lower', cmap='viridis_r', vmax=best_var*5)
plt.plot(best_x, best_y, 'r*', markersize=10)
plt.scatter(stations['x_km'], stations['y_km'], c='w', marker='^', edgecolors='k')
plt.xlabel('X (km)')
plt.ylabel('Y (km)')
plt.title('XY slice')

plt.subplot(132)
plt.imshow(variance[:, min_idx[1], :, min_idx[3]].T, extent=[x[0], x[-1], z[0], z[-1]], origin='lower', cmap='viridis_r', vmax=best_var*5)
plt.plot(best_x, best_z, 'r*', markersize=10)
plt.xlabel('X (km)')
plt.ylabel('Z (km)')
plt.title('XZ slice')
plt.gca().invert_yaxis()

plt.subplot(133)
plt.imshow(variance[min_idx[0], min_idx[1], :, :].T, extent=[z[0], z[-1], v[0], v[-1]], origin='lower', cmap='viridis_r', vmax=best_var*5)
plt.plot(best_z, best_v, 'r*', markersize=10)
plt.xlabel('Z (km)')
plt.ylabel('V (km/s)')
plt.title('ZV slice')

plt.tight_layout()
plt.savefig('outputs/grid_search.png')
