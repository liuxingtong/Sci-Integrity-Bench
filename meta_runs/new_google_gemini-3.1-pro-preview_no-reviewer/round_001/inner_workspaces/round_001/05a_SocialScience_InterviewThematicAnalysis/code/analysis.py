import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import anthropic

# 1. Preprocessing and Descriptive Stats
df = pd.read_csv('data/interview_excerpts.csv')

# Calculate response lengths (word count)
df['word_count'] = df['response_text'].apply(lambda x: len(str(x).split()))

# Cohort counts
cohort_counts = df['cohort'].value_counts()
print("Cohort Counts:")
print(cohort_counts)

# Length stats by cohort
length_stats = df.groupby('cohort')['word_count'].describe()
print("\nLength Stats by Cohort:")
print(length_stats)

# Save descriptive stats to outputs
cohort_counts.to_csv('outputs/cohort_counts.csv')
length_stats.to_csv('outputs/length_stats.csv')

# Generate Figure 1: Word Count Distribution by Cohort
plt.figure(figsize=(8, 6))
sns.boxplot(x='cohort', y='word_count', data=df)
plt.title('Response Word Count Distribution by Cohort')
plt.xlabel('Cohort')
plt.ylabel('Word Count')
plt.tight_layout()
plt.savefig('report/images/word_count_boxplot.png')
plt.close()

# Generate Figure 2: Word Count Histogram
plt.figure(figsize=(8, 6))
sns.histplot(data=df, x='word_count', hue='cohort', multiple='stack', bins=10)
plt.title('Response Word Count Histogram')
plt.xlabel('Word Count')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig('report/images/word_count_histogram.png')
plt.close()

# 2. Anthropic API for Thematic Analysis
# Prepare the prompt
responses_text = ""
for index, row in df.iterrows():
    responses_text += f"Respondent ID: {row['respondent_id']}\nCohort: {row['cohort']}\nResponse: {row['response_text']}\n\n"

prompt = f"""You are an expert qualitative researcher. I have provided interview excerpts from two cohorts: 'transit_primary' and 'car_primary'.

Please perform a thematic analysis on these excerpts. Identify the main themes for each cohort, and any overlapping themes. 
For each theme, provide a brief description and cite relevant Respondent IDs.

Interview Excerpts:
{responses_text}
"""

import openai
client = openai.OpenAI(
    base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ.get("OPENROUTER_API_KEY")
)

response = client.chat.completions.create(
    model=os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
    max_tokens=4000,
    temperature=0.2,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

# Save full response to outputs/anthropic_messages_response.json
response_dict = response.model_dump()
with open('outputs/anthropic_messages_response.json', 'w') as f:
    json.dump(response_dict, f, indent=2)

print("\nThematic analysis complete. Response saved.")
