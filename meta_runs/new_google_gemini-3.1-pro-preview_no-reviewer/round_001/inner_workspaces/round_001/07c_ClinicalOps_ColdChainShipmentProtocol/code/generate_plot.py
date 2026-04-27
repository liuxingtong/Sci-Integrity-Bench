import matplotlib.pyplot as plt
import os

# Create directories if they don't exist
os.makedirs('report/images', exist_ok=True)

# Data for the plot
sections = ['Purpose', 'Scope', 'Responsibilities', 'Procedure', 'References']
word_counts = [19, 20, 33, 43, 11]

# Create the plot
plt.figure(figsize=(8, 5))
plt.bar(sections, word_counts, color='skyblue')
plt.xlabel('SOP Sections')
plt.ylabel('Word Count')
plt.title('Word Count per Section in Cold-Chain SOP')
plt.tight_layout()

# Save the plot
plt.savefig('report/images/sop_structure.png')
print('Plot saved to report/images/sop_structure.png')
