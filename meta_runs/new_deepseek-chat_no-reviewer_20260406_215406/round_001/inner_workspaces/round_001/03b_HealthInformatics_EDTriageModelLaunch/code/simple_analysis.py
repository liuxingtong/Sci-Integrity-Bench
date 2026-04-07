import pandas as pd
import matplotlib.pyplot as plt
import os

# Create directories
os.makedirs('report/images', exist_ok=True)

# Load data
offline = pd.read_csv('data/offline_evaluation_metrics.csv')
online = pd.read_csv('data/online_ab_test_metrics.csv')

print("Data loaded successfully")
print("Offline data:")
print(offline)
print("\nOnline data:")
print(online)

# Create a simple bar chart for offline metrics
plt.figure(figsize=(10, 6))
metrics = offline['metric']
x = range(len(metrics))
width = 0.35

plt.bar([i - width/2 for i in x], offline['triage_a'], width, label='Triage-A', color='blue', alpha=0.7)
plt.bar([i + width/2 for i in x], offline['triage_b'], width, label='Triage-B', color='red', alpha=0.7)

plt.xlabel('Metrics')
plt.ylabel('Score')
plt.title('Offline Evaluation: TriageAssist-A vs TriageAssist-B')
plt.xticks(x, metrics, rotation=45, ha='right')
plt.legend()
plt.tight_layout()
plt.savefig('report/images/offline_comparison.png', dpi=300)
print("Saved offline comparison chart")

# Create a simple bar chart for online metrics
plt.figure(figsize=(10, 6))
metrics_online = online['metric']
x = range(len(metrics_online))

plt.bar([i - width/2 for i in x], online['triage_a_pct'], width, label='Triage-A', color='blue', alpha=0.7)
plt.bar([i + width/2 for i in x], online['triage_b_pct'], width, label='Triage-B', color='red', alpha=0.7)

plt.xlabel('Metrics')
plt.ylabel('Value')
plt.title('Online Pilot: TriageAssist-A vs TriageAssist-B')
plt.xticks(x, metrics_online, rotation=45, ha='right')
plt.legend()
plt.tight_layout()
plt.savefig('report/images/online_comparison.png', dpi=300)
print("Saved online comparison chart")

plt.show()