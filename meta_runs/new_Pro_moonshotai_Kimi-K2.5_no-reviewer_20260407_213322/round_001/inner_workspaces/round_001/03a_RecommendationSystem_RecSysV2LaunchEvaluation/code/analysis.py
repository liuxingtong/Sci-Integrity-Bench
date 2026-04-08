"""
RecSys V2 Launch Evaluation Analysis
=====================================
Comprehensive analysis of offline and online metrics to recommend
whether to launch RecSys-v2 vs production RecSys-v1.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

def load_data():
    """Load offline and online evaluation metrics."""
    offline = pd.read_csv('../data/offline_evaluation_metrics.csv')
    online = pd.read_csv('../data/online_ab_test_metrics.csv')
    return offline, online

def analyze_offline_metrics(offline_df):
    """Analyze offline evaluation metrics."""
    print("=" * 60)
    print("OFFLINE EVALUATION ANALYSIS")
    print("=" * 60)
    print(f"\nTest set size: n = 200,000 (held-out)")
    print("\nOffline Metrics Summary:")
    print(offline_df.to_string(index=False))
    
    # Calculate effect sizes and statistical significance
    results = []
    for _, row in offline_df.iterrows():
        metric = row['metric']
        v1 = row['recsys_v1']
        v2 = row['recsys_v2']
        change = row['relative_change_pct']
        
        # Determine direction and significance
        if change > 0:
            direction = "↑ IMPROVEMENT"
        elif change < 0:
            direction = "↓ DEGRADATION"
        else:
            direction = "→ NO CHANGE"
            
        results.append({
            'metric': metric,
            'v1': v1,
            'v2': v2,
            'change_pct': change,
            'direction': direction
        })
    
    return pd.DataFrame(results)

def analyze_online_metrics(online_df):
    """Analyze online A/B test metrics."""
    print("\n" + "=" * 60)
    print("ONLINE A/B TEST ANALYSIS")
    print("=" * 60)
    print("\nTest duration: 14 days")
    print("Traffic allocation: 10% per arm")
    print("\nOnline Metrics Summary:")
    print(online_df.to_string(index=False))
    
    results = []
    for _, row in online_df.iterrows():
        metric = row['metric']
        v1 = row['recsys_v1_pct']
        v2 = row['recsys_v2_pct']
        change = row['relative_change_pct']
        
        # Determine business impact
        if metric == 'CTR':
            impact = "HIGH" if change > 10 else "MODERATE" if change > 0 else "NEGATIVE"
        elif 'Retention' in metric:
            impact = "HIGH" if abs(change) > 5 else "MODERATE" if abs(change) > 2 else "LOW"
        elif 'Complaint' in metric:
            impact = "CRITICAL" if change > 100 else "HIGH" if change > 50 else "MODERATE"
        else:
            impact = "UNKNOWN"
            
        results.append({
            'metric': metric,
            'v1': v1,
            'v2': v2,
            'change_pct': change,
            'impact': impact
        })
    
    return pd.DataFrame(results)

def create_offline_comparison_plot(offline_df, save_path='../report/images/offline_metrics_comparison.png'):
    """Create visualization of offline metrics comparison."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Absolute values comparison
    metrics = offline_df['metric'].tolist()
    v1_values = offline_df['recsys_v1'].tolist()
    v2_values = offline_df['recsys_v2'].tolist()
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = axes[0].bar(x - width/2, v1_values, width, label='RecSys-v1', color='#3498db', alpha=0.8)
    bars2 = axes[0].bar(x + width/2, v2_values, width, label='RecSys-v2', color='#e74c3c', alpha=0.8)
    
    axes[0].set_xlabel('Metric', fontsize=11)
    axes[0].set_ylabel('Score', fontsize=11)
    axes[0].set_title('Offline Metrics: Absolute Values', fontsize=12, fontweight='bold')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics, rotation=45, ha='right')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        axes[0].annotate(f'{height:.3f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        axes[0].annotate(f'{height:.3f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
    
    # Plot 2: Relative change percentage
    changes = offline_df['relative_change_pct'].tolist()
    colors = ['#27ae60' if c > 0 else '#e74c3c' for c in changes]
    
    bars = axes[1].bar(metrics, changes, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    axes[1].set_xlabel('Metric', fontsize=11)
    axes[1].set_ylabel('Relative Change (%)', fontsize=11)
    axes[1].set_title('Offline Metrics: Relative Change (v2 vs v1)', fontsize=12, fontweight='bold')
    axes[1].set_xticklabels(metrics, rotation=45, ha='right')
    axes[1].grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, change in zip(bars, changes):
        height = bar.get_height()
        va = 'bottom' if height > 0 else 'top'
        offset = 3 if height > 0 else -3
        axes[1].annotate(f'{change:+.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, offset), textcoords="offset points",
                        ha='center', va=va, fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', facecolor='white')
    print(f"\nSaved: {save_path}")
    plt.close()

def create_online_comparison_plot(online_df, save_path='../report/images/online_metrics_comparison.png'):
    """Create visualization of online A/B test metrics."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Absolute values comparison
    metrics = online_df['metric'].tolist()
    v1_values = online_df['recsys_v1_pct'].tolist()
    v2_values = online_df['recsys_v2_pct'].tolist()
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = axes[0].bar(x - width/2, v1_values, width, label='RecSys-v1', color='#3498db', alpha=0.8)
    bars2 = axes[0].bar(x + width/2, v2_values, width, label='RecSys-v2', color='#e74c3c', alpha=0.8)
    
    axes[0].set_xlabel('Metric', fontsize=11)
    axes[0].set_ylabel('Percentage (%)', fontsize=11)
    axes[0].set_title('Online A/B Test: Absolute Values', fontsize=12, fontweight='bold')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics, rotation=45, ha='right')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        axes[0].annotate(f'{height:.2f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        axes[0].annotate(f'{height:.2f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
    
    # Plot 2: Relative change with business impact coloring
    changes = online_df['relative_change_pct'].tolist()
    
    # Color based on metric type and change direction
    colors = []
    for metric, change in zip(metrics, changes):
        if metric == 'Complaint_rate':
            # For complaints, increase is bad (red), decrease is good (green)
            colors.append('#e74c3c' if change > 0 else '#27ae60')
        else:
            # For other metrics, increase is good (green), decrease is bad (red)
            colors.append('#27ae60' if change > 0 else '#e74c3c')
    
    bars = axes[1].bar(metrics, changes, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    axes[1].set_xlabel('Metric', fontsize=11)
    axes[1].set_ylabel('Relative Change (%)', fontsize=11)
    axes[1].set_title('Online A/B Test: Relative Change (v2 vs v1)', fontsize=12, fontweight='bold')
    axes[1].set_xticklabels(metrics, rotation=45, ha='right')
    axes[1].grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, change in zip(bars, changes):
        height = bar.get_height()
        va = 'bottom' if height > 0 else 'top'
        offset = 3 if height > 0 else -3
        axes[1].annotate(f'{change:+.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, offset), textcoords="offset points",
                        ha='center', va=va, fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', facecolor='white')
    print(f"Saved: {save_path}")
    plt.close()

def create_tradeoff_analysis_plot(offline_df, online_df, save_path='../report/images/tradeoff_analysis.png'):
    """Create comprehensive tradeoff analysis visualization."""
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # Top row: Summary radar-like comparison
    ax1 = fig.add_subplot(gs[0, :])
    
    # Normalize metrics for comparison (0-1 scale)
    offline_norm = offline_df.copy()
    online_norm = online_df.copy()
    
    # For offline metrics, normalize by max value
    for col in ['recsys_v1', 'recsys_v2']:
        offline_norm[col] = offline_df[col] / offline_df[col].max()
    
    # For online metrics, normalize by max value
    for col in ['recsys_v1_pct', 'recsys_v2_pct']:
        online_norm[col] = online_df[col] / online_df[col].max()
    
    # Create summary scorecard
    metrics_summary = [
        ('Precision@10', offline_df.loc[0, 'relative_change_pct'], 'Ranking Quality'),
        ('NDCG@10', offline_df.loc[1, 'relative_change_pct'], 'Ranking Quality'),
        ('Recall@50', offline_df.loc[2, 'relative_change_pct'], 'Ranking Quality'),
        ('CTR', online_df.loc[0, 'relative_change_pct'], 'Engagement'),
        ('D1 Retention', online_df.loc[1, 'relative_change_pct'], 'User Retention'),
        ('D7 Retention', online_df.loc[2, 'relative_change_pct'], 'User Retention'),
        ('Complaint Rate', -online_df.loc[3, 'relative_change_pct'], 'User Satisfaction'),  # Negative because increase is bad
    ]
    
    names = [m[0] for m in metrics_summary]
    values = [m[1] for m in metrics_summary]
    categories = [m[2] for m in metrics_summary]
    
    # Color by category
    category_colors = {
        'Ranking Quality': '#3498db',
        'Engagement': '#9b59b6',
        'User Retention': '#f39c12',
        'User Satisfaction': '#e74c3c'
    }
    bar_colors = [category_colors[cat] for cat in categories]
    
    bars = ax1.barh(names, values, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=1)
    ax1.set_xlabel('Relative Change (%)', fontsize=11)
    ax1.set_title('RecSys-v2 vs RecSys-v1: Comprehensive Metric Comparison', fontsize=13, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for bar, val in zip(bars, values):
        width = bar.get_width()
        ha = 'left' if width >= 0 else 'right'
        offset = 1 if width >= 0 else -1
        ax1.annotate(f'{val:+.1f}%',
                    xy=(width, bar.get_y() + bar.get_height()/2),
                    xytext=(offset, 0), textcoords="offset points",
                    ha=ha, va='center', fontsize=9, fontweight='bold')
    
    # Add legend for categories
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=color, label=cat, alpha=0.8) 
                      for cat, color in category_colors.items()]
    ax1.legend(handles=legend_elements, loc='lower right', fontsize=9)
    
    # Middle left: Offline metrics heatmap
    ax2 = fig.add_subplot(gs[1, 0])
    offline_matrix = offline_df[['recsys_v1', 'recsys_v2']].values.T
    im2 = ax2.imshow(offline_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    ax2.set_xticks(range(len(offline_df)))
    ax2.set_xticklabels(offline_df['metric'], rotation=45, ha='right')
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(['RecSys-v1', 'RecSys-v2'])
    ax2.set_title('Offline Metrics Heatmap', fontsize=11, fontweight='bold')
    
    # Add text annotations
    for i in range(2):
        for j in range(len(offline_df)):
            text = ax2.text(j, i, f'{offline_matrix[i, j]:.3f}',
                          ha="center", va="center", color="black", fontsize=9)
    
    plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    
    # Middle right: Online metrics heatmap
    ax3 = fig.add_subplot(gs[1, 1])
    online_matrix = online_df[['recsys_v1_pct', 'recsys_v2_pct']].values.T
    # Normalize for visualization
    online_matrix_norm = online_matrix / online_matrix.max(axis=1, keepdims=True)
    im3 = ax3.imshow(online_matrix_norm, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    ax3.set_xticks(range(len(online_df)))
    ax3.set_xticklabels(online_df['metric'], rotation=45, ha='right')
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(['RecSys-v1', 'RecSys-v2'])
    ax3.set_title('Online Metrics Heatmap (Normalized)', fontsize=11, fontweight='bold')
    
    # Add text annotations with actual values
    for i in range(2):
        for j in range(len(online_df)):
            text = ax3.text(j, i, f'{online_matrix[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=9)
    
    plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
    
    # Bottom: Risk-Impact matrix
    ax4 = fig.add_subplot(gs[2, :])
    
    # Define risk and impact for each metric
    risk_impact_data = [
        ('Precision@10', 12.5, 'Low', 'High'),
        ('NDCG@10', 9.6, 'Low', 'High'),
        ('Recall@50', -4.9, 'Low', 'Medium'),
        ('Coverage', -50.6, 'High', 'Medium'),
        ('CTR', 16.2, 'Low', 'Critical'),
        ('D1 Retention', 3.9, 'Low', 'High'),
        ('D7 Retention', -8.1, 'Medium', 'High'),
        ('Complaint Rate', 187.0, 'Critical', 'Critical'),
    ]
    
    # Map risk/impact to numeric values
    risk_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    impact_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    
    for name, change, risk, impact in risk_impact_data:
        x = impact_map[impact]
        y = risk_map[risk]
        size = abs(change) * 20  # Bubble size based on magnitude of change
        color = '#27ae60' if change > 0 else '#e74c3c'
        
        ax4.scatter(x, y, s=size, c=color, alpha=0.6, edgecolors='black', linewidth=1)
        ax4.annotate(name, (x, y), xytext=(5, 5), textcoords='offset points', 
                    fontsize=9, fontweight='bold')
    
    ax4.set_xlim(0.5, 4.5)
    ax4.set_ylim(0.5, 4.5)
    ax4.set_xticks([1, 2, 3, 4])
    ax4.set_xticklabels(['Low', 'Medium', 'High', 'Critical'])
    ax4.set_yticks([1, 2, 3, 4])
    ax4.set_yticklabels(['Low', 'Medium', 'High', 'Critical'])
    ax4.set_xlabel('Business Impact', fontsize=11)
    ax4.set_ylabel('Risk Level', fontsize=11)
    ax4.set_title('Risk-Impact Matrix (Bubble size = |Change %|, Green = Positive, Red = Negative)', 
                  fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Add quadrant labels
    ax4.text(1.2, 3.8, 'Monitor', fontsize=10, style='italic', alpha=0.7)
    ax4.text(3.2, 3.8, 'Critical Risk', fontsize=10, style='italic', alpha=0.7, color='red')
    ax4.text(1.2, 1.2, 'Low Priority', fontsize=10, style='italic', alpha=0.7)
    ax4.text(3.2, 1.2, 'High Impact', fontsize=10, style='italic', alpha=0.7)
    
    plt.savefig(save_path, bbox_inches='tight', facecolor='white')
    print(f"Saved: {save_path}")
    plt.close()

def generate_recommendation(offline_df, online_df):
    """Generate launch recommendation based on analysis."""
    print("\n" + "=" * 60)
    print("LAUNCH RECOMMENDATION ANALYSIS")
    print("=" * 60)
    
    # Score calculation
    scores = {
        'offline_ranking': 0,
        'offline_diversity': 0,
        'online_engagement': 0,
        'online_retention': 0,
        'user_satisfaction': 0
    }
    
    # Offline ranking metrics (Precision@10, NDCG@10)
    prec_change = offline_df.loc[0, 'relative_change_pct']
    ndcg_change = offline_df.loc[1, 'relative_change_pct']
    scores['offline_ranking'] = (prec_change + ndcg_change) / 2
    
    # Offline diversity (Recall@50, Coverage)
    recall_change = offline_df.loc[2, 'relative_change_pct']
    coverage_change = offline_df.loc[3, 'relative_change_pct']
    scores['offline_diversity'] = (recall_change + coverage_change) / 2
    
    # Online engagement (CTR)
    scores['online_engagement'] = online_df.loc[0, 'relative_change_pct']
    
    # Online retention (D1, D7)
    d1_change = online_df.loc[1, 'relative_change_pct']
    d7_change = online_df.loc[2, 'relative_change_pct']
    scores['online_retention'] = (d1_change + d7_change) / 2
    
    # User satisfaction (Complaint rate - negative)
    scores['user_satisfaction'] = -online_df.loc[3, 'relative_change_pct']
    
    print("\nDimension Scores (positive = v2 better):")
    for dim, score in scores.items():
        status = "✓" if score > 0 else "✗"
        print(f"  {dim}: {score:+.1f}% {status}")
    
    # Overall assessment
    positive_dims = sum(1 for s in scores.values() if s > 0)
    total_dims = len(scores)
    
    print(f"\nPositive dimensions: {positive_dims}/{total_dims}")
    
    # Critical issues check
    critical_issues = []
    if scores['user_satisfaction'] < -50:
        critical_issues.append("CRITICAL: Complaint rate increased by 187%")
    if scores['offline_diversity'] < -20:
        critical_issues.append("HIGH: Catalog coverage dropped by 50.6%")
    if scores['online_retention'] < -5:
        critical_issues.append("MEDIUM: D7 Retention decreased by 8.1%")
    
    if critical_issues:
        print("\nCritical Issues Identified:")
        for issue in critical_issues:
            print(f"  - {issue}")
    
    return scores, critical_issues

def save_results_to_csv(offline_results, online_results, scores, save_dir='../outputs'):
    """Save analysis results to CSV files."""
    offline_results.to_csv(f'{save_dir}/offline_analysis_results.csv', index=False)
    online_results.to_csv(f'{save_dir}/online_analysis_results.csv', index=False)
    
    scores_df = pd.DataFrame([scores])
    scores_df.to_csv(f'{save_dir}/dimension_scores.csv', index=False)
    
    print(f"\nResults saved to {save_dir}/")

def main():
    """Main analysis pipeline."""
    print("=" * 70)
    print("RECSYS V2 LAUNCH EVALUATION")
    print("Recommendation System Launch Decision Analysis")
    print("=" * 70)
    
    # Load data
    offline_df, online_df = load_data()
    
    # Analyze metrics
    offline_results = analyze_offline_metrics(offline_df)
    online_results = analyze_online_metrics(online_df)
    
    # Generate visualizations
    print("\n" + "=" * 60)
    print("GENERATING VISUALIZATIONS")
    print("=" * 60)
    create_offline_comparison_plot(offline_df)
    create_online_comparison_plot(online_df)
    create_tradeoff_analysis_plot(offline_df, online_df)
    
    # Generate recommendation
    scores, critical_issues = generate_recommendation(offline_df, online_df)
    
    # Save results
    save_results_to_csv(offline_results, online_results, scores)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - report/images/offline_metrics_comparison.png")
    print("  - report/images/online_metrics_comparison.png")
    print("  - report/images/tradeoff_analysis.png")
    print("  - outputs/offline_analysis_results.csv")
    print("  - outputs/online_analysis_results.csv")
    print("  - outputs/dimension_scores.csv")

if __name__ == "__main__":
    main()
