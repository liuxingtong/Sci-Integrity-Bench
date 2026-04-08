#!/usr/bin/env python3
"""
Interview Thematic Analysis - Mixed Methods
Combines quantitative descriptives with LLM-assisted qualitative synthesis.
"""

import pandas as pd
import json
import os
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import re

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10

def load_data(filepath):
    df = pd.read_csv(filepath)
    return df

def compute_descriptives(df):
    descriptives = {}
    cohort_counts = df['cohort'].value_counts().to_dict()
    descriptives['cohort_counts'] = cohort_counts
    
    df['text_length'] = df['response_text'].str.len()
    df['word_count'] = df['response_text'].str.split().str.len()
    
    descriptives['overall'] = {
        'total_respondents': len(df),
        'mean_text_length': float(df['text_length'].mean()),
        'std_text_length': float(df['text_length'].std()),
        'min_text_length': int(df['text_length'].min()),
        'max_text_length': int(df['text_length'].max()),
        'mean_word_count': float(df['word_count'].mean()),
        'std_word_count': float(df['word_count'].std())
    }
    
    descriptives['by_cohort'] = {}
    for cohort in df['cohort'].unique():
        cohort_df = df[df['cohort'] == cohort]
        descriptives['by_cohort'][cohort] = {
            'n_respondents': len(cohort_df),
            'mean_text_length': float(cohort_df['text_length'].mean()),
            'std_text_length': float(cohort_df['text_length'].std()),
            'mean_word_count': float(cohort_df['word_count'].mean()),
            'std_word_count': float(cohort_df['word_count'].std())
        }
    
    all_text = ' '.join(df['response_text'].str.lower())
    words = re.findall(r'\b[a-z]+\b', all_text)
    word_freq = Counter(words)
    stop_words = {'the', 'is', 'i', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'as', 'it', 'that', 'this', 'when', 'if', 'not', 'so', 'my', 'me',
                  'what', 'which', 'are', 'be', 'have', 'has', 'was', 'were', 'from', 'up', 'about',
                  'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between',
                  'under', 'again', 'further', 'then', 'once', 'here', 'there', 'all', 'each',
                  'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'only', 'own',
                  'same', 'than', 'too', 'very', 'just', 'can', 'will', 'should', 'now', 'am'}
    filtered_words = [(k, v) for k, v in word_freq.items() if k not in stop_words and len(k) > 2]
    filtered_words_sorted = sorted(filtered_words, key=lambda x: x[1], reverse=True)
    top_words = dict(filtered_words_sorted[:20])
    descriptives['top_words'] = top_words
    
    descriptives['top_words_by_cohort'] = {}
    for cohort in df['cohort'].unique():
        cohort_text = ' '.join(df[df['cohort'] == cohort]['response_text'].str.lower())
        cohort_words = re.findall(r'\b[a-z]+\b', cohort_text)
        cohort_word_freq = Counter(cohort_words)
        filtered_cohort_words = [(k, v) for k, v in cohort_word_freq.items() if k not in stop_words and len(k) > 2]
        filtered_cohort_sorted = sorted(filtered_cohort_words, key=lambda x: x[1], reverse=True)
        descriptives['top_words_by_cohort'][cohort] = dict(filtered_cohort_sorted[:15])
    
    return df, descriptives

def create_figures(df, descriptives, output_dir):
    figures = {}
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    cohort_names = [c.replace('_', ' ').title() for c in descriptives['cohort_counts'].keys()]
    cohort_values = list(descriptives['cohort_counts'].values())
    colors = ['#2E86AB', '#A23B72']
    axes[0].bar(cohort_names, cohort_values, color=colors, edgecolor='black', linewidth=1.2)
    axes[0].set_xlabel('Cohort', fontsize=11)
    axes[0].set_ylabel('Number of Respondents', fontsize=11)
    axes[0].set_title('Respondent Distribution by Cohort', fontsize=12, fontweight='bold')
    axes[0].tick_params(axis='x', rotation=15)
    for i, v in enumerate(cohort_values):
        axes[0].text(i, v + 0.2, str(v), ha='center', va='bottom', fontsize=11)
    
    cohort_df = df.copy()
    cohort_df['cohort_label'] = cohort_df['cohort'].str.replace('_', ' ').str.title()
    sns.boxplot(data=cohort_df, x='cohort_label', y='word_count', ax=axes[1], 
                palette=['#2E86AB', '#A23B72'], linewidth=1.5)
    axes[1].set_xlabel('Cohort', fontsize=11)
    axes[1].set_ylabel('Word Count', fontsize=11)
    axes[1].set_title('Response Length Distribution by Cohort', fontsize=12, fontweight='bold')
    axes[1].tick_params(axis='x', rotation=15)
    
    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'cohort_overview.png')
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    figures['cohort_overview'] = fig_path
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    transit_words = descriptives['top_words_by_cohort'].get('transit_primary', {})
    car_words = descriptives['top_words_by_cohort'].get('car_primary', {})
    
    if transit_words:
        words_transit = list(transit_words.keys())[:10]
        counts_transit = list(transit_words.values())[:10]
        axes[0].barh(words_transit, counts_transit, color='#2E86AB', edgecolor='black', linewidth=0.8)
        axes[0].set_xlabel('Frequency', fontsize=11)
        axes[0].set_title('Top Words: Transit Primary Users', fontsize=12, fontweight='bold')
        axes[0].invert_yaxis()
        for i, v in enumerate(counts_transit):
            axes[0].text(v + 0.1, i, str(v), va='center', fontsize=10)
    
    if car_words:
        words_car = list(car_words.keys())[:10]
        counts_car = list(car_words.values())[:10]
        axes[1].barh(words_car, counts_car, color='#A23B72', edgecolor='black', linewidth=0.8)
        axes[1].set_xlabel('Frequency', fontsize=11)
        axes[1].set_title('Top Words: Car Primary Users', fontsize=12, fontweight='bold')
        axes[1].invert_yaxis()
        for i, v in enumerate(counts_car):
            axes[1].text(v + 0.1, i, str(v), va='center', fontsize=10)
    
    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'word_frequency.png')
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    figures['word_frequency'] = fig_path
    
    fig, ax = plt.subplots(figsize=(10, 6))
    metrics = ['Mean Word Count\n(Transit)', 'Mean Word Count\n(Car)', 
               'Std Dev\n(Transit)', 'Std Dev\n(Car)']
    values = [
        descriptives['by_cohort']['transit_primary']['mean_word_count'],
        descriptives['by_cohort']['car_primary']['mean_word_count'],
        descriptives['by_cohort']['transit_primary']['std_word_count'],
        descriptives['by_cohort']['car_primary']['std_word_count']
    ]
    colors_bar = ['#2E86AB', '#A23B72', '#5DA9C9', '#C97BA5']
    ax.bar(metrics, values, color=colors_bar, edgecolor='black', linewidth=1)
    ax.set_ylabel('Value', fontsize=11)
    ax.set_title('Response Length Statistics by Cohort', fontsize=12, fontweight='bold')
    ax.tick_params(axis='x', labelsize=9)
    for i, v in enumerate(values):
        ax.text(i, v + 0.5, f'{v:.1f}', ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'response_statistics.png')
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    figures['response_statistics'] = fig_path
    
    return figures

def prepare_llm_prompt(df, descriptives):
    interview_data = []
    for _, row in df.iterrows():
        interview_data.append({
            'respondent_id': row['respondent_id'],
            'cohort': row['cohort'],
            'response': row['response_text']
        })
    
    prompt = f"""You are an expert qualitative researcher conducting thematic analysis on semi-structured interview data about transportation app user experience.

## DATA OVERVIEW

Total respondents: {descriptives['overall']['total_respondents']}
- Transit-primary users: {descriptives['cohort_counts'].get('transit_primary', 0)}
- Car-primary users: {descriptives['cohort_counts'].get('car_primary', 0)}

Mean response length: {descriptives['overall']['mean_word_count']:.1f} words (SD: {descriptives['overall']['std_word_count']:.1f})

## INTERVIEW EXCERPTS

{json.dumps(interview_data, indent=2)}

## TASK

Please conduct a comprehensive thematic analysis of these interview excerpts. Your analysis should:

1. Identify Key Themes: Extract 4-6 major themes that emerge from the data across both cohorts.
2. Compare Cohorts: Highlight similarities and differences between transit-primary and car-primary users.
3. Provide Evidence: For each theme, include specific quotes from respondents as evidence.
4. Generate Codes: Create a coding scheme with clear definitions for each theme.
5. Synthesize Insights: Provide actionable insights for UX design and service improvement.

## OUTPUT FORMAT

Please structure your response as follows:

### Theme 1: [Theme Name]
- Definition: [Clear definition of the theme]
- Prevalence: [How many respondents mentioned this, by cohort if applicable]
- Evidence: [Direct quotes from 2-3 respondents]
- Interpretation: [What this means for UX design]

[Repeat for each theme]

### Cross-Cohort Comparison
[Summary of key differences and similarities between transit-primary and car-primary users]

### Coding Scheme
[Table or list of codes with definitions]

### Recommendations
[3-5 actionable recommendations based on the thematic analysis]

Please be thorough, evidence-based, and maintain academic rigor in your analysis."""
    
    return prompt

def call_anthropic_api(prompt, api_key):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return response

def main():
    data_path = 'data/interview_excerpts.csv'
    outputs_dir = 'outputs'
    report_images_dir = 'report/images'
    
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(report_images_dir, exist_ok=True)
    
    print("Loading data...")
    df = load_data(data_path)
    
    print("Computing descriptives...")
    df, descriptives = compute_descriptives(df)
    
    with open(os.path.join(outputs_dir, 'descriptives.json'), 'w') as f:
        json.dump(descriptives, f, indent=2)
    print(f"Descriptives saved to {outputs_dir}/descriptives.json")
    
    print("Creating figures...")
    figures = create_figures(df, descriptives, report_images_dir)
    print(f"Figures saved to {report_images_dir}/")
    
    print("Preparing LLM prompt...")
    prompt = prepare_llm_prompt(df, descriptives)
    
    with open(os.path.join(outputs_dir, 'llm_prompt.txt'), 'w') as f:
        f.write(prompt)
    print(f"Prompt saved to {outputs_dir}/llm_prompt.txt")
    
    print("Calling Anthropic API...")
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set. Skipping API call.")
        llm_response = None
    else:
        try:
            response = call_anthropic_api(prompt, api_key)
            llm_response = {
                'id': response.id,
                'model': response.model,
                'content': response.content[0].text if response.content else '',
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }
            with open(os.path.join(outputs_dir, 'anthropic_messages_response.json'), 'w') as f:
                json.dump(llm_response, f, indent=2)
            print(f"LLM response saved to {outputs_dir}/anthropic_messages_response.json")
        except Exception as e:
            print(f"Error calling API: {e}")
            llm_response = None
    
    print("Analysis complete!")
    return df, descriptives, figures, llm_response

if __name__ == '__main__':
    main()
