#!/usr/bin/env python3
"""
Create visualization of themes from LLM thematic analysis.
"""

import json
import re
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def extract_themes_from_response():
    """Extract themes and frequencies from the LLM response."""
    with open("../outputs/anthropic_messages_response.json", "r") as f:
        response = json.load(f)
    
    content = response["content"]
    
    # Parse transit themes
    transit_section = content.split("2. CAR-PRIMARY COHORT THEMES")[0]
    transit_themes = []
    
    # Find all theme blocks in transit section
    # Updated pattern to handle the actual format
    theme_pattern = r'Theme \d+: ([^\n]+)\nDescription: ([^\n]+(?:\n[^\n]+)*?)\nRepresentative quotes:[^\n]+\nFrequency: Appears in (\d+)/9 responses \((\d+)%\)'
    
    for match in re.finditer(theme_pattern, transit_section, re.DOTALL):
        theme_name = match.group(1).strip()
        description = match.group(2).strip()
        count = int(match.group(3))
        percentage = int(match.group(4))
        
        transit_themes.append({
            "theme_name": theme_name,
            "description": description,
            "count": count,
            "percentage": percentage,
            "cohort": "transit_primary"
        })
    
    # Parse car themes
    car_section = content.split("2. CAR-PRIMARY COHORT THEMES")[1].split("3. COMPARATIVE ANALYSIS")[0]
    car_themes = []
    
    for match in re.finditer(theme_pattern, car_section, re.DOTALL):
        theme_name = match.group(1).strip()
        description = match.group(2).strip()
        count = int(match.group(3))
        percentage = int(match.group(4))
        
        car_themes.append({
            "theme_name": theme_name,
            "description": description,
            "count": count,
            "percentage": percentage,
            "cohort": "car_primary"
        })
    
    return transit_themes, car_themes

def create_theme_comparison_chart(transit_themes, car_themes):
    """Create a comparison chart of themes across cohorts."""
    # Combine all themes
    all_themes = transit_themes + car_themes
    
    # Prepare data for plotting
    theme_names = [t["theme_name"] for t in all_themes]
    counts = [t["count"] for t in all_themes]
    cohorts = [t["cohort"] for t in all_themes]
    
    # Create color mapping
    colors = ['#1f77b4' if c == 'transit_primary' else '#ff7f0e' for c in cohorts]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    bars = ax.barh(theme_names, counts, color=colors)
    ax.invert_yaxis()  # Highest count at top
    
    # Add count labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                f'{width}/9', ha='left', va='center', fontweight='bold')
    
    # Customize plot
    ax.set_xlabel('Number of Respondents Mentioning Theme (out of 9)', fontsize=12)
    ax.set_title('Thematic Analysis: Theme Prevalence by Cohort', fontsize=16, fontweight='bold')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#1f77b4', label='Transit-Primary Cohort'),
        Patch(facecolor='#ff7f0e', label='Car-Primary Cohort')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plt.savefig('../report/images/theme_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Created theme comparison chart with {len(all_themes)} themes")

def create_theme_summary_table(transit_themes, car_themes):
    """Create a summary table of themes and save as text."""
    os.makedirs("../outputs", exist_ok=True)
    
    with open("../outputs/theme_summary.txt", "w") as f:
        f.write("=== THEMATIC ANALYSIS SUMMARY ===\n\n")
        
        f.write("TRANSIT-PRIMARY COHORT THEMES:\n")
        f.write("="*50 + "\n")
        for i, theme in enumerate(transit_themes, 1):
            f.write(f"\nTheme {i}: {theme['theme_name']}\n")
            f.write(f"Description: {theme['description']}\n")
            f.write(f"Prevalence: {theme['count']}/9 respondents ({theme['percentage']}%)\n")
        
        f.write("\n\nCAR-PRIMARY COHORT THEMES:\n")
        f.write("="*50 + "\n")
        for i, theme in enumerate(car_themes, 1):
            f.write(f"\nTheme {i}: {theme['theme_name']}\n")
            f.write(f"Description: {theme['description']}\n")
            f.write(f"Prevalence: {theme['count']}/9 respondents ({theme['percentage']}%)\n")
        
        # Calculate summary statistics
        total_themes = len(transit_themes) + len(car_themes)
        avg_transit_prevalence = sum(t['percentage'] for t in transit_themes) / len(transit_themes) if transit_themes else 0
        avg_car_prevalence = sum(t['percentage'] for t in car_themes) / len(car_themes) if car_themes else 0
        
        f.write("\n\nSUMMARY STATISTICS:\n")
        f.write("="*50 + "\n")
        f.write(f"Total themes identified: {total_themes}\n")
        f.write(f"Transit-primary themes: {len(transit_themes)}\n")
        f.write(f"Car-primary themes: {len(car_themes)}\n")
        f.write(f"Average theme prevalence (transit): {avg_transit_prevalence:.1f}%\n")
        f.write(f"Average theme prevalence (car): {avg_car_prevalence:.1f}%\n")
    
    print("Theme summary saved to ../outputs/theme_summary.txt")

def main():
    """Main execution function."""
    print("Extracting themes from LLM response...")
    transit_themes, car_themes = extract_themes_from_response()
    
    print(f"Found {len(transit_themes)} transit themes and {len(car_themes)} car themes")
    
    print("Creating theme comparison visualization...")
    create_theme_comparison_chart(transit_themes, car_themes)
    
    print("Creating theme summary table...")
    create_theme_summary_table(transit_themes, car_themes)
    
    print("\n=== VISUALIZATION COMPLETE ===")
    print("Check report/images/theme_comparison.png for the chart")
    print("Check outputs/theme_summary.txt for the detailed summary")

if __name__ == "__main__":
    main()