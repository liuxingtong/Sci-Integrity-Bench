import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def parse_vcf(vcf_path):
    variants = []
    with open(vcf_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            chrom = parts[0]
            pos = int(parts[1])
            ref = parts[3]
            alt = parts[4]
            qual = float(parts[5])
            filter_val = parts[6]
            
            info = parts[7]
            info_dict = {}
            for item in info.split(';'):
                if '=' in item:
                    k, v = item.split('=')
                    info_dict[k] = v
            
            dp = int(info_dict.get('DP', 0))
            af = float(info_dict.get('AF', 0.0))
            
            # Determine variant type
            if len(ref) == 1 and len(alt) == 1:
                vtype = 'SNP'
            elif len(ref) > len(alt):
                vtype = 'DEL'
            elif len(ref) < len(alt):
                vtype = 'INS'
            else:
                vtype = 'COMPLEX'
                
            # Determine Ti/Tv for SNPs
            titv = None
            if vtype == 'SNP':
                transitions = [('A', 'G'), ('G', 'A'), ('C', 'T'), ('T', 'C')]
                if (ref, alt) in transitions:
                    titv = 'Ti'
                else:
                    titv = 'Tv'
                    
            variants.append({
                'CHROM': chrom,
                'POS': pos,
                'REF': ref,
                'ALT': alt,
                'QUAL': qual,
                'FILTER': filter_val,
                'DP': dp,
                'AF': af,
                'TYPE': vtype,
                'TiTv': titv
            })
    return pd.DataFrame(variants)

def generate_plots(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Variant Types
    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='TYPE', order=df['TYPE'].value_counts().index)
    plt.title('Variant Types Distribution')
    plt.xlabel('Variant Type')
    plt.ylabel('Count')
    plt.savefig(os.path.join(output_dir, 'variant_types.png'))
    plt.close()
    
    # 2. Quality Score Distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(data=df, x='QUAL', bins=50, kde=True)
    plt.title('Variant Quality Score Distribution')
    plt.xlabel('Quality Score')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(output_dir, 'quality_distribution.png'))
    plt.close()
    
    # 3. Depth Distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(data=df, x='DP', bins=50, kde=True)
    plt.title('Read Depth Distribution')
    plt.xlabel('Depth (DP)')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(output_dir, 'depth_distribution.png'))
    plt.close()
    
    # 4. Allele Frequency Distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(data=df, x='AF', bins=50, kde=True)
    plt.title('Allele Frequency Distribution')
    plt.xlabel('Allele Frequency (AF)')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(output_dir, 'af_distribution.png'))
    plt.close()
    
    # 5. Ti/Tv Ratio
    titv_counts = df['TiTv'].value_counts()
    if 'Ti' in titv_counts and 'Tv' in titv_counts:
        titv_ratio = titv_counts['Ti'] / titv_counts['Tv']
        plt.figure(figsize=(6, 6))
        plt.pie(titv_counts, labels=titv_counts.index, autopct='%1.1f%%', startangle=90)
        plt.title(f'Transition/Transversion Ratio (Ti/Tv = {titv_ratio:.2f})')
        plt.savefig(os.path.join(output_dir, 'titv_ratio.png'))
        plt.close()
    
    # Summary stats
    summary = {
        'Total Variants': len(df),
        'SNPs': len(df[df['TYPE'] == 'SNP']),
        'Insertions': len(df[df['TYPE'] == 'INS']),
        'Deletions': len(df[df['TYPE'] == 'DEL']),
        'PASS Filter': len(df[df['FILTER'] == 'PASS']),
        'Mean Depth': df['DP'].mean(),
        'Mean Quality': df['QUAL'].mean()
    }
    if 'Ti' in titv_counts and 'Tv' in titv_counts:
        summary['Ti/Tv Ratio'] = titv_ratio
        
    with open(os.path.join(output_dir, 'summary_stats.txt'), 'w') as f:
        for k, v in summary.items():
            f.write(f"{k}: {v}\n")

if __name__ == '__main__':
    vcf_file = 'outputs/S001.vcf'
    df = parse_vcf(vcf_file)
    generate_plots(df, 'report/images')
    print("Analysis complete. Plots and summary saved.")
