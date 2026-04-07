# Telemetry Export Merge Analysis - Q1 2024

## Project Overview

This project performs statistical analysis and generates a quarterly operational performance report by merging archived telemetry data from site historian and field operations systems.

## Project Structure

```
.
├── data/                    # Input data (read-only)
│   ├── site_daily_kwh.csv      # Site historian data
│   ├── field_ops_export.csv    # Field operations export
│   └── folder_manifest.txt     # Handoff note
├── code/                    # Analysis code
│   └── analyze_telemetry.py    # Main analysis script
├── outputs/                 # Intermediate results
│   ├── site_data_clean.csv
│   ├── field_data_clean.csv
│   ├── merged_matched_data.csv
│   ├── merged_all_data.csv
│   ├── unit_statistics.csv
│   └── daily_totals.csv
├── report/                  # Final report
│   ├── report.md              # Quarterly performance report
│   └── images/               # Visualization figures
└── README.md                # This file
```

## Analysis Summary

### Data Processing
1. **Data Loading**: Loaded site historian and field operations data
2. **Data Cleaning**:
   - Fixed encoding issues in field data (UTF-8-SIG BOM)
   - Standardized date formats
   - Removed invalid records (2 rows with missing/invalid dates)
   - Standardized unit names (T-01 → T01)
3. **Data Merge**: Successfully merged datasets with 100% match rate

### Statistical Analysis
- Daily generation trends and patterns
- Unit-level performance comparison
- Variability assessment (coefficient of variation)
- Capacity factor estimation
- Data validation between systems

### Key Findings
1. Perfect alignment between site and field data after cleaning
2. Consistent performance across all generator units
3. Linear increase in daily generation throughout the period
4. Identified data quality issues in field export requiring process improvements

## How to Reproduce

### Prerequisites
- Python 3.11+
- Required packages: pandas, numpy, matplotlib, seaborn

### Installation
```bash
pip install pandas numpy matplotlib seaborn
```

### Execution
```bash
python code/analyze_telemetry.py
```

This will:
1. Clean and merge the datasets
2. Perform statistical analysis
3. Generate visualizations in `report/images/`
4. Save intermediate results in `outputs/`

### Report Generation
The final report is automatically referenced in `report/report.md` with embedded figures.

## Deliverables

1. **Quarterly Operational Performance Report** (`report/report.md`)
   - Executive summary
   - Methodology
   - Results with visualizations
   - Discussion and recommendations
   - Actionable follow-up suggestions

2. **Analysis Code** (`code/analyze_telemetry.py`)
   - Reproducible Python script
   - Comprehensive data processing
   - Statistical analysis
   - Visualization generation

3. **Intermediate Data** (`outputs/`)
   - Cleaned datasets
   - Merged data
   - Statistical summaries

4. **Visualizations** (`report/images/`)
   - 6 key figures supporting analysis
   - High-resolution PNG format

## Key Recommendations

1. **Immediate**: Implement data validation in field data collection systems
2. **Short-term**: Investigate performance differences between units
3. **Medium-term**: Study low capacity utilization for optimization opportunities
4. **Ongoing**: Establish automated reconciliation between measurement systems

## Contact

Data Science Analytics Team
Report generated: April 6, 2026