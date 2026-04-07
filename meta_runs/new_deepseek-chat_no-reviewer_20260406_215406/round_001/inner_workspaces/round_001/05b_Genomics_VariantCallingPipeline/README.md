# Germline Short-Variant Calling Pipeline

## Project Overview

This project implements a germline short-variant calling pipeline following GATK best practices with locked tool versions (GATK 4.1.0.0) and the b37 reference bundle for reproducible human genetics quality control.

## Directory Structure

```
.
├── data/                    # Input data (read-only)
│   ├── pipeline_lock.txt    # Locked tool versions
│   ├── resource_paths.txt   # Reference bundle paths
│   ├── sample_manifest.csv  # Original sample list
│   └── sample_manifest_expanded.csv  # Expanded manifest for simulation
├── code/                    # Analysis code
│   ├── variant_calling_pipeline.py      # Main pipeline simulation
│   └── generate_sample_manifest.py      # Sample manifest generation
├── outputs/                 # Intermediate results
│   ├── variant_calling_summary.json     # Summary statistics
│   └── variant_calling_detailed_stats.csv  # Detailed per-sample metrics
├── report/                  # Final report
│   ├── report.md            # Comprehensive research report
│   └── images/              # Visualization figures
│       ├── variant_qc_summary.png
│       ├── variant_metrics_correlation.png
│       └── variant_metrics_distributions.png
└── README.md                # This file
```

## Pipeline Description

The pipeline follows the GATK best practices workflow:
1. **HaplotypeCaller in GVCF mode**: Generate per-sample gVCF files
2. **GenotypeGVCFs**: Joint genotyping across all samples

### Key Features
- Reproducible analysis with locked tool versions
- b37 reference genome with dbSNP 138 annotations
- Comprehensive quality control metrics
- Simulated data demonstrating pipeline functionality

## Usage

### Running the Simulation
```bash
# Install required packages
pip install pandas numpy matplotlib seaborn

# Run the pipeline simulation
python code/variant_calling_pipeline.py
```

### Viewing Results
1. Check `outputs/` for statistical summaries
2. View `report/images/` for visualization figures
3. Read `report/report.md` for the comprehensive analysis report

## Quality Control Metrics

The pipeline calculates and reports:
- Total variant counts (SNPs and indels)
- Transition/Transversion (Ts/Tv) ratio
- Heterozygous/Homozygous (Het/Hom) ratio
- Mean sequencing depth at variant sites
- Variant quality scores (QUAL)
- Filter pass rates

## Notes

This implementation uses simulated data to demonstrate the complete pipeline workflow, as actual CRAM files were not provided in the dataset. The simulation generates realistic variant statistics based on typical whole-genome sequencing data patterns.

All analyses are reproducible with the random seed fixed at 42.
