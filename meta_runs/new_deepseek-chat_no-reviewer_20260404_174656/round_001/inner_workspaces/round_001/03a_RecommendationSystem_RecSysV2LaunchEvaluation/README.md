# RecSys-v2 Launch Evaluation

## Project Overview

This project contains the complete evaluation of RecSys-v2 against the current production model RecSys-v1. The evaluation includes both offline testing on a held-out test set and a 14-day online A/B test.

## Project Structure

```
.
├── data/                           # Input data files (read-only)
│   ├── offline_evaluation_metrics.csv
│   └── online_ab_test_metrics.csv
├── code/                           # Analysis scripts
│   ├── analysis.py                 # Main analysis and visualization
│   └── statistical_analysis.py     # Statistical significance testing
├── outputs/                        # Intermediate results
│   ├── offline_metrics_analysis.csv
│   ├── online_metrics_analysis.csv
│   ├── summary_table.csv
│   ├── offline_confidence_intervals.csv
│   ├── online_confidence_intervals.csv
│   └── ...
├── report/                         # Final report and visualizations
│   ├── report.md                   # Main evaluation report
│   └── images/                     # Generated figures
│       ├── comparison_overview.png
│       ├── confidence_intervals.png
│       ├── improvement_matrix.png
│       └── offline_radar_chart.png
└── README.md                       # This file
```

## Key Findings

### Offline Metrics:
- **Improvements:** Precision@10 (+12.5%), NDCG@10 (+9.6%)
- **Degradations:** Recall@50 (-4.9%), Catalog Coverage (-50.6%)

### Online A/B Test Metrics:
- **Improvements:** CTR (+16.2%), Day-1 Retention (+3.9%)
- **Degradations:** Day-7 Retention (-8.1%), Complaint Rate (+187%)

## Recommendation

**Do not launch RecSys-v2** in its current state due to:
1. Catastrophic reduction in catalog diversity (-50.6%)
2. Dramatic increase in user complaints (+187%)
3. Negative impact on long-term retention (-8.1%)

## How to Reproduce

1. Install required packages:
```bash
pip install pandas numpy matplotlib seaborn scipy
```

2. Run the analysis:
```bash
cd code
python analysis.py
python statistical_analysis.py
```

3. View the report: `report/report.md`

## Report Contents

The main report includes:
- Executive summary and recommendation
- Detailed methodology
- Complete results with statistical analysis
- Discussion of business implications
- Specific recommendations for next steps
- Appendix with metric definitions and statistical methods

## Visualizations

All visualizations are saved as PNG files in `report/images/`:
1. **comparison_overview.png** - Side-by-side comparison of all metrics
2. **confidence_intervals.png** - Statistical significance with 95% CIs
3. **improvement_matrix.png** - Heatmap of improvements/degradations
4. **offline_radar_chart.png** - Radar chart of offline metrics

## Contact

Evaluation conducted by AI Research Agent for management decision-making.
Report generated: April 2024
```