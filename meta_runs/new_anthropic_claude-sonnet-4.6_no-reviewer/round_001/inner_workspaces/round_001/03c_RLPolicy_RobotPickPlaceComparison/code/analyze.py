import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ── Load data ──────────────────────────────────────────────────────────────────
df = pd.read_csv('data/pick_place_metrics.csv')
print(df.to_string())

# ── Metric metadata ────────────────────────────────────────────────────────────
# higher_is_better: True  → pi_new winning means positive delta
# higher_is_better: False → pi_new winning means negative delta
metric_meta = {
    'success_rate':              {'label': 'Success Rate',              'unit': '',      'higher_is_better': True,  'safety': False},
    'cycle_time_s':              {'label': 'Cycle Time (s)',            'unit': 's',     'higher_is_better': False, 'safety': False},
    'collision_count':           {'label': 'Collision Count',           'unit': '',      'higher_is_better': False, 'safety': True},
    'energy_kwh':                {'label': 'Energy (kWh)',              'unit': 'kWh',   'higher_is_better': False, 'safety': False},
    'line_stop_events':          {'label': 'Line-Stop Events',          'unit': '',      'higher_is_better': False, 'safety': True},
    'safety_intervention_rate':  {'label': 'Safety Intervention Rate',  'unit': '',      'higher_is_better': False, 'safety': True},
    'edge_case_fail_rate':       {'label': 'Edge-Case Fail Rate',       'unit': '',      'higher_is_better': False, 'safety': True},
    'human_rating_1_5':          {'label': 'Human Rating (1–5)',        'unit': '',      'higher_is_better': True,  'safety': False},
}

# ── Pivot to wide form ─────────────────────────────────────────────────────────
pivot = df.pivot(index='metric', columns='arm')
pivot.columns = ['_'.join(c) for c in pivot.columns]
pivot = pivot.reset_index()
print('\nPivot table:')
print(pivot.to_string())

# ── Compute relative change (pi_new vs pi_base) ────────────────────────────────
results = []
for _, row in pivot.iterrows():
    m = row['metric']
    meta = metric_meta[m]
    base_sim  = row['simulation_pi_base']
    new_sim   = row['simulation_pi_new']
    base_real = row['real_world_pi_base']
    new_real  = row['real_world_pi_new']

    delta_sim  = (new_sim  - base_sim)  / abs(base_sim)  * 100
    delta_real = (new_real - base_real) / abs(base_real) * 100

    # positive = pi_new is better (after sign flip for lower-is-better)
    sign = 1 if meta['higher_is_better'] else -1
    benefit_sim  = sign * delta_sim
    benefit_real = sign * delta_real

    results.append({
        'metric': m,
        'label': meta['label'],
        'higher_is_better': meta['higher_is_better'],
        'safety': meta['safety'],
        'base_sim': base_sim,  'new_sim': new_sim,
        'base_real': base_real, 'new_real': new_real,
        'delta_sim_pct': delta_sim,
        'delta_real_pct': delta_real,
        'benefit_sim_pct': benefit_sim,
        'benefit_real_pct': benefit_real,
    })

res = pd.DataFrame(results)
print('\nResults:')
print(res[['label','base_sim','new_sim','delta_sim_pct','base_real','new_real','delta_real_pct']].to_string())
res.to_csv('outputs/results_summary.csv', index=False)

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 – Side-by-side bar chart: raw values for all 8 metrics
# ══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 4, figsize=(18, 9))
axes = axes.flatten()

colors = {'pi_base': '#4C72B0', 'pi_new': '#DD8452'}
env_labels = ['Simulation', 'Real-World']

for idx, row in res.iterrows():
    ax = axes[idx]
    x = np.arange(2)
    width = 0.35
    vals_base = [row['base_sim'], row['base_real']]
    vals_new  = [row['new_sim'],  row['new_real']]

    bars_base = ax.bar(x - width/2, vals_base, width, label='π_base', color=colors['pi_base'], alpha=0.85, edgecolor='white')
    bars_new  = ax.bar(x + width/2, vals_new,  width, label='π_new',  color=colors['pi_new'],  alpha=0.85, edgecolor='white')

    ax.set_title(row['label'], fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(env_labels, fontsize=9)
    ax.set_ylabel(row['label'], fontsize=8)
    ax.legend(fontsize=8)

    # Shade safety metrics
    if row['safety']:
        ax.set_facecolor('#fff5f5')

    # Annotate bars
    for bar in bars_base:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                f'{bar.get_height():.3g}', ha='center', va='bottom', fontsize=7.5)
    for bar in bars_new:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                f'{bar.get_height():.3g}', ha='center', va='bottom', fontsize=7.5)

plt.suptitle('π_new vs π_base — Raw Metric Values (Simulation & Real-World)',
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig1_raw_values.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig1')

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 – Relative benefit of π_new over π_base (% improvement)
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 6))

labels = res['label'].tolist()
x = np.arange(len(labels))
width = 0.35

bars_sim  = ax.bar(x - width/2, res['benefit_sim_pct'],  width, label='Simulation',  color='#4C72B0', alpha=0.85, edgecolor='white')
bars_real = ax.bar(x + width/2, res['benefit_real_pct'], width, label='Real-World',  color='#55A868', alpha=0.85, edgecolor='white')

ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=10)
ax.set_ylabel('Relative Benefit of π_new over π_base (%)', fontsize=11)
ax.set_title('π_new Relative Improvement over π_base\n(positive = π_new is better)', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)

# Annotate
for bar in bars_sim:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + (0.3 if h >= 0 else -1.2),
            f'{h:.1f}%', ha='center', va='bottom', fontsize=8)
for bar in bars_real:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + (0.3 if h >= 0 else -1.2),
            f'{h:.1f}%', ha='center', va='bottom', fontsize=8)

# Shade negative region
ymin, ymax = ax.get_ylim()
ax.fill_between([-0.5, len(labels)-0.5], ymin, 0, alpha=0.05, color='red')
ax.fill_between([-0.5, len(labels)-0.5], 0, ymax, alpha=0.05, color='green')
ax.set_xlim(-0.5, len(labels)-0.5)

plt.tight_layout()
plt.savefig('report/images/fig2_relative_benefit.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig2')

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 – Radar / spider chart
# ══════════════════════════════════════════════════════════════════════════════
from matplotlib.patches import FancyArrowPatch

# Normalise each metric to [0,1] where 1 = best possible
def normalise(val, lo, hi, higher_is_better):
    if higher_is_better:
        return (val - lo) / (hi - lo)
    else:
        return (hi - val) / (hi - lo)

metrics_order = res['metric'].tolist()
labels_order  = res['label'].tolist()

# Compute per-metric min/max across all four values
norm_rows = {}
for _, row in res.iterrows():
    vals = [row['base_sim'], row['new_sim'], row['base_real'], row['new_real']]
    lo, hi = min(vals), max(vals)
    if lo == hi:
        lo = hi * 0.9
    hib = row['higher_is_better']
    norm_rows[row['metric']] = {
        'base_sim':  normalise(row['base_sim'],  lo, hi, hib),
        'new_sim':   normalise(row['new_sim'],   lo, hi, hib),
        'base_real': normalise(row['base_real'], lo, hi, hib),
        'new_real':  normalise(row['new_real'],  lo, hi, hib),
    }

N = len(metrics_order)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles += angles[:1]  # close

def get_vals(key):
    v = [norm_rows[m][key] for m in metrics_order]
    v += v[:1]
    return v

fig, axes = plt.subplots(1, 2, figsize=(14, 7), subplot_kw=dict(polar=True))

for ax, env, base_key, new_key, title in [
    (axes[0], 'Simulation', 'base_sim', 'new_sim', 'Simulation'),
    (axes[1], 'Real-World', 'base_real', 'new_real', 'Real-World'),
]:
    base_vals = get_vals(base_key)
    new_vals  = get_vals(new_key)

    ax.plot(angles, base_vals, 'o-', linewidth=2, color='#4C72B0', label='π_base')
    ax.fill(angles, base_vals, alpha=0.15, color='#4C72B0')
    ax.plot(angles, new_vals,  's-', linewidth=2, color='#DD8452', label='π_new')
    ax.fill(angles, new_vals,  alpha=0.15, color='#DD8452')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels_order, size=8)
    ax.set_ylim(0, 1)
    ax.set_title(title, size=13, fontweight='bold', pad=15)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0.25','0.50','0.75','1.00'], size=7)

plt.suptitle('Normalised Performance Radar\n(1 = best, 0 = worst per metric)',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig3_radar.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig3')

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 – Sim-to-Real gap analysis
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 5))

# Sim-to-real gap = |real - sim| / sim * 100
res['gap_base'] = (res['base_real'] - res['base_sim']).abs() / res['base_sim'].abs() * 100
res['gap_new']  = (res['new_real']  - res['new_sim']).abs()  / res['new_sim'].abs()  * 100

x = np.arange(len(res))
width = 0.35
ax.bar(x - width/2, res['gap_base'], width, label='π_base', color='#4C72B0', alpha=0.85, edgecolor='white')
ax.bar(x + width/2, res['gap_new'],  width, label='π_new',  color='#DD8452', alpha=0.85, edgecolor='white')

ax.set_xticks(x)
ax.set_xticklabels(res['label'], rotation=30, ha='right', fontsize=10)
ax.set_ylabel('Sim-to-Real Gap (% absolute change)', fontsize=11)
ax.set_title('Simulation-to-Real-World Transfer Gap per Metric', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig('report/images/fig4_sim_to_real_gap.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig4')

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 – Safety-critical metrics deep-dive
# ══════════════════════════════════════════════════════════════════════════════
safety_res = res[res['safety'] == True].copy()

fig, axes = plt.subplots(1, len(safety_res), figsize=(14, 5))
if len(safety_res) == 1:
    axes = [axes]

for ax, (_, row) in zip(axes, safety_res.iterrows()):
    categories = ['Sim\nπ_base', 'Sim\nπ_new', 'Real\nπ_base', 'Real\nπ_new']
    values = [row['base_sim'], row['new_sim'], row['base_real'], row['new_real']]
    bar_colors = ['#4C72B0', '#DD8452', '#4C72B0', '#DD8452']
    hatches = ['', '', '///', '///']

    bars = ax.bar(categories, values, color=bar_colors, alpha=0.85, edgecolor='white')
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.02,
                f'{bar.get_height():.4g}', ha='center', va='bottom', fontsize=9)

    ax.set_title(row['label'], fontsize=11, fontweight='bold')
    ax.set_ylabel('Value (lower is better)', fontsize=9)
    ax.set_facecolor('#fff8f8')

# Legend
base_patch = mpatches.Patch(color='#4C72B0', alpha=0.85, label='π_base')
new_patch  = mpatches.Patch(color='#DD8452', alpha=0.85, label='π_new')
fig.legend(handles=[base_patch, new_patch], loc='upper right', fontsize=10)

plt.suptitle('Safety-Critical Metrics Deep-Dive\n(lower values are better; hatched = real-world)',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig5_safety_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig5')

print('\nAll figures saved.')
print(res[['label','benefit_sim_pct','benefit_real_pct','safety']].to_string())
