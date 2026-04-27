import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from anthropic import Anthropic

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

# Save descriptive stats to a JSON for reporting
stats = {
    'cohort_counts': cohort_counts.to_dict(),
    'length_stats': length_stats.to_dict(orient='index')
}
with open('outputs/descriptive_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

# Generate Figure: Word Count Distribution by Cohort
plt.figure(figsize=(8, 6))
sns.boxplot(x='cohort', y='word_count', data=df)
plt.title('Response Word Count Distribution by Cohort')
plt.xlabel('Cohort')
plt.ylabel('Word Count')
plt.savefig('report/images/word_count_boxplot.png')
plt.close()

# Generate Figure: Word Count Histogram
plt.figure(figsize=(8, 6))
sns.histplot(data=df, x='word_count', hue='cohort', multiple='stack', bins=10)
plt.title('Response Word Count Histogram')
plt.xlabel('Word Count')
plt.ylabel('Frequency')
plt.savefig('report/images/word_count_histogram.png')
plt.close()

# 2. Anthropic API for Thematic Analysis
# Prepare the prompt
responses_text = ""
for index, row in df.iterrows():
    responses_text += f"Respondent ID: {row['respondent_id']}\nCohort: {row['cohort']}\nResponse: {row['response_text']}\n\n"

prompt = f"""You are an expert qualitative researcher. Please perform a thematic analysis on the following interview excerpts from two cohorts: transit_primary and car_primary.

Interview Excerpts:
{responses_text}

Please provide:
1. Key themes identified across all responses.
2. Specific themes or concerns unique to the 'transit_primary' cohort.
3. Specific themes or concerns unique to the 'car_primary' cohort.
4. A brief summary of the overall user experience issues highlighted by the respondents.

Format your response clearly with headings."""

client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', 'dummy_key'))

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2000,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

# Save full response
with open('outputs/anthropic_messages_response.json', 'w') as f:
    json.dump(response.model_dump(), f, indent=2)

print("Analysis complete. Outputs saved.")
