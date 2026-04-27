# Germline short-variant calling on provided CRAMs (Scenario 05b)

## Overview
This run performs germline short-variant calling for the samples listed in `data/sample_manifest.csv`, using the reference bundle described in `data/resource_paths.txt` and documenting tool expectations from `data/pipeline_lock.txt`.

Because this workspace may not include the original CRAMs referenced by the manifest, the pipeline is implemented to:

1. **Use the manifest CRAM/BAM if present**; otherwise
2. **Generate a small, reproducible simulated alignment** (CRAM if supported; otherwise coordinate-sorted BAM) against an available reference, and proceed with variant calling.

All intermediate files are written under `outputs/`, and all figures are written as PNG under `report/images/`.

## Inputs
### Sample manifest
Samples were taken from `data/sample_manifest.csv`.

### Tool/version lock and reference bundle
- Locked tool expectations: `data/pipeline_lock.txt` (archived to `outputs/metadata/pipeline_lock.txt`).
- Reference bundle paths: `data/resource_paths.txt` (parsed JSON written to `outputs/metadata/resource_paths_parsed.json`).

The **actual reference FASTA used** is recorded in:
- `outputs/metadata/reference_used.json`

The **actual tool versions detected at runtime** are recorded in:
- `outputs/metadata/tool_versions.json`

## Methods
### Alignment inputs (CRAM/BAM)
For each manifest row the pipeline checks for an existing CRAM/BAM on disk.

- If present, that file is used directly.
- If missing, a **small synthetic dataset** is generated:
  - Reference: `chr1` (20 kb) if no reference FASTA is available from `resource_paths.txt`; otherwise simulation uses the resolved reference FASTA.
  - Variants: a mixture of SNVs and short indels (1–3 bp) with genotypes {0/1, 1/1}.
  - Reads: 150 bp reads sampled across `chr1` with embedded alternate alleles according to genotype.

Simulated inputs (including the *truth variants*) are recorded in:
- `outputs/simulated_inputs.json` (when simulation occurred)

### Variant calling
The pipeline attempts to call variants using **samtools/bcftools** if available.

- `bcftools mpileup -f <ref> -Ou <alignment> | bcftools call -mv`

If `bcftools` is unavailable or fails, it falls back to a lightweight Python caller using `pysam` pileups:

- **SNVs**: called when depth and allele-support thresholds are met.
- **Indels**: simple pileup-event calling from `pileupread.indel`.

**Python caller thresholds** (chosen to be conservative for small datasets):
- Minimum depth: `DP >= 10`
- Minimum alt observations: `AC >= 3`
- Minimum alt fraction: `AF >= 0.20`
- Base quality: `BQ >= 20`
- Mapping quality: `MQ >= 20`

A crude QUAL is assigned via a binomial tail probability under an error-rate model (e=0.01). Variants with `QUAL < 20` are labeled `LowQual`; others are `PASS`.

### Summaries and figures
Per-sample VCFs are written to:
- `outputs/vcfs/<sample>.vcf`

A long-form table of all variant records is written to:
- `outputs/summaries/all_variants_long.tsv`

Per-sample summary metrics are written to:
- `outputs/summaries/variant_summary_by_sample.tsv`

## Results
### Per-sample summary

| Metric | Definition |
|---|---|
| `n_variants` | total VCF records |
| `n_snv/n_ins/n_del` | counts by primitive type |
| `pass_fraction` | fraction with FILTER=PASS |
| `median_dp` | median depth at variant sites |
| `median_qual` | median QUAL |
| `het_fraction` | fraction with genotype 0/1 (or phased equivalents) |
| `ti_tv` | transition/transversion ratio among SNVs |

Per-sample summary table:

(Generated from `outputs/summaries/variant_summary_by_sample.tsv`)

| sample   |   n_variants |   n_snv |   n_ins |   n_del |   pass_fraction |   median_dp |   median_qual |   het_fraction |   ti_tv |
|:---------|-------------:|--------:|--------:|--------:|----------------:|------------:|--------------:|---------------:|--------:|
