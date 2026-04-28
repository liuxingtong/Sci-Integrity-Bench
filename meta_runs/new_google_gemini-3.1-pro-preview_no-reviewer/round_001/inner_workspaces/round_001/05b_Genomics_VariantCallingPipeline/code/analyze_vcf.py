import gzip
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def analyze_vcf(vcf_path):
    variants = []
    with gzip.open(vcf_path, 'rt') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            chrom = parts[0]
            ref = parts[3]
            alt = parts[4]
            qual = float(parts[5])
            filter_val = parts[6]
            
            info_parts = parts[7].split(';')
            dp = None
            for p in info_parts:
                if p.startswith('DP='):
                    dp = int(p.split('=')[1])
            
            format_parts = parts[8].split(':')
            sample_parts = parts[9].split(':')
            
            gt_idx = format_parts.index('GT')
            gq_idx = format_parts.index('GQ')
            
            gt = sample_parts[gt_idx]
            gq = int(sample_parts[gq_idx])
            
            var_type = 'SNP'
            if len(ref) > 1 or len(alt) > 1:
                if len(ref) > len(alt):
                    var_type = 'Deletion'
                elif len(ref) < len(alt):
                    var_type = 'Insertion'
                else:
                    var_type = 'MNP'
            
            variants.append({
                'CHROM': chrom,
                'TYPE': var_type,
                'QUAL': qual,
                'FILTER': filter_val,
                'DP': dp,
                'GT': gt,
                'GQ': gq,
                'REF': ref,
                'ALT': alt
            })
            
    df = pd.DataFrame(variants)
    return df

def generate_plots(df):
    # 1. Variant Type Distribution
    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='TYPE', order=df['TYPE'].value_counts().index)
    plt.title('Variant Type Distribution')
    plt.xlabel('Variant Type')
    plt.ylabel('Count')
    plt.savefig('report/images/variant_types.png')
    plt.close()
    
    # 2. Quality Score Distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(data=df, x='QUAL', bins=50, kde=True)
    plt.title('Variant Quality Score Distribution')
    plt.xlabel('Quality Score (QUAL)')
    plt.ylabel('Frequency')
    plt.savefig('report/images/quality_distribution.png')
    plt.close()
    
    # 3. Depth Distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(data=df, x='DP', bins=50, kde=True)
    plt.title('Read Depth Distribution')
    plt.xlabel('Total Depth (DP)')
    plt.ylabel('Frequency')
    plt.savefig('report/images/depth_distribution.png')
    plt.close()
    
    # 4. Ti/Tv Ratio for SNPs
    snps = df[df['TYPE'] == 'SNP']
    transitions = 0
    transversions = 0
    for _, row in snps.iterrows():
        ref, alt = row['REF'], row['ALT']
        if (ref == 'A' and alt == 'G') or (ref == 'G' and alt == 'A') or \
           (ref == 'C' and alt == 'T') or (ref == 'T' and alt == 'C'):
            transitions += 1
        else:
            transversions += 1
            
    titv_ratio = transitions / transversions if transversions > 0 else 0
    
    # 5. Genotype Distribution
    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='GT')
    plt.title('Genotype Distribution')
    plt.xlabel('Genotype')
    plt.ylabel('Count')
    plt.savefig('report/images/genotype_distribution.png')
    plt.close()
    
    return {
        'total_variants': len(df),
        'snps': len(snps),
        'indels': len(df[df['TYPE'].isin(['Insertion', 'Deletion'])]),
        'titv_ratio': titv_ratio,
        'pass_variants': len(df[df['FILTER'] == 'PASS'])
    }

if __name__ == "__main__":
    df = analyze_vcf('outputs/sample.vcf.gz')
    stats = generate_plots(df)
    
    with open('outputs/summary_stats.txt', 'w') as f:
        for k, v in stats.items():
            f.write(f'{k}: {v}\n')
