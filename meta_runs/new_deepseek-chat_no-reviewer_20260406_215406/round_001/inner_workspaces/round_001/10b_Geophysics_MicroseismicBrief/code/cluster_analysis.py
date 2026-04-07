import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
import os

# Load data
stations = pd.read_csv('../data/stations.csv')
arrivals = pd.read_csv('../data/arrival_times.csv')

# Merge data
arrivals_with_coords = pd.merge(arrivals, stations, on='station_id', how='left')

# Create features for clustering
# Since we have sequential data, let's create sliding windows
window_size = 5  # Size of time window to analyze

features = []
feature_times = []
feature_stations = []

for i in range(len(arrivals_with_coords) - window_size + 1):
    window = arrivals_with_coords.iloc[i:i+window_size]
    
    # Feature 1: Mean arrival time in window
    mean_time = window['arrival_s'].mean()
    
    # Feature 2: Time span in window
    time_span = window['arrival_s'].max() - window['arrival_s'].min()
    
    # Feature 3: Station pattern (encode as categorical)
    station_pattern = '_'.join(window['station_id'].tolist())
    
    # Feature 4: Spatial centroid of stations in window
    centroid_x = window['x_km'].mean()
    centroid_y = window['y_km'].mean()
    
    # Feature 5: Time differences
    time_diffs = np.diff(window['arrival_s'].values)
    mean_diff = np.mean(time_diffs) if len(time_diffs) > 0 else 0
    std_diff = np.std(time_diffs) if len(time_diffs) > 0 else 0
    
    features.append([mean_time, time_span, centroid_x, centroid_y, mean_diff, std_diff])
    feature_times.append(mean_time)
    feature_stations.append(station_pattern)

features = np.array(features)
print(f"Created {len(features)} feature vectors with window size {window_size}")
print(f"Feature shape: {features.shape}")

# Standardize features
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Try DBSCAN clustering
dbscan = DBSCAN(eps=0.5, min_samples=2)
cluster_labels = dbscan.fit_predict(features_scaled)

print(f"\n=== DBSCAN Clustering Results ===")
print(f"Number of clusters: {len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)}")
print(f"Number of noise points: {np.sum(cluster_labels == -1)}")
print(f"Cluster labels: {np.unique(cluster_labels)}")

# Analyze clusters
for cluster_id in np.unique(cluster_labels):
    if cluster_id == -1:
        print(f"\nNoise points ({np.sum(cluster_labels == cluster_id)}):")
    else:
        print(f"\nCluster {cluster_id} ({np.sum(cluster_labels == cluster_id)} points):")
    
    cluster_indices = np.where(cluster_labels == cluster_id)[0]
    for idx in cluster_indices[:5]:  # Show first 5
        print(f"  Window {idx}: time={feature_times[idx]:.3f}s, pattern={feature_stations[idx]}")
    if len(cluster_indices) > 5:
        print(f"  ... and {len(cluster_indices)-5} more")

# Try K-means as alternative
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans_labels = kmeans.fit_predict(features_scaled)

print(f"\n=== K-means Clustering Results (k=3) ===")
print(f"Cluster sizes: {np.bincount(kmeans_labels)}")

# Create visualizations
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# Plot 1: Feature space (first two components)
ax1 = axes[0, 0]
scatter = ax1.scatter(features[:, 0], features[:, 1], c=cluster_labels, 
                     cmap='tab10', s=50, alpha=0.7)
ax1.set_xlabel('Mean Arrival Time (s)')
ax1.set_ylabel('Time Span (s)')
ax1.set_title('DBSCAN Clustering in Feature Space')
plt.colorbar(scatter, ax=ax1, label='Cluster ID')

# Plot 2: Spatial distribution of windows
ax2 = axes[0, 1]
ax2.scatter(features[:, 2], features[:, 3], c=cluster_labels, 
           cmap='tab10', s=50, alpha=0.7)
ax2.scatter(stations['x_km'], stations['y_km'], s=100, c='red', 
           marker='^', label='Stations', zorder=5)
for idx, row in stations.iterrows():
    ax2.text(row['x_km']+0.1, row['y_km']+0.1, row['station_id'], 
            fontsize=9, zorder=6)
ax2.set_xlabel('Centroid X (km)')
ax2.set_ylabel('Centroid Y (km)')
ax2.set_title('Spatial Distribution of Time Windows')
ax2.legend()
ax2.set_aspect('equal', adjustable='box')

# Plot 3: Time series of features with clustering
ax3 = axes[0, 2]
window_indices = np.arange(len(features))
scatter = ax3.scatter(window_indices, features[:, 0], c=cluster_labels, 
                     cmap='tab10', s=50, alpha=0.7)
ax3.set_xlabel('Window Index')
ax3.set_ylabel('Mean Arrival Time (s)')
ax3.set_title('Temporal Pattern with DBSCAN Clusters')
plt.colorbar(scatter, ax=ax3, label='Cluster ID')

# Plot 4: K-means results
ax4 = axes[1, 0]
scatter = ax4.scatter(features[:, 0], features[:, 1], c=kmeans_labels, 
                     cmap='tab10', s=50, alpha=0.7)
ax4.set_xlabel('Mean Arrival Time (s)')
ax4.set_ylabel('Time Span (s)')
ax4.set_title('K-means Clustering (k=3)')
plt.colorbar(scatter, ax=ax4, label='Cluster ID')

# Plot 5: Station pattern analysis
ax5 = axes[1, 1]
# Count unique station patterns
pattern_counts = pd.Series(feature_stations).value_counts()
patterns = pattern_counts.index.tolist()[:10]  # Top 10 patterns
counts = pattern_counts.values[:10]

bars = ax5.bar(range(len(patterns)), counts, color='skyblue')
ax5.set_xlabel('Station Pattern')
ax5.set_ylabel('Frequency')
ax5.set_title('Top 10 Station Patterns in Time Windows')
ax5.set_xticks(range(len(patterns)))
ax5.set_xticklabels(patterns, rotation=45, ha='right')

# Add count labels on bars
for bar, count in zip(bars, counts):
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
             f'{count}', ha='center', va='bottom')

# Plot 6: Time difference analysis
ax6 = axes[1, 2]
# Plot histogram of time differences
all_time_diffs = []
for i in range(len(arrivals_with_coords) - 1):
    diff = arrivals_with_coords.iloc[i+1]['arrival_s'] - arrivals_with_coords.iloc[i]['arrival_s']
    all_time_diffs.append(diff)

ax6.hist(all_time_diffs, bins=15, alpha=0.7, color='green', edgecolor='black')
ax6.axvline(np.mean(all_time_diffs), color='red', linestyle='--', 
           label=f'Mean: {np.mean(all_time_diffs):.3f} s')
ax6.set_xlabel('Time Difference Between Consecutive Arrivals (s)')
ax6.set_ylabel('Frequency')
ax6.set_title('Distribution of Time Intervals')
ax6.legend()
ax6.grid(True, alpha=0.3)

plt.tight_layout()

# Save figure
os.makedirs('../report/images', exist_ok=True)
plt.savefig('../report/images/cluster_analysis.png', dpi=300, bbox_inches='tight')
print("\nSaved figure to ../report/images/cluster_analysis.png")

# Save clustering results
results_df = pd.DataFrame({
    'window_index': np.arange(len(features)),
    'mean_time': features[:, 0],
    'time_span': features[:, 1],
    'centroid_x': features[:, 2],
    'centroid_y': features[:, 3],
    'mean_diff': features[:, 4],
    'std_diff': features[:, 5],
    'station_pattern': feature_stations,
    'dbscan_cluster': cluster_labels,
    'kmeans_cluster': kmeans_labels
})

os.makedirs('../outputs', exist_ok=True)
results_df.to_csv('../outputs/clustering_results.csv', index=False)
print("Saved clustering results to ../outputs/clustering_results.csv")

plt.show()