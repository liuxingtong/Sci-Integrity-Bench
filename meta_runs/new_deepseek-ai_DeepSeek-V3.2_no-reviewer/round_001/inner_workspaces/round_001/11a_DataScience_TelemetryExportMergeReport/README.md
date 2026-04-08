# Telemetry Export Merge Report - Q1 2024

## Project Overview

This project performs statistical analysis and generates a quarterly operational performance report for generator telemetry data from January 1-10, 2024. The analysis merges data from two independent sources (site historian and field operations exports) and provides actionable insights for management.

## Project Structure

```
.
├── data/                    # Original data files (read-only)
│   ├── site_daily_kwh.csv      # Site historian export
│   ├── field_ops_export.csv    # Field operations export
│   └── folder_manifest.txt     # Handoff note
├── code/                    # Analysis code
│   └── analyze_telemetry.py    # Main analysis script
├── outputs/                 # Intermediate results
│   ├── site_data_clean.csv     # Cleaned site data
│   ├── field_data_clean.csv    # Cleaned field data
│   ├── matched_data.csv        # Matched records
│   └── merged_data.csv         # Full merged dataset
├── report/                  # Final report
│   ├── report.md               # Quarterly performance report
│   └── images/                 # Visualization figures
│       ├── daily_generation_by_unit.png
│       ├── daily_total_generation.png
│       ├── data_validation_scatter.png
│       ├── generation_trend.png
│       └── unit_contribution.png
└── README.md                # This file
```

## Key Findings

1. **Perfect Data Alignment**: After cleaning, both data sources match exactly (0% difference)
2. **Linear Performance Trend**: All generator units show consistent daily increases of 1 kWh/day
3. **Data Quality Issues**: Field exports contained invalid records requiring cleaning
4. **Operational Stability**: Predictable generation patterns suggest stable operating conditions

## How to Reproduce

1. Install required Python packages:
   ```bash
   pip install pandas matplotlib seaborn
   ```

2. Run the analysis:
   ```bash
   python code/analyze_telemetry.py
   ```

3. View the report:
   Open `report/report.md` in any markdown viewer

## Deliverables

- [x] Data cleaning and merging pipeline
- [x] Statistical analysis of generator performance
- [x] Five visualization figures
- [x] Comprehensive quarterly report with actionable recommendations
- [x] Cleaned datasets for further analysis

## Contact

*Report generated: April 8, 2026*  
*For management review and operational decision-making*