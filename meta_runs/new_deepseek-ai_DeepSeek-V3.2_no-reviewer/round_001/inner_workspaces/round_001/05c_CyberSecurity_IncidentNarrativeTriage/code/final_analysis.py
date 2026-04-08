#!/usr/bin/env python3
"""
Final analysis script combining preprocessing and triage results.
Generates comprehensive insights for the research report.
"""

import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os
from typing import Dict, List


def load_all_data() -> Dict:
    """Load all generated data files."""
    data = {}
    
    # Load original data
    data['original'] = pd.read_csv("../data/incident_narratives.csv")
    
    # Load processed data
    data['processed'] = pd.read_csv("../outputs/processed_incidents.csv")
    
    # Load data summaries
    with open("../outputs/data_summaries.json", 'r') as f:
        data['summaries'] = json.load(f)
    
    # Load Gemini triage summary
    data['triage_summary'] = pd.read_csv("../outputs/gemini_raw_summary.csv")
    
    # Load Gemini raw responses
    with open("../outputs/gemini_raw.json", 'r') as f:
        data['gemini_raw'] = json.load(f)
    
    return data


def analyze_triage_effectiveness(data: Dict) -> Dict:
    """Analyze the effectiveness of automated triage."""
    results = {}
    
    # Merge processed data with triage summary
    merged = pd.merge(
        data['processed'], 
        data['triage_summary'], 
        on=['incident_id', 'source_system']
    )
    
    # Calculate correlation between narrative features and triage priority
    priority_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    merged['priority_numeric'] = merged['priority'].map(priority_map)
    
    # Correlation analysis
    numeric_cols = ['narrative_length', 'word_count', 'term_count', 'confidence_score']
    correlations = merged[numeric_cols + ['priority_numeric']].corr()['priority_numeric'].drop('priority_numeric')
    
    results['correlations_with_priority'] = correlations.to_dict()
    
    # Effectiveness metrics
    # 1. Time savings estimation
    time_map = {'2-4 hours': 3, '8-24 hours': 16, '24-72 hours': 48}
    merged['estimated_hours'] = merged['estimated_resolution_time'].map(time_map)
    
    # Assuming manual triage takes 15 minutes per incident on average
    manual_time_per_incident = 0.25  # hours
    total_manual_time = len(merged) * manual_time_per_incident
    total_automated_time = 0.01 * len(merged)  # 0.6 seconds per incident
    
    time_savings = total_manual_time - total_automated_time
    time_savings_percentage = (time_savings / total_manual_time) * 100
    
    results['time_savings'] = {
        'total_manual_hours': total_manual_time,
        'total_automated_hours': total_automated_time,
        'time_savings_hours': time_savings,
        'time_savings_percentage': time_savings_percentage
    }
    
    # 2. Priority distribution consistency
    # Check if automated triage aligns with estimated severity from preprocessing
    severity_priority_map = {'high': 'HIGH', 'medium': 'MEDIUM', 'low': 'LOW', 'unknown': 'MEDIUM'}
    merged['expected_priority'] = merged['estimated_severity'].map(severity_priority_map)
    
    accuracy = (merged['priority'] == merged['expected_priority']).mean() * 100
    results['priority_alignment_accuracy'] = accuracy
    
    # 3. Risk detection coverage
    high_risk_incidents = len(merged[merged['priority'] == 'HIGH'])
    total_incidents = len(merged)
    high_risk_percentage = (high_risk_incidents / total_incidents) * 100
    
    results['risk_detection'] = {
        'high_risk_count': high_risk_incidents,
        'high_risk_percentage': high_risk_percentage,
        'false_positives': merged['is_false_positive'].sum(),
        'encoded_content_detected': merged['has_encoded_content'].sum(),
        'data_exfiltration_detected': merged['has_data_exfiltration'].sum()
    }
    
    # 4. Source system analysis
    source_analysis = merged.groupby('source_system').agg({
        'priority': lambda x: (x == 'HIGH').mean() * 100,
        'confidence_score': 'mean',
        'entities_count': 'mean',
        'actions_count': 'mean'
    }).round(2)
    
    results['source_system_analysis'] = source_analysis.to_dict('index')
    
    return results


def create_comprehensive_visualizations(data: Dict, analysis_results: Dict, output_dir: str):
    """Create comprehensive visualizations combining all analyses."""
    os.makedirs(output_dir, exist_ok=True)
    
    merged = pd.merge(
        data['processed'], 
        data['triage_summary'], 
        on=['incident_id', 'source_system']
    )
    
    # Figure 10: Correlation heatmap
    plt.figure(figsize=(10, 8))
    numeric_cols = ['narrative_length', 'word_count', 'term_count', 'confidence_score', 'entities_count', 'actions_count']
    correlation_matrix = merged[numeric_cols].corr()
    
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title('Correlation Matrix of Narrative and Triage Features', 
              fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure10_correlation_heatmap.png'), 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 11: Time savings visualization
    plt.figure(figsize=(10, 6))
    time_data = analysis_results['time_savings']
    categories = ['Manual Triage', 'Automated Triage']
    times = [time_data['total_manual_hours'], time_data['total_automated_hours']]
    
    bars = plt.bar(categories, times, color=['lightcoral', 'lightgreen'], edgecolor='black')
    plt.title('Time Comparison: Manual vs Automated Triage', fontsize=16, fontweight='bold')
    plt.ylabel('Total Hours Required', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                 f'{height:.3f}h', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure11_time_savings.png'), 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 12: Priority alignment
    plt.figure(figsize=(10, 6))
    accuracy = analysis_results['priority_alignment_accuracy']
    
    plt.bar(['Alignment Accuracy'], [accuracy], color='skyblue', edgecolor='black')
    plt.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='Perfect Alignment')
    plt.title('Automated vs Expected Priority Alignment', fontsize=16, fontweight='bold')
    plt.ylabel('Accuracy (%)', fontsize=12)
    plt.ylim(0, 110)
    plt.grid(axis='y', alpha=0.3)
    plt.legend()
    
    plt.text(0, accuracy + 2, f'{accuracy:.1f}%', ha='center', va='bottom', 
             fontweight='bold', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure12_priority_alignment.png'), 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 13: Comprehensive risk assessment
    plt.figure(figsize=(12, 8))
    risk_data = analysis_results['risk_detection']
    
    risk_metrics = {
        'High Risk Incidents': risk_data['high_risk_percentage'],
        'False Positives': (risk_data['false_positives'] / len(merged)) * 100,
        'Encoded Content': (risk_data['encoded_content_detected'] / len(merged)) * 100,
        'Data Exfiltration': (risk_data['data_exfiltration_detected'] / len(merged)) * 100
    }
    
    colors = ['red', 'orange', 'yellow', 'green']
    bars = plt.bar(risk_metrics.keys(), risk_metrics.values(), color=colors, edgecolor='black')
    plt.title('Comprehensive Risk Assessment Metrics', fontsize=16, fontweight='bold')
    plt.ylabel('Percentage of Incidents (%)', fontsize=12)
    plt.xticks(rotation=15)
    plt.grid(axis='y', alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                 f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure13_risk_assessment.png'), 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Comprehensive visualizations saved to {output_dir}")


def generate_insights_report(data: Dict, analysis_results: Dict) -> str:
    """Generate a text report of key insights."""
    report = []
    report.append("=" * 60)
    report.append("COMPREHENSIVE INCIDENT TRIAGE ANALYSIS INSIGHTS")
    report.append("=" * 60)
    report.append("")
    
    # Data overview
    report.append("1. DATA OVERVIEW")
    report.append("-" * 40)
    report.append(f"Total incidents analyzed: {data['summaries']['total_incidents']}")
    report.append(f"Source system distribution: {data['summaries']['by_source']}")
    report.append(f"Average narrative length: {data['summaries']['narrative_stats']['mean_length']:.1f} characters")
    report.append(f"Average word count: {data['summaries']['narrative_stats']['mean_word_count']:.1f} words")
    report.append("")
    
    # Triage results
    report.append("2. AUTOMATED TRIAGE RESULTS")
    report.append("-" * 40)
    priority_dist = data['triage_summary']['priority'].value_counts().to_dict()
    report.append(f"Priority distribution: {priority_dist}")
    report.append(f"Average confidence score: {data['triage_summary']['confidence_score'].mean():.1f}")
    report.append(f"Average entities extracted per incident: {data['triage_summary']['entities_count'].mean():.1f}")
    report.append("")
    
    # Effectiveness analysis
    report.append("3. EFFECTIVENESS ANALYSIS")
    report.append("-" * 40)
    
    time_savings = analysis_results['time_savings']
    report.append(f"Time savings: {time_savings['time_savings_hours']:.3f} hours ({time_savings['time_savings_percentage']:.1f}% reduction)")
    report.append(f"Priority alignment accuracy: {analysis_results['priority_alignment_accuracy']:.1f}%")
    
    risk = analysis_results['risk_detection']
    report.append(f"High-risk incidents identified: {risk['high_risk_count']} ({risk['high_risk_percentage']:.1f}%)")
    report.append(f"False positives detected: {risk['false_positives']}")
    report.append(f"Incidents with encoded content: {risk['encoded_content_detected']}")
    report.append(f"Incidents with data exfiltration indicators: {risk['data_exfiltration_detected']}")
    report.append("")
    
    # Correlation insights
    report.append("4. KEY CORRELATIONS")
    report.append("-" * 40)
    correlations = analysis_results['correlations_with_priority']
    for feature, corr in correlations.items():
        report.append(f"{feature}: {corr:.3f}")
    report.append("")
    
    # Source system insights
    report.append("5. SOURCE SYSTEM ANALYSIS")
    report.append("-" * 40)
    source_analysis = analysis_results['source_system_analysis']
    for source, metrics in source_analysis.items():
        report.append(f"{source.upper()}:")
        report.append(f"  • High priority rate: {metrics['priority']}%")
        report.append(f"  • Average confidence: {metrics['confidence_score']}")
        report.append(f"  • Average entities: {metrics['entities_count']}")
        report.append(f"  • Average actions: {metrics['actions_count']}")
    report.append("")
    
    # Recommendations
    report.append("6. RECOMMENDATIONS")
    report.append("-" * 40)
    report.append("1. Implement automated triage for all incoming incidents")
    report.append("2. Focus manual review on HIGH priority incidents")
    report.append("3. Use extracted entities for threat hunting and correlation")
    report.append("4. Continuously refine triage rules based on analyst feedback")
    report.append("5. Expand entity extraction to include more asset types")
    
    return "\n".join(report)


def main():
    """Main execution function."""
    print("Loading all data for comprehensive analysis...")
    data = load_all_data()
    
    print("Analyzing triage effectiveness...")
    analysis_results = analyze_triage_effectiveness(data)
    
    print("Creating comprehensive visualizations...")
    create_comprehensive_visualizations(data, analysis_results, "../report/images")
    
    print("Generating insights report...")
    insights = generate_insights_report(data, analysis_results)
    
    # Save insights to file
    insights_path = "../outputs/comprehensive_insights.txt"
    with open(insights_path, 'w') as f:
        f.write(insights)
    
    print(f"\nInsights saved to {insights_path}")
    print("\n" + "=" * 60)
    print(insights)
    print("=" * 60)
    
    print("\nComprehensive analysis complete!")


if __name__ == "__main__":
    main()