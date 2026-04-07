import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import os

# Read the data
df = pd.read_csv("../outputs/calibrated_ages.csv")
print("Data loaded for stratigraphic analysis")

# Create a Harris matrix visualization
# For simplicity, we'll assume layers are sequential (L1 above L2 above L3, etc.)
# But we know from ages that this might not be chronologically consistent

plt.figure(figsize=(12, 10))

# Create a directed graph for stratigraphic relationships
G = nx.DiGraph()

# Add nodes (samples)
for _, row in df.iterrows():
    node_id = row['artifact_id']
    G.add_node(node_id, 
               age=row['calibrated_age_BP'],
               unit=row['stratigraphic_unit'],
               layer=row['layer'] if not pd.isna(row['layer']) else None)

# Add edges based on layer numbers (lower number = higher/younger layer)
# Only for Trench 3 which has clear layer numbering
trench3_df = df[df['trench'] == '3'].copy()
trench3_df = trench3_df[trench3_df['layer'].notna()]
trench3_df = trench3_df.sort_values('layer')

if len(trench3_df) > 1:
    for i in range(len(trench3_df) - 1):
        upper = trench3_df.iloc[i]['artifact_id']
        lower = trench3_df.iloc[i + 1]['artifact_id']
        G.add_edge(upper, lower, relationship='stratigraphically above')

# Position nodes based on age (x) and layer/trench (y)
pos = {}
for _, row in df.iterrows():
    node_id = row['artifact_id']
    
    # X position based on age (log scale for better visualization of wide range)
    x_pos = np.log10(row['calibrated_age_BP'] + 1)
    
    # Y position based on trench and layer
    if row['trench'] == '2':
        y_pos = 3  # Trench 2 at top
    elif row['trench'] == '3':
        # Use layer for y-position within Trench 3
        y_pos = 2 - (row['layer'] / 10 if not pd.isna(row['layer']) else 0)
    elif row['trench'] == '4':
        y_pos = 1  # Trench 4 at bottom
    else:
        y_pos = 0
    
    pos[node_id] = (x_pos, y_pos)

# Draw the graph
plt.figure(figsize=(14, 10))

# Draw nodes with color by age
node_colors = []
node_sizes = []
for node in G.nodes():
    node_data = G.nodes[node]
    age = node_data['age']
    
    # Color by age (red = older, blue = younger)
    if age > 20000:
        color = '#8b0000'  # dark red for very old
    elif age > 10000:
        color = '#ff4500'  # orange-red
    elif age > 5000:
        color = '#ffa500'  # orange
    elif age > 3000:
        color = '#ffd700'  # gold
    elif age > 1000:
        color = '#90ee90'  # light green
    else:
        color = '#4169e1'  # royal blue
    
    node_colors.append(color)
    node_sizes.append(800)

nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                       node_size=node_sizes, alpha=0.8,
                       edgecolors='black')

# Draw edges with arrows for stratigraphic relationships
nx.draw_networkx_edges(G, pos, edge_color='gray', 
                       arrows=True, arrowsize=20,
                       connectionstyle="arc3,rad=0.1",
                       alpha=0.6)

# Draw labels
labels = {}
for node in G.nodes():
    node_data = G.nodes[node]
    labels[node] = f"{node}\n{node_data['unit']}\n{node_data['age']:.0f} BP"

nx.draw_networkx_labels(G, pos, labels, font_size=9, 
                        font_weight='bold')

plt.title('Stratigraphic Relationships and Chronology at Huangtupo Site')
plt.xlabel('Log10(Calendar Years BP) → Older →')
plt.ylabel('Stratigraphic Position (Trench/Layer)')

# Add a colorbar legend for ages
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# Create a custom colorbar
cmap = cm.get_cmap('viridis_r')
norm = mcolors.Normalize(vmin=df['calibrated_age_BP'].min(), 
                         vmax=df['calibrated_age_BP'].max())

sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

cbar = plt.colorbar(sm, ax=plt.gca(), orientation='vertical', 
                    fraction=0.03, pad=0.04)
cbar.set_label('Calendar Years BP', rotation=270, labelpad=20)

plt.grid(True, alpha=0.3)
plt.tight_layout()

plot_path = "../report/images/stratigraphic_relationships.png"
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_path}")

# Create a simpler bar chart showing age vs layer for Trench 3
if len(trench3_df) > 0:
    plt.figure(figsize=(10, 8))
    
    bars = plt.barh(trench3_df['layer'], trench3_df['calibrated_age_BP'], 
                    color='skyblue', edgecolor='black', alpha=0.7)
    
    # Add error bars
    plt.errorbar(trench3_df['calibrated_age_BP'], trench3_df['layer'],
                 xerr=trench3_df['calibrated_sigma_BP'],
                 fmt='none', ecolor='black', capsize=5, alpha=0.7)
    
    # Add sample labels
    for i, (_, row) in enumerate(trench3_df.iterrows()):
        plt.text(row['calibrated_age_BP'] + 500, row['layer'],
                 f"{row['artifact_id']}\n{row['material']}",
                 fontsize=9, va='center')
    
    plt.xlabel('Calendar Years BP')
    plt.ylabel('Layer Number (L1 = top, L6 = bottom)')
    plt.title('Trench 3: Age vs Stratigraphic Layer (Reveals Inconsistencies)')
    plt.grid(True, alpha=0.3, axis='x')
    
    # Add expected trend line (age should increase with depth)
    if len(trench3_df) > 1:
        # Sort by layer for trend line
        trench3_sorted = trench3_df.sort_values('layer')
        plt.plot(trench3_sorted['calibrated_age_BP'], 
                 trench3_sorted['layer'], 
                 'r--', alpha=0.5, label='Expected trend (older with depth)')
        plt.legend()
    
    plt.tight_layout()
    plot_path2 = "../report/images/trench3_age_vs_layer.png"
    plt.savefig(plot_path2, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {plot_path2}")

print("\nStratigraphic analysis complete!")