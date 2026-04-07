import matplotlib.pyplot as plt
import numpy as np
import os

# Data from analysis
components = ['Purpose', 'Scope', 'Definitions', 'Responsibilities', 
              'Procedure', 'Temperature Excursion', 'Training', 'References', 'Revision History']
present = [1, 1, 1, 1, 1, 1, 1, 1, 1]  # All present

email_terms = ['logger', 'calibration', 'vendor', 'packaging', 'biologics', 'truck']
term_present = [1, 1, 1, 1, 1, 1]  # All present

# Create figure with subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Component completeness
colors1 = ['green' if p == 1 else 'red' for p in present]
ax1.barh(components, present, color=colors1)
ax1.set_xlabel('Presence (1 = Present)')
ax1.set_title('SOP Component Completeness')
ax1.set_xlim(0, 1.2)
for i, (comp, pres) in enumerate(zip(components, present)):
    ax1.text(pres + 0.05, i, f'{pres}/1', va='center')

# Email term coverage
colors2 = ['green' if p == 1 else 'red' for p in term_present]
ax2.barh(email_terms, term_present, color=colors2)
ax2.set_xlabel('Presence (1 = Present)')
ax2.set_title('Email Term Coverage in SOP')
ax2.set_xlim(0, 1.2)
for i, (term, pres) in enumerate(zip(email_terms, term_present)):
    ax2.text(pres + 0.05, i, f'{pres}/1', va='center')

plt.tight_layout()
plt.savefig('report/images/sop_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a pie chart for overall assessment
fig, ax = plt.subplots(1, 2, figsize=(10, 4))

# Components pie
component_labels = ['Present', 'Missing']
component_sizes = [9, 0]
component_colors = ['lightgreen', 'lightcoral']
ax[0].pie(component_sizes, labels=component_labels, colors=component_colors, autopct='%1.1f%%', startangle=90)
ax[0].set_title('SOP Components (9 total)')

# Terms pie
term_labels = ['Addressed', 'Missing']
term_sizes = [6, 0]
term_colors = ['lightblue', 'lightcoral']
ax[1].pie(term_sizes, labels=term_labels, colors=term_colors, autopct='%1.1f%%', startangle=90)
ax[1].set_title('Email Terms Addressed (6 total)')

plt.tight_layout()
plt.savefig('report/images/sop_pie_charts.png', dpi=300, bbox_inches='tight')
plt.close()

print("Visualizations created and saved to report/images/")