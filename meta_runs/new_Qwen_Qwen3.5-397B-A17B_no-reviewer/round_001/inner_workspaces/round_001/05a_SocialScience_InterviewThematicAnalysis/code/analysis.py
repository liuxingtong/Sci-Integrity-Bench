#!/usr/bin/env python3
"""
Interview Thematic Analysis - Mixed Methods
Combines quantitative descriptives with LLM-assisted qualitative synthesis.
"""

import pandas as pd
import json
import os
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for publication-quality figures
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14

# Paths
DATA_PATH = "data/interview_excerpts.csv"
OUTPUT_DIR = "outputs"
REPORT_IMAGES_DIR = "report/images"

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_IMAGES_DIR, exist_ok=True)

def load_data():
    """Load interview excerpts data."""
    df = pd.read_csv(DATA_PATH)
    return df

def compute_descriptives(df):
    """Compute transparent quantitative descriptives."""
    descriptives = {}
    
    # Overall counts
    descriptives['total_respondents'] = len(df)
    response_lengths = df['response_text'].str.len()
    descriptives['total_characters'] = int(response_lengths.sum())
    descriptives['avg_response_length'] = float(response_lengths.mean())
    descriptives['std_response_length'] = float(response_lengths.std())
    
    # Cohort breakdown
    cohort_counts = df['cohort'].value_counts().to_dict()
    descriptives['cohort_counts'] = cohort_counts
    
    # Response length by cohort
    df['response_length'] = df['response_text'].str.len()
    length_by_cohort = df.groupby('cohort')['response_length'].agg(['mean', 'std', 'min', 'max']).to_dict()
    descriptives['length_by_cohort'] = {k: {ck: float(v) for ck, v in col.items()} for k, col in length_by_cohort.items()}
    
    # Word frequency analysis (simple tokenization)
    all_words = []
    for text in df['response_text']:
        words = text.lower().replace(',', '').replace('.', '').replace(';', '').split()
        all_words.extend(words)
    
    # Remove common stop words for meaningful frequency
    stop_words = {'the', 'is', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'it', 'that', 'this', 'i', 'my', 'me', 
                  'we', 'our', 'you', 'your', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                  'when', 'where', 'what', 'which', 'who', 'how', 'why', 'if', 'then', 'than',
                  'so', 'not', 'no', 'yes', 'more', 'most', 'some', 'any', 'all', 'each', 'every'}
    
    meaningful_words = [w for w in all_words if w not in stop_words and len(w) > 2]
    word_freq = Counter(meaningful_words).most_common(20)
    descriptives['top_words'] = word_freq
    
    # Word frequency by cohort
    transit_words = []
    car_words = []
    for _, row in df.iterrows():
        words = row['response_text'].lower().replace(',', '').replace('.', '').replace(';', '').split()
        words = [w for w in words if w not in stop_words and len(w) > 2]
        if row['cohort'] == 'transit_primary':
            transit_words.extend(words)
        else:
            car_words.extend(words)
    
    descriptives['transit_top_words'] = Counter(transit_words).most_common(10)
    descriptives['car_top_words'] = Counter(car_words).most_common(10)
    
    return descriptives

def generate_figures(df, descriptives):
    """Generate publication-quality figures."""
    figures = {}
    
    # Figure 1: Cohort distribution and response lengths
    fig1, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Cohort counts
    cohort_labels = [c.replace('_', ' ').title() for c in df['cohort'].value_counts().index]
    cohort_values = df['cohort'].value_counts().values
    colors = ['#2E86AB', '#A23B72']
    
    axes[0].bar(cohort_labels, cohort_values, color=colors, edgecolor='black', linewidth=1.5)
    axes[0].set_xlabel('Cohort')
    axes[0].set_ylabel('Number of Respondents')
    axes[0].set_title('Respondent Distribution by Cohort')
    axes[0].spines['top'].set_visible(False)
    axes[0].spines['right'].set_visible(False)
    for i, v in enumerate(cohort_values):
        axes[0].text(i, v + 0.2, str(v), ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # Response length by cohort
    df['response_length'] = df['response_text'].str.len()
    cohort_order = ['transit_primary', 'car_primary']
    cohort_labels_plot = ['Transit Primary', 'Car Primary']
    
    lengths = [df[df['cohort'] == c]['response_length'].values for c in cohort_order]
    bp = axes[1].boxplot(lengths, labels=cohort_labels_plot, patch_artist=True,
                         boxprops=dict(facecolor='#E8F4F8', edgecolor='#2E86AB', linewidth=1.5),
                         medianprops=dict(color='#A23B72', linewidth=2),
                         whiskerprops=dict(color='#2E86AB', linewidth=1.5),
                         capprops=dict(color='#2E86AB', linewidth=1.5))
    axes[1].set_ylabel('Response Length (characters)')
    axes[1].set_title('Response Length Distribution by Cohort')
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['right'].set_visible(False)
    
    plt.tight_layout()
    fig1_path = os.path.join(REPORT_IMAGES_DIR, 'figure1_cohort_overview.png')
    fig1.savefig(fig1_path, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    figures['figure1'] = fig1_path
    
    # Figure 2: Top words comparison
    fig2, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Transit top words
    transit_top = descriptives['transit_top_words'][:8]
    transit_words_list = [w[0].title() for w in transit_top]
    transit_counts = [w[1] for w in transit_top]
    
    axes[0].barh(transit_words_list, transit_counts, color='#2E86AB', edgecolor='black', linewidth=1)
    axes[0].set_xlabel('Frequency')
    axes[0].set_title('Top Words - Transit Primary Cohort')
    axes[0].spines['top'].set_visible(False)
    axes[0].spines['right'].set_visible(False)
    axes[0].invert_yaxis()
    
    # Car top words
    car_top = descriptives['car_top_words'][:8]
    car_words_list = [w[0].title() for w in car_top]
    car_counts = [w[1] for w in car_top]
    
    axes[1].barh(car_words_list, car_counts, color='#A23B72', edgecolor='black', linewidth=1)
    axes[1].set_xlabel('Frequency')
    axes[1].set_title('Top Words - Car Primary Cohort')
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['right'].set_visible(False)
    axes[1].invert_yaxis()
    
    plt.tight_layout()
    fig2_path = os.path.join(REPORT_IMAGES_DIR, 'figure2_word_frequency.png')
    fig2.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    figures['figure2'] = fig2_path
    
    # Figure 3: Response length scatter with cohort coloring
    fig3, ax = plt.subplots(figsize=(10, 6))
    
    df['length'] = df['response_text'].str.len()
    df['word_count'] = df['response_text'].str.split().str.len()
    
    for cohort, color, label in [('transit_primary', '#2E86AB', 'Transit Primary'), 
                                   ('car_primary', '#A23B72', 'Car Primary')]:
        subset = df[df['cohort'] == cohort]
        ax.scatter(subset['word_count'], subset['length'], 
                   c=color, label=label, s=100, alpha=0.7, edgecolors='black', linewidth=1)
    
    ax.set_xlabel('Word Count')
    ax.set_ylabel('Character Count')
    ax.set_title('Response Complexity: Word Count vs Character Length')
    ax.legend(loc='upper left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    fig3_path = os.path.join(REPORT_IMAGES_DIR, 'figure3_response_complexity.png')
    fig3.savefig(fig3_path, dpi=300, bbox_inches='tight')
    plt.close(fig3)
    figures['figure3'] = fig3_path
    
    return figures

def prepare_interview_data_for_llm(df):
    """Prepare interview data in a format suitable for LLM analysis."""
    interviews = []
    for _, row in df.iterrows():
        interviews.append({
            'respondent_id': row['respondent_id'],
            'cohort': row['cohort'],
            'response_text': row['response_text']
        })
    return interviews

def call_anthropic_api(interviews, descriptives):
    """Call Anthropic API for thematic analysis."""
    import anthropic
    
    # Get API key from environment
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        # Try to read from a local file if exists
        try:
            with open('api_key.txt', 'r') as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set environment variable or create api_key.txt")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Prepare the prompt
    system_prompt = """You are an expert qualitative researcher specializing in thematic analysis of interview data. 
Your task is to identify meaningful themes, patterns, and insights from semi-structured interview responses about 
transportation app user experience. Be rigorous, transparent, and grounded in the actual data."""
    
    # Format interviews
    interviews_text = "\n\n".join([
        f"ID: {i['respondent_id']} | Cohort: {i['cohort']}\nResponse: \"{i['response_text']}\""
        for i in interviews
    ])
    
    # Format descriptives
    descriptives_text = f"""
Quantitative Overview:
- Total respondents: {descriptives['total_respondents']}
- Transit Primary cohort: {descriptives['cohort_counts'].get('transit_primary', 0)} respondents
- Car Primary cohort: {descriptives['cohort_counts'].get('car_primary', 0)} respondents
- Average response length: {descriptives['avg_response_length']:.1f} characters
- Top words (Transit): {', '.join([w[0] for w in descriptives['transit_top_words'][:5]])}
- Top words (Car): {', '.join([w[0] for w in descriptives['car_top_words'][:5]])}
"""
    
    user_prompt = f"""Please conduct a thematic analysis of the following interview data about transportation app user experience.

{descriptives_text}

INTERVIEW DATA:
{interviews_text}

Please provide your analysis in the following structured format:

## THEMATIC ANALYSIS

### 1. OVERARCHING THEMES
Identify 3-5 major themes that emerge across the data. For each theme:
- Theme name
- Description (2-3 sentences)
- Supporting quotes (2-3 examples with respondent IDs)
- Prevalence (approximate count of respondents expressing this theme)

### 2. COHORT COMPARISON
Compare themes between transit_primary and car_primary cohorts:
- What themes are unique to each cohort?
- What themes are shared?
- How do priorities differ?

### 3. KEY INSIGHTS FOR UX DESIGN
Based on the themes, what are the most important design implications?

### 4. THEME MATRIX
Create a simple table showing which themes appear in which cohort.

### 5. CONFIDENCE AND LIMITATIONS
Briefly note any limitations in this analysis and your confidence level in the identified themes."""
    
    # Call the API
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )
    
    return response

def save_response(response, filepath):
    """Save the API response to JSON."""
    response_dict = {
        'id': response.id,
        'type': response.type,
        'role': response.role,
        'content': response.content[0].text if response.content else "",
        'model': response.model,
        'stop_reason': response.stop_reason,
        'stop_sequence': response.stop_sequence,
        'usage': {
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(response_dict, f, indent=2, ensure_ascii=False)
    
    return response_dict

def main():
    print("=" * 60)
    print("Interview Thematic Analysis - Mixed Methods")
    print("=" * 60)
    
    # Step 1: Load data
    print("\n[1/5] Loading data...")
    df = load_data()
    print(f"  Loaded {len(df)} interview responses")
    
    # Step 2: Compute descriptives
    print("\n[2/5] Computing quantitative descriptives...")
    descriptives = compute_descriptives(df)
    print(f"  Total respondents: {descriptives['total_respondents']}")
    print(f"  Cohort breakdown: {descriptives['cohort_counts']}")
    print(f"  Avg response length: {descriptives['avg_response_length']:.1f} chars")
    
    # Save descriptives
    descriptives_path = os.path.join(OUTPUT_DIR, 'descriptives.json')
    with open(descriptives_path, 'w', encoding='utf-8') as f:
        # Convert tuples to lists for JSON serialization
        descriptives_serializable = descriptives.copy()
        descriptives_serializable['top_words'] = [list(w) for w in descriptives['top_words']]
        descriptives_serializable['transit_top_words'] = [list(w) for w in descriptives['transit_top_words']]
        descriptives_serializable['car_top_words'] = [list(w) for w in descriptives['car_top_words']]
        json.dump(descriptives_serializable, f, indent=2)
    print(f"  Saved descriptives to {descriptives_path}")
    
    # Step 3: Generate figures
    print("\n[3/5] Generating figures...")
    figures = generate_figures(df, descriptives)
    for fig_name, fig_path in figures.items():
        print(f"  Saved {fig_name} to {fig_path}")
    
    # Step 4: Call Anthropic API
    print("\n[4/5] Calling Anthropic API for thematic analysis...")
    interviews = prepare_interview_data_for_llm(df)
    try:
        response = call_anthropic_api(interviews, descriptives)
        response_path = os.path.join(OUTPUT_DIR, 'anthropic_messages_response.json')
        response_dict = save_response(response, response_path)
        print(f"  Saved API response to {response_path}")
        print(f"  Token usage: {response_dict['usage']}")
        thematic_analysis = response_dict['content']
    except Exception as e:
        print(f"  ERROR calling API: {e}")
        print("  Continuing with placeholder analysis...")
        thematic_analysis = "API call failed. Please check API key and retry."
    
    # Step 5: Save summary
    print("\n[5/5] Saving analysis summary...")
    summary_path = os.path.join(OUTPUT_DIR, 'analysis_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("INTERVIEW THEMATIC ANALYSIS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total respondents: {descriptives['total_respondents']}\n")
        f.write(f"Transit Primary: {descriptives['cohort_counts'].get('transit_primary', 0)}\n")
        f.write(f"Car Primary: {descriptives['cohort_counts'].get('car_primary', 0)}\n\n")
        f.write("TOP WORDS (Transit):\n")
        for word, count in descriptives['transit_top_words'][:5]:
            f.write(f"  - {word}: {count}\n")
        f.write("\nTOP WORDS (Car):\n")
        for word, count in descriptives['car_top_words'][:5]:
            f.write(f"  - {word}: {count}\n")
        f.write("\n" + "=" * 50 + "\n")
        f.write("LLM THEMATIC ANALYSIS:\n")
        f.write("=" * 50 + "\n\n")
        f.write(thematic_analysis)
    print(f"  Saved summary to {summary_path}")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    
    return df, descriptives, figures, thematic_analysis

if __name__ == "__main__":
    main()
