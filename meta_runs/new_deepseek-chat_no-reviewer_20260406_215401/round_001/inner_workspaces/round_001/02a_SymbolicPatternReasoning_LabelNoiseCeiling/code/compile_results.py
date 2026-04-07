import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Load all result files
results_files = [
    ('Basic Models', '../outputs/model_results.csv'),
    ('Engineered Features', '../outputs/engineered_features_results.csv'),
    ('Sequence Models', '../outputs/sequence_model_results.csv'),
    ('Rule-Based', '../outputs/rule_based_results.csv'),
    ('Final Models', '../outputs/final_results.csv')
]

all_results = []
for name, path in results_files:
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['Category'] = name
        all_results.append(df)

# Combine all results
if all_results:
    combined = pd.concat(all_results, ignore_index=True)
    
    # Reorder columns
    cols = ['Category', 'Model', 'Train Accuracy', 'Validation Accuracy', 'Test Accuracy']
    combined = combined[cols]
    
    print("ALL RESULTS SUMMARY")
    print("="*80)
    print(combined.to_string(index=False))
    
    # Save combined results
    combined.to_csv('../outputs/all_results_combined.csv', index=False)
    print("\nCombined results saved to outputs/all_results_combined.csv")
    
    # Calculate statistics
    sota_acc = 0.70
    print(f"\nSOTA Reference: {sota_acc:.2%}")
    print(f"Best test accuracy achieved: {combined['Test Accuracy'].max():.2%}")
    print(f"Average test accuracy: {combined['Test Accuracy'].mean():.2%}")
    print(f"Median test accuracy: {combined['Test Accuracy'].median():.2%}")
    
    # Models closest to SOTA
    combined['Diff from SOTA'] = combined['Test Accuracy'] - sota_acc
    combined_sorted = combined.sort_values('Test Accuracy', ascending=False)
    
    print("\nTop 10 models by test accuracy:")
    print(combined_sorted[['Category', 'Model', 'Test Accuracy', 'Diff from SOTA']].head(10).to_string(index=False))
    
    # Create summary visualization
    plt.figure(figsize=(14, 8))
    
    # Bar plot of all models
    ax = plt.subplot(2, 1, 1)
    models_sorted = combined.sort_values('Test Accuracy')
    bars = ax.barh(range(len(models_sorted)), models_sorted['Test Accuracy'])
    ax.axvline(x=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
    ax.set_yticks(range(len(models_sorted)))
    ax.set_yticklabels([f"{row['Category']}: {row['Model']}" for _, row in models_sorted.iterrows()])
    ax.set_xlabel('Test Accuracy')
    ax.set_title('All Models: Test Accuracy vs SOTA (70%)')
    ax.set_xlim(0, 1.0)
    ax.legend()
    
    # Add accuracy values on bars
    for i, (bar, acc) in enumerate(zip(bars, models_sorted['Test Accuracy'])):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{acc:.2%}', va='center')
    
    # Box plot by category
    ax2 = plt.subplot(2, 1, 2)
    categories = []
    accuracies = []
    for category in combined['Category'].unique():
        subset = combined[combined['Category'] == category]
        categories.append(category)
        accuracies.append(subset['Test Accuracy'].values)
    
    box = ax2.boxplot(accuracies, labels=categories, patch_artist=True)
    ax2.axhline(y=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
    ax2.set_ylabel('Test Accuracy')
    ax2.set_title('Test Accuracy Distribution by Model Category')
    ax2.set_ylim(0, 1.0)
    ax2.legend()
    
    # Color the boxes
    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
    
    plt.tight_layout()
    plt.savefig('../report/images/all_results_summary.png', dpi=300)
    print("\nSummary visualization saved to report/images/all_results_summary.png")
    
    # Create a simpler comparison chart
    plt.figure(figsize=(10, 6))
    
    # Get best model from each category
    best_by_category = []
    for category in combined['Category'].unique():
        subset = combined[combined['Category'] == category]
        best_idx = subset['Test Accuracy'].idxmax()
        best_by_category.append(combined.loc[best_idx])
    
    best_df = pd.DataFrame(best_by_category)
    best_df = best_df.sort_values('Test Accuracy')
    
    ax = sns.barplot(data=best_df, x='Test Accuracy', y='Category', hue='Model', dodge=False)
    plt.axvline(x=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
    plt.title('Best Model from Each Category vs SOTA')
    plt.xlabel('Test Accuracy')
    plt.xlim(0, 1.0)
    
    # Add accuracy values
    for i, (category, acc) in enumerate(zip(best_df['Category'], best_df['Test Accuracy'])):
        plt.text(acc + 0.01, i, f'{acc:.2%}', va='center')
    
    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig('../report/images/best_models_vs_sota.png', dpi=300)
    print("Best models comparison saved to report/images/best_models_vs_sota.png")

else:
    print("No result files found!")