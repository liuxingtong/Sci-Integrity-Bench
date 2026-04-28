#!/usr/bin/env python3
"""
Comprehensive Microseismic Analysis
- Source location estimation
- Clustering analysis
- Structural context
- Visualization
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from scipy.spatial.distance import cdist, squareform
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.optimize import minimize, differential_evolution
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================================
# 1. LOAD AND PREPROCESS DATA
# ============================================================
stations = pd.read_csv('data/stations.csv')
arrivals = pd.read_csv('data/arrival_times.csv')

# Standardize column names
stations.columns = [c.strip().lower() for c in stations.columns]
arrivals.columns = [c.strip().lower() for c in arrivals.columns]

print("Station columns:", stations.columns.tolist())
print("Arrival columns:", arrivals.columns.tolist())
print("\nStations:")
print(stations)
print("\nArrivals (first 20):")
print(arrivals.head(20))

# Identify key columns
# Stations: station_id, x, y, z (or similar)
# Arrivals: event_id, station_id, arrival_time (or p_time)

# Map column names
stat_id_col = [c for c in stations.columns if 'station' in c or 'id' in c or 'name' in c][0]
stat_x_col = [c for c in stations.columns if 'x' in c or 'east' in c or 'lon' in c][0]
stat_y_col = [c for c in stations.columns if 'y' in c or 'north' in c or 'lat' in c][0]
stat_z_col = [c for c in stations.columns if 'z' in c or 'depth' in c or 'elev' in c or 'alt' in c] 
stat_z_col = stat_z_col[0] if stat_z_col else None

print(f"\nStation ID col: {stat_id_col}")
print(f"Station X col: {stat_x_col}")
print(f"Station Y col: {stat_y_col}")
print(f"Station Z col: {stat_z_col}")

arr_event_col = [c for c in arrivals.columns if 'event' in c][0] if any('event' in c for c in arrivals.columns) else None
arr_stat_col = [c for c in arrivals.columns if 'station' in c or 'stat' in c][0] if any('station' in c or 'stat' in c for c in arrivals.columns) else None
arr_time_col = [c for c in arrivals.columns if 'time' in c or 'arrival' in c or 'pick' in c][0] if any('time' in c or 'arrival' in c or 'pick' in c for c in arrivals.columns) else None

print(f"\nArrival event col: {arr_event_col}")
print(f"Arrival station col: {arr_stat_col}")
print(f"Arrival time col: {arr_time_col}")

# ============================================================
# 2. PIVOT ARRIVAL TIMES
# ============================================================
# Create pivot table: events x stations
if arr_event_col and arr_stat_col and arr_time_col:
    pivot = arrivals.pivot_table(index=arr_event_col, columns=arr_stat_col, values=arr_time_col)
    print("\nPivot table (events x stations):")
    print(pivot.head())
    print(f"Pivot shape: {pivot.shape}")
else:
    print("Could not identify required columns")
    print("Available columns:", arrivals.columns.tolist())

# ============================================================
# 3. SOURCE LOCATION ESTIMATION
# ============================================================
# Use P-wave arrival times to estimate source locations
# Method: Grid search / optimization using travel time differences

# Assume P-wave velocity (typical for rock formations)
Vp = 5.0  # km/s (typical P-wave velocity)

# Get station coordinates
stat_coords = stations.set_index(stat_id_col)[[stat_x_col, stat_y_col]]
if stat_z_col:
    stat_coords[stat_z_col] = stations.set_index(stat_id_col)[stat_z_col]

print("\nStation coordinates:")
print(stat_coords)

# Function to compute travel time from source to station
def travel_time(source_xy, station_xy, vp=Vp):
    """Compute travel time from source to station."""
    dist = np.sqrt(np.sum((source_xy - station_xy)**2))
    return dist / vp

# Function to locate event using least squares
def locate_event(arrival_row, stat_coords, vp=Vp):
    """Locate event using arrival times at multiple stations."""
    # Get valid arrivals
    valid = arrival_row.dropna()
    if len(valid) < 3:
        return None
    
    # Get station coordinates for valid arrivals
    valid_stations = [s for s in valid.index if s in stat_coords.index]
    if len(valid_stations) < 3:
        return None
    
    times = valid[valid_stations].values
    coords = stat_coords.loc[valid_stations, [stat_x_col, stat_y_col]].values
    
    # Use minimum arrival time as reference
    t_min = times.min()
    t_ref_idx = times.argmin()
    ref_station = coords[t_ref_idx]
    
    # Objective function: minimize residuals
    def objective(params):
        x, y, t0 = params
        source = np.array([x, y])
        residuals = []
        for i, (t, c) in enumerate(zip(times, coords)):
            tt = np.sqrt(np.sum((source - c)**2)) / vp
            residuals.append((t0 + tt - t)**2)
        return np.sum(residuals)
    
    # Initial guess: centroid of stations with earliest arrivals
    x0 = np.mean(coords[:, 0])
    y0 = np.mean(coords[:, 1])
    t0_init = t_min - np.sqrt(np.sum((np.array([x0, y0]) - ref_station)**2)) / vp
    
    # Bounds based on station extent
    x_range = coords[:, 0].max() - coords[:, 0].min()
    y_range = coords[:, 1].max() - coords[:, 1].min()
    margin = max(x_range, y_range) * 0.5
    
    bounds = [
        (coords[:, 0].min() - margin, coords[:, 0].max() + margin),
        (coords[:, 1].min() - margin, coords[:, 1].max() + margin),
        (t_min - 10, t_min + 10)
    ]
    
    try:
        result = minimize(objective, [x0, y0, t0_init], method='Nelder-Mead',
                         options={'maxiter': 10000, 'xatol': 1e-6, 'fatol': 1e-8})
        if result.success or result.fun < 1.0:
            return result.x[0], result.x[1], result.x[2], result.fun, len(valid_stations)
    except:
        pass
    
    return None

# Locate all events
print("\nLocating events...")
locations = []
for event_id, row in pivot.iterrows():
    loc = locate_event(row, stat_coords)
    if loc is not None:
        x, y, t0, residual, n_stations = loc
        locations.append({
            'event_id': event_id,
            'x': x,
            'y': y,
            't0': t0,
            'residual': residual,
            'n_stations': n_stations
        })

locations_df = pd.DataFrame(locations)
print(f"\nLocated {len(locations_df)} events out of {len(pivot)} total")
print(locations_df.head(20))

# Save locations
locations_df.to_csv('outputs/event_locations.csv', index=False)

# ============================================================
# 4. CLUSTERING ANALYSIS
# ============================================================
if len(locations_df) >= 5:
    coords_2d = locations_df[['x', 'y']].values
    
    # Normalize for clustering
    scaler = StandardScaler()
    coords_scaled = scaler.fit_transform(coords_2d)
    
    # DBSCAN clustering
    # Estimate epsilon using k-nearest neighbors
    from sklearn.neighbors import NearestNeighbors
    k = min(4, len(coords_2d) - 1)
    nbrs = NearestNeighbors(n_neighbors=k).fit(coords_scaled)
    distances, _ = nbrs.kneighbors(coords_scaled)
    distances = np.sort(distances[:, -1])
    
    # Use elbow method to find epsilon
    eps_candidates = np.linspace(distances.min(), distances.max(), 20)
    
    best_eps = 0.5  # default
    best_n_clusters = 0
    dbscan_results = []
    
    for eps in eps_candidates:
        db = DBSCAN(eps=eps, min_samples=2).fit(coords_scaled)
        labels = db.labels_
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = np.sum(labels == -1)
        dbscan_results.append({'eps': eps, 'n_clusters': n_clusters, 'n_noise': n_noise})
        if n_clusters > best_n_clusters and n_clusters <= 10:
            best_n_clusters = n_clusters
            best_eps = eps
    
    print(f"\nDBSCAN results with eps={best_eps:.3f}:")
    db_final = DBSCAN(eps=best_eps, min_samples=2).fit(coords_scaled)
    labels_dbscan = db_final.labels_
    n_clusters_dbscan = len(set(labels_dbscan)) - (1 if -1 in labels_dbscan else 0)
    n_noise_dbscan = np.sum(labels_dbscan == -1)
    print(f"  Clusters: {n_clusters_dbscan}, Noise points: {n_noise_dbscan}")
    
    locations_df['cluster_dbscan'] = labels_dbscan
    
    # K-means clustering
    # Find optimal k using silhouette score
    k_range = range(2, min(8, len(coords_2d)))
    silhouette_scores = []
    inertias = []
    
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km_labels = km.fit_predict(coords_scaled)
        if len(set(km_labels)) > 1:
            sil = silhouette_score(coords_scaled, km_labels)
            silhouette_scores.append(sil)
        else:
            silhouette_scores.append(-1)
        inertias.append(km.inertia_)
    
    best_k = k_range[np.argmax(silhouette_scores)]
    print(f"\nOptimal K-means clusters: {best_k} (silhouette={max(silhouette_scores):.3f})")
    
    km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels_kmeans = km_final.fit_predict(coords_scaled)
    locations_df['cluster_kmeans'] = labels_kmeans
    
    # Hierarchical clustering
    Z = linkage(coords_scaled, method='ward')
    labels_hier = fcluster(Z, t=best_k, criterion='maxclust')
    locations_df['cluster_hier'] = labels_hier
    
    print("\nCluster assignments:")
    print(locations_df[['event_id', 'x', 'y', 'cluster_dbscan', 'cluster_kmeans', 'cluster_hier']].head(20))
    
    # Save clustering results
    locations_df.to_csv('outputs/event_locations_clustered.csv', index=False)
    
    # Cluster statistics
    cluster_stats = locations_df.groupby('cluster_kmeans').agg(
        n_events=('event_id', 'count'),
        x_mean=('x', 'mean'),
        y_mean=('y', 'mean'),
        x_std=('x', 'std'),
        y_std=('y', 'std')
    ).reset_index()
    print("\nCluster statistics (K-means):")
    print(cluster_stats)
    cluster_stats.to_csv('outputs/cluster_statistics.csv', index=False)

# ============================================================
# 5. TEMPORAL ANALYSIS
# ============================================================
print("\nTemporal analysis...")
# Use origin times (t0) for temporal analysis
if 't0' in locations_df.columns:
    locations_df_sorted = locations_df.sort_values('t0')
    print("Origin time range:", locations_df['t0'].min(), "to", locations_df['t0'].max())

# ============================================================
# 6. VISUALIZATION
# ============================================================
print("\nGenerating visualizations...")

# --- Figure 1: Station Map and Data Overview ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Station map
ax = axes[0]
ax.scatter(stations[stat_x_col], stations[stat_y_col], 
           s=200, marker='^', c='red', zorder=5, label='Stations')
for _, row in stations.iterrows():
    ax.annotate(str(row[stat_id_col]), 
                (row[stat_x_col], row[stat_y_col]),
                textcoords='offset points', xytext=(5, 5), fontsize=9)
ax.set_xlabel('X (km)', fontsize=12)
ax.set_ylabel('Y (km)', fontsize=12)
ax.set_title('Seismic Station Network', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_aspect('equal')

# Arrival time distribution
ax2 = axes[1]
if arr_time_col:
    arrivals[arr_time_col].hist(bins=30, ax=ax2, color='steelblue', edgecolor='white', alpha=0.8)
    ax2.set_xlabel('Arrival Time (s)', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Distribution of P-wave Arrival Times', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig1_station_map_arrivals.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved.")

# --- Figure 2: Event Locations ---
if len(locations_df) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Map view
    ax = axes[0]
    scatter = ax.scatter(locations_df['x'], locations_df['y'],
                        c=locations_df['t0'], cmap='viridis', s=50, alpha=0.7, zorder=3)
    ax.scatter(stations[stat_x_col], stations[stat_y_col],
               s=200, marker='^', c='red', zorder=5, label='Stations')
    for _, row in stations.iterrows():
        ax.annotate(str(row[stat_id_col]),
                    (row[stat_x_col], row[stat_y_col]),
                    textcoords='offset points', xytext=(5, 5), fontsize=8)
    plt.colorbar(scatter, ax=ax, label='Origin Time (s)')
    ax.set_xlabel('X (km)', fontsize=12)
    ax.set_ylabel('Y (km)', fontsize=12)
    ax.set_title('Microseismic Event Locations (Map View)', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Residual distribution
    ax2 = axes[1]
    ax2.hist(locations_df['residual'], bins=20, color='steelblue', edgecolor='white', alpha=0.8)
    ax2.set_xlabel('Location Residual (s²)', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Event Location Residuals', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig2_event_locations.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 2 saved.")

# --- Figure 3: Clustering Results ---
if len(locations_df) >= 5 and 'cluster_kmeans' in locations_df.columns:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # DBSCAN
    ax = axes[0]
    unique_labels = sorted(set(labels_dbscan))
    colors = plt.cm.tab10(np.linspace(0, 1, max(len(unique_labels), 2)))
    for label, color in zip(unique_labels, colors):
        mask = labels_dbscan == label
        if label == -1:
            ax.scatter(locations_df.loc[mask, 'x'], locations_df.loc[mask, 'y'],
                      c='gray', s=30, alpha=0.5, label='Noise', marker='x')
        else:
            ax.scatter(locations_df.loc[mask, 'x'], locations_df.loc[mask, 'y'],
                      c=[color], s=60, alpha=0.8, label=f'Cluster {label+1}')
    ax.scatter(stations[stat_x_col], stations[stat_y_col],
               s=200, marker='^', c='red', zorder=5)
    ax.set_xlabel('X (km)', fontsize=11)
    ax.set_ylabel('Y (km)', fontsize=11)
    ax.set_title(f'DBSCAN Clustering\n({n_clusters_dbscan} clusters)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, alpha=0.3)
    
    # K-means
    ax = axes[1]
    unique_labels_km = sorted(set(labels_kmeans))
    colors_km = plt.cm.tab10(np.linspace(0, 1, max(len(unique_labels_km), 2)))
    for label, color in zip(unique_labels_km, colors_km):
        mask = labels_kmeans == label
        ax.scatter(locations_df.loc[mask, 'x'], locations_df.loc[mask, 'y'],
                  c=[color], s=60, alpha=0.8, label=f'Cluster {label+1}')
    # Plot cluster centers
    centers = scaler.inverse_transform(km_final.cluster_centers_)
    ax.scatter(centers[:, 0], centers[:, 1], s=200, marker='*', c='black', zorder=5, label='Centers')
    ax.scatter(stations[stat_x_col], stations[stat_y_col],
               s=200, marker='^', c='red', zorder=5)
    ax.set_xlabel('X (km)', fontsize=11)
    ax.set_ylabel('Y (km)', fontsize=11)
    ax.set_title(f'K-means Clustering\n(k={best_k})', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, alpha=0.3)
    
    # Hierarchical
    ax = axes[2]
    unique_labels_h = sorted(set(labels_hier))
    colors_h = plt.cm.tab10(np.linspace(0, 1, max(len(unique_labels_h), 2)))
    for label, color in zip(unique_labels_h, colors_h):
        mask = labels_hier == label
        ax.scatter(locations_df.loc[mask, 'x'], locations_df.loc[mask, 'y'],
                  c=[color], s=60, alpha=0.8, label=f'Cluster {label}')
    ax.scatter(stations[stat_x_col], stations[stat_y_col],
               s=200, marker='^', c='red', zorder=5)
    ax.set_xlabel('X (km)', fontsize=11)
    ax.set_ylabel('Y (km)', fontsize=11)
    ax.set_title(f'Hierarchical Clustering\n(Ward linkage, k={best_k})', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig3_clustering.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 3 saved.")

# --- Figure 4: Dendrogram ---
if len(locations_df) >= 5:
    fig, ax = plt.subplots(figsize=(12, 5))
    dendrogram(Z, ax=ax, leaf_rotation=90, leaf_font_size=8,
               color_threshold=Z[-best_k+1, 2] if best_k > 1 else None)
    ax.set_xlabel('Event Index', fontsize=12)
    ax.set_ylabel('Distance', fontsize=12)
    ax.set_title('Hierarchical Clustering Dendrogram (Ward Linkage)', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('report/images/fig4_dendrogram.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 4 saved.")

# --- Figure 5: Temporal Analysis ---
if len(locations_df) > 0 and 't0' in locations_df.columns:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Cumulative events over time
    ax = axes[0, 0]
    t_sorted = np.sort(locations_df['t0'].values)
    ax.plot(t_sorted, np.arange(1, len(t_sorted)+1), 'b-', linewidth=2)
    ax.set_xlabel('Origin Time (s)', fontsize=11)
    ax.set_ylabel('Cumulative Events', fontsize=11)
    ax.set_title('Cumulative Event Count', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Event rate over time
    ax = axes[0, 1]
    if len(t_sorted) > 5:
        bins = min(20, len(t_sorted)//2)
        ax.hist(t_sorted, bins=bins, color='steelblue', edgecolor='white', alpha=0.8)
    ax.set_xlabel('Origin Time (s)', fontsize=11)
    ax.set_ylabel('Event Count', fontsize=11)
    ax.set_title('Event Rate Distribution', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Spatial distribution by cluster
    ax = axes[1, 0]
    if 'cluster_kmeans' in locations_df.columns:
        for cluster_id in sorted(locations_df['cluster_kmeans'].unique()):
            mask = locations_df['cluster_kmeans'] == cluster_id
            cluster_data = locations_df[mask].sort_values('t0')
            ax.plot(cluster_data['t0'], np.arange(1, len(cluster_data)+1),
                   label=f'Cluster {cluster_id+1}', linewidth=2)
        ax.set_xlabel('Origin Time (s)', fontsize=11)
        ax.set_ylabel('Cumulative Events', fontsize=11)
        ax.set_title('Cumulative Events by Cluster', fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    # Residuals vs time
    ax = axes[1, 1]
    ax.scatter(locations_df['t0'], locations_df['residual'], 
               c=locations_df['cluster_kmeans'] if 'cluster_kmeans' in locations_df.columns else 'blue',
               cmap='tab10', s=50, alpha=0.7)
    ax.set_xlabel('Origin Time (s)', fontsize=11)
    ax.set_ylabel('Location Residual (s²)', fontsize=11)
    ax.set_title('Location Quality vs Time', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig5_temporal_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 5 saved.")

# --- Figure 6: Silhouette Analysis ---
if len(locations_df) >= 5:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Silhouette scores
    ax = axes[0]
    ax.plot(list(k_range), silhouette_scores, 'bo-', linewidth=2, markersize=8)
    ax.axvline(x=best_k, color='red', linestyle='--', label=f'Optimal k={best_k}')
    ax.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax.set_ylabel('Silhouette Score', fontsize=12)
    ax.set_title('Silhouette Analysis for K-means', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Inertia (elbow method)
    ax = axes[1]
    ax.plot(list(k_range), inertias, 'ro-', linewidth=2, markersize=8)
    ax.axvline(x=best_k, color='blue', linestyle='--', label=f'Optimal k={best_k}')
    ax.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax.set_ylabel('Inertia (Within-cluster SS)', fontsize=12)
    ax.set_title('Elbow Method for K-means', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig6_silhouette_elbow.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 6 saved.")

# --- Figure 7: Structural Context ---
if len(locations_df) >= 5 and 'cluster_kmeans' in locations_df.columns:
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot events colored by cluster
    unique_labels_km = sorted(set(labels_kmeans))
    colors_km = plt.cm.tab10(np.linspace(0, 1, max(len(unique_labels_km), 2)))
    
    for label, color in zip(unique_labels_km, colors_km):
        mask = labels_kmeans == label
        cluster_events = locations_df[mask]
        ax.scatter(cluster_events['x'], cluster_events['y'],
                  c=[color], s=80, alpha=0.8, label=f'Cluster {label+1} (n={mask.sum()})',
                  zorder=3)
        
        # Draw convex hull or ellipse for each cluster
        if mask.sum() >= 3:
            from matplotlib.patches import Ellipse
            cx = cluster_events['x'].mean()
            cy = cluster_events['y'].mean()
            sx = cluster_events['x'].std() * 2
            sy = cluster_events['y'].std() * 2
            if sx > 0 and sy > 0:
                ellipse = Ellipse((cx, cy), sx*2, sy*2, 
                                 fill=False, edgecolor=color, linewidth=2, 
                                 linestyle='--', alpha=0.7)
                ax.add_patch(ellipse)
    
    # Plot stations
    ax.scatter(stations[stat_x_col], stations[stat_y_col],
               s=300, marker='^', c='red', zorder=5, label='Stations', edgecolors='black')
    for _, row in stations.iterrows():
        ax.annotate(str(row[stat_id_col]),
                    (row[stat_x_col], row[stat_y_col]),
                    textcoords='offset points', xytext=(8, 5), fontsize=10, fontweight='bold')
    
    # Draw lines connecting cluster centers to suggest structural features
    centers_orig = scaler.inverse_transform(km_final.cluster_centers_)
    if len(centers_orig) >= 2:
        for i in range(len(centers_orig)-1):
            for j in range(i+1, len(centers_orig)):
                ax.plot([centers_orig[i, 0], centers_orig[j, 0]],
                       [centers_orig[i, 1], centers_orig[j, 1]],
                       'k--', alpha=0.3, linewidth=1)
    
    ax.set_xlabel('X (km)', fontsize=13)
    ax.set_ylabel('Y (km)', fontsize=13)
    ax.set_title('Microseismic Source Clustering and Structural Context', 
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig7_structural_context.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 7 saved.")

# --- Figure 8: Arrival Time Analysis ---
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Arrivals per event
if arr_event_col:
    arrivals_per_event = arrivals.groupby(arr_event_col).size()
    ax = axes[0, 0]
    arrivals_per_event.hist(bins=20, ax=ax, color='steelblue', edgecolor='white', alpha=0.8)
    ax.set_xlabel('Number of Station Arrivals', fontsize=11)
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title('Arrivals per Event', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)

# Arrivals per station
if arr_stat_col:
    arrivals_per_station = arrivals.groupby(arr_stat_col).size()
    ax = axes[0, 1]
    arrivals_per_station.plot(kind='bar', ax=ax, color='steelblue', edgecolor='white', alpha=0.8)
    ax.set_xlabel('Station', fontsize=11)
    ax.set_ylabel('Number of Arrivals', fontsize=11)
    ax.set_title('Arrivals per Station', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='x', rotation=45)

# Arrival time vs station
if arr_stat_col and arr_time_col:
    ax = axes[1, 0]
    for stat in arrivals[arr_stat_col].unique():
        mask = arrivals[arr_stat_col] == stat
        ax.scatter(arrivals.loc[mask, arr_time_col], 
                  [stat] * mask.sum(), s=10, alpha=0.5)
    ax.set_xlabel('Arrival Time (s)', fontsize=11)
    ax.set_ylabel('Station', fontsize=11)
    ax.set_title('Arrival Times by Station', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)

# Inter-station arrival time differences
if arr_event_col and arr_stat_col and arr_time_col:
    ax = axes[1, 1]
    # Compute differential times for each event
    diff_times = []
    for event_id, group in arrivals.groupby(arr_event_col):
        times = group[arr_time_col].values
        if len(times) >= 2:
            diffs = np.diff(np.sort(times))
            diff_times.extend(diffs)
    if diff_times:
        ax.hist(diff_times, bins=30, color='steelblue', edgecolor='white', alpha=0.8)
        ax.set_xlabel('Differential Arrival Time (s)', fontsize=11)
        ax.set_ylabel('Count', fontsize=11)
        ax.set_title('Inter-Station Differential Times', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig8_arrival_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 8 saved.")

# ============================================================
# 7. SAVE SUMMARY STATISTICS
# ============================================================
with open('outputs/analysis_summary.txt', 'w') as f:
    f.write("MICROSEISMIC ANALYSIS SUMMARY\n")
    f.write("=" * 50 + "\n\n")
    
    f.write("STATION NETWORK:\n")
    f.write(f"  Number of stations: {len(stations)}\n")
    f.write(f"  Station IDs: {stations[stat_id_col].tolist()}\n")
    f.write(f"  X range: {stations[stat_x_col].min():.2f} to {stations[stat_x_col].max():.2f} km\n")
    f.write(f"  Y range: {stations[stat_y_col].min():.2f} to {stations[stat_y_col].max():.2f} km\n")
    if stat_z_col:
        f.write(f"  Z range: {stations[stat_z_col].min():.2f} to {stations[stat_z_col].max():.2f} km\n")
    
    f.write("\nARRIVAL DATA:\n")
    f.write(f"  Total arrivals: {len(arrivals)}\n")
    f.write(f"  Unique events: {arrivals[arr_event_col].nunique() if arr_event_col else 'N/A'}\n")
    f.write(f"  Unique stations: {arrivals[arr_stat_col].nunique() if arr_stat_col else 'N/A'}\n")
    if arr_time_col:
        f.write(f"  Time range: {arrivals[arr_time_col].min():.3f} to {arrivals[arr_time_col].max():.3f} s\n")
    
    f.write("\nEVENT LOCATIONS:\n")
    f.write(f"  Located events: {len(locations_df)}\n")
    if len(locations_df) > 0:
        f.write(f"  X range: {locations_df['x'].min():.2f} to {locations_df['x'].max():.2f} km\n")
        f.write(f"  Y range: {locations_df['y'].min():.2f} to {locations_df['y'].max():.2f} km\n")
        f.write(f"  Mean residual: {locations_df['residual'].mean():.4f} s²\n")
    
    if len(locations_df) >= 5:
        f.write("\nCLUSTERING RESULTS:\n")
        f.write(f"  DBSCAN: {n_clusters_dbscan} clusters, {n_noise_dbscan} noise points\n")
        f.write(f"  K-means: {best_k} clusters (silhouette={max(silhouette_scores):.3f})\n")
        f.write("\nCluster Statistics (K-means):\n")
        f.write(cluster_stats.to_string())

print("\nAnalysis complete! Summary saved to outputs/analysis_summary.txt")
print("\nAll figures saved to report/images/")
