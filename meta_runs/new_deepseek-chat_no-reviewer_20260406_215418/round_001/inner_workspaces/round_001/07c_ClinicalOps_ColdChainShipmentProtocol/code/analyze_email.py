import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os

# Read the email draft
with open('data/email_thread_draft.txt', 'r') as f:
    text = f.read()

print("Email content:")
print(text)
print("\n" + "="*50 + "\n")

# Basic text analysis
words = re.findall(r'\b\w+\b', text.lower())
word_counts = Counter(words)

print("Word frequencies:")
for word, count in word_counts.most_common():
    print(f"{word}: {count}")

# Generate word cloud
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

# Save figure
os.makedirs('report/images', exist_ok=True)
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Word Cloud of Email Draft')
plt.savefig('report/images/wordcloud.png', dpi=300, bbox_inches='tight')
plt.close()

# Create bar chart of top words
top_words = word_counts.most_common(5)
words, counts = zip(*top_words)

plt.figure(figsize=(8, 4))
plt.bar(words, counts, color='skyblue')
plt.xlabel('Words')
plt.ylabel('Frequency')
plt.title('Top 5 Words in Email Draft')
plt.savefig('report/images/word_frequencies.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nAnalysis complete. Figures saved to report/images/")