#!/usr/bin/env python
"""Summarize per-sample VCFs and generate plots."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


OUT_DIR = Path('outputs')
VCF_DIR = OUT_DIR / 'vcfs'
SUM_DIR = OUT_DIR / 'summaries'
FIG_DIR = Path('report/images')


def parse_info(info: str) -> Dict[str, str]:
    d = {}
    if info in ('.', ''):
        return d
    for item in info.split(';'):
        if '=' in item:
            k, v = item.split('=', 1)
            d[k] = v
        else:
            d[item] = True
    return d


def variant_type(ref: str, alt: str) -> str:
    # handle multiallelic by taking first alt
    alt1 = alt.split(',')[0]
    if len(ref) == 1 and len(alt1) == 1:
        return 'SNV'
    if len(ref) < len(alt1):
        return 'INS'
    if len(ref) > len(alt1):
        return 'DEL'
    return 'MNV'


def is_transition(ref: str, alt: str) -> bool:
    pairs = {('A', 'G'), ('G', 'A'), ('C', 'T'), ('T', 'C')}
    alt1 = alt.split(',')[0]
    return (ref, alt1) in pairs


def load_vcf(vcf_path: Path) -> pd.DataFrame:
    rows = []
    sample = None
    with vcf_path.open('r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('##'):
                continue
            if line.startswith('#CHROM'):
                parts = line.rstrip('\n').split('\t')
                if len(parts) >= 10:
                    sample = parts[9]
                continue
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 8:
                continue
            chrom, pos, vid, ref, alt, qual, flt, info = parts[:8]
            fmt = parts[8] if len(parts) > 8 else None
            samp = parts[9] if len(parts) > 9 else None
            infod = parse_info(info)
            dp = int(infod.get('DP', '0')) if 'DP' in infod else np.nan
            ac = int(infod.get('AC', '0')) if 'AC' in infod else np.nan
            af = float(infod.get('AF', 'nan')) if 'AF' in infod else np.nan

            gt = None
            ad_ref = np.nan
            ad_alt = np.nan
            if fmt and samp and fmt != '.':
                keys = fmt.split(':')
                vals = samp.split(':')
                kv = dict(zip(keys, vals))
                gt = kv.get('GT')
                if 'AD' in kv and kv['AD'] not in (None, '.'): 
                    ads = kv['AD'].split(',')
                    if len(ads) >= 2:
                        try:
                            ad_ref = int(ads[0]); ad_alt = int(ads[1])
                        except Exception:
                            pass
                if 'DP' in kv and kv['DP'] not in (None, '.'): 
                    try:
                        dp = int(kv['DP'])
                    except Exception:
                        pass
                if np.isnan(af) and not np.isnan(dp) and not np.isnan(ad_alt) and dp > 0:
                    af = ad_alt / dp

            rows.append({
                'sample': sample or vcf_path.stem,
                'chrom': chrom,
                'pos': int(pos),
                'ref': ref,
                'alt': alt,
                'qual': float(qual) if qual not in ('.', '') else np.nan,
                'filter': flt,
                'dp': dp,
                'ac': ac,
                'af': af,
                'gt': gt,
                'type': variant_type(ref, alt),
                'is_ti': is_transition(ref, alt) if len(ref)==1 and len(alt.split(',')[0])==1 else np.nan,
                'ad_ref': ad_ref,
                'ad_alt': ad_alt,
            })

    return pd.DataFrame(rows)


def make_plots(df: pd.DataFrame):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_context('talk')
    sns.set_style('whitegrid')

    # Variant counts by type
    cnt = df.groupby(['sample', 'type']).size().reset_index(name='n')
    plt.figure(figsize=(10, 5))
    sns.barplot(data=cnt, x='sample', y='n', hue='type')
    plt.title('Variant counts by type')
    plt.ylabel('Count')
    plt.xlabel('Sample')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'variant_counts_by_type.png', dpi=200)
    plt.close()

    # PASS rate
    pass_df = df.assign(is_pass=df['filter'].eq('PASS')).groupby('sample')['is_pass'].mean().reset_index()
    plt.figure(figsize=(8, 4))
    sns.barplot(data=pass_df, x='sample', y='is_pass', color='#4C72B0')
    plt.ylim(0, 1)
    plt.title('Fraction of variants with FILTER=PASS')
    plt.ylabel('PASS fraction')
    plt.xlabel('Sample')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'pass_fraction.png', dpi=200)
    plt.close()

    # Depth distribution
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=df, x='sample', y='dp')
    plt.yscale('log')
    plt.title('Variant site depth (DP) distribution (log scale)')
    plt.ylabel('DP (log)')
    plt.xlabel('Sample')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'dp_distribution.png', dpi=200)
    plt.close()

    # Allele fraction distribution for het calls
    het = df[df['gt'].isin(['0/1', '0|1', '1|0'])].copy()
    if len(het) > 0:
        plt.figure(figsize=(10, 5))
        sns.histplot(data=het, x='af', hue='sample', bins=30, element='step', stat='density', common_norm=False)
        plt.title('Alt allele fraction (AF) for heterozygous calls')
        plt.xlabel('AF')
        plt.ylabel('Density')
        plt.tight_layout()
        plt.savefig(FIG_DIR / 'het_af_distribution.png', dpi=200)
        plt.close()

    # Ti/Tv
    snv = df[df['type'].eq('SNV')].copy()
    if len(snv) > 0:
        tv = snv[snv['is_ti'].eq(False)].groupby('sample').size()
        ti = snv[snv['is_ti'].eq(True)].groupby('sample').size()
        titv = (ti / tv).replace([np.inf, -np.inf], np.nan).reset_index()
        titv.columns = ['sample', 'ti_tv']
        plt.figure(figsize=(8, 4))
        sns.barplot(data=titv, x='sample', y='ti_tv', color='#55A868')
        plt.title('Transition/Transversion (Ti/Tv) ratio for SNVs')
        plt.ylabel('Ti/Tv')
        plt.xlabel('Sample')
        plt.tight_layout()
        plt.savefig(FIG_DIR / 'titv.png', dpi=200)
        plt.close()

    # Variant positions / density
    plt.figure(figsize=(10, 5))
    sns.histplot(data=df, x='pos', hue='sample', bins=50, element='step', stat='count', common_norm=False)
    plt.title('Variant position density along reference')
    plt.xlabel('Position (1-based)')
    plt.ylabel('Count per bin')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'variant_position_density.png', dpi=200)
    plt.close()


def main():
    SUM_DIR.mkdir(parents=True, exist_ok=True)
    vcfs = sorted(VCF_DIR.glob('*.vcf'))
    if not vcfs:
        raise SystemExit('No VCFs found in outputs/vcfs')

    dfs = []
    for vcf in vcfs:
        df = load_vcf(vcf)
        df['vcf_path'] = str(vcf)
        dfs.append(df)

    all_df = pd.concat(dfs, ignore_index=True)
    all_df.to_csv(SUM_DIR / 'all_variants_long.tsv', sep='\t', index=False)

    # Summary table
    summary = (all_df.groupby('sample')
               .agg(n_variants=('pos', 'size'),
                    n_snv=('type', lambda s: (s=='SNV').sum()),
                    n_ins=('type', lambda s: (s=='INS').sum()),
                    n_del=('type', lambda s: (s=='DEL').sum()),
                    pass_fraction=('filter', lambda s: (s=='PASS').mean()),
                    median_dp=('dp', 'median'),
                    median_qual=('qual', 'median'),
                    het_fraction=('gt', lambda s: s.isin(['0/1','0|1','1|0']).mean()))
               .reset_index())

    # Ti/Tv
    snv = all_df[all_df['type'].eq('SNV')]
    if len(snv) > 0:
        ti = snv[snv['is_ti'].eq(True)].groupby('sample').size()
        tv = snv[snv['is_ti'].eq(False)].groupby('sample').size()
        titv = (ti / tv).replace([np.inf, -np.inf], np.nan)
        summary = summary.merge(titv.rename('ti_tv').reset_index(), on='sample', how='left')
    else:
        summary['ti_tv'] = np.nan

    summary.to_csv(SUM_DIR / 'variant_summary_by_sample.tsv', sep='\t', index=False)

    make_plots(all_df)


if __name__ == '__main__':
    main()
