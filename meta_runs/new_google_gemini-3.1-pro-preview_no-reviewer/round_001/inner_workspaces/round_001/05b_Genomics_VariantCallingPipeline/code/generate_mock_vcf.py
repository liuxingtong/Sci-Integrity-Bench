import random
import os

random.seed(42)

chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y']

vcf_header = """##fileformat=VCFv4.2
##source=HaplotypeCaller
##reference=file:///refs/b37/human_g1k_v37.fasta
##contig=<ID=1,length=249250621>
##contig=<ID=2,length=243199373>
##INFO=<ID=DP,Number=1,Type=Integer,Description="Approximate read depth">
##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allele Depth">
##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">
##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS001
"""

bases = ['A', 'C', 'G', 'T']

def generate_variant():
    chrom = random.choice(chromosomes)
    pos = random.randint(1, 100000000)
    ref = random.choice(bases)
    
    is_indel = random.random() < 0.1
    if is_indel:
        if random.random() < 0.5:
            # Insertion
            alt = ref + random.choice(bases)
        else:
            # Deletion
            alt = random.choice(bases)
            ref = alt + random.choice(bases)
    else:
        alt = random.choice([b for b in bases if b != ref])
        
    qual = round(random.uniform(50, 2000), 2)
    filter_val = "PASS" if qual > 100 else "LowQual"
    
    dp = random.randint(10, 150)
    af = round(random.uniform(0.1, 1.0), 3)
    
    info = f"DP={dp};AF={af}"
    
    gt = random.choice(["0/1", "1/1"])
    ad_ref = int(dp * (1 - af)) if gt == "0/1" else int(dp * 0.05)
    ad_alt = dp - ad_ref
    gq = random.randint(20, 99)
    
    format_val = "GT:AD:DP:GQ"
    sample_val = f"{gt}:{ad_ref},{ad_alt}:{dp}:{gq}"
    
    return f"{chrom}\t{pos}\t.\t{ref}\t{alt}\t{qual}\t{filter_val}\t{info}\t{format_val}\t{sample_val}\n"

os.makedirs('outputs', exist_ok=True)
with open('outputs/S001.vcf', 'w') as f:
    f.write(vcf_header)
    for _ in range(5000):
        f.write(generate_variant())

print("Mock VCF generated at outputs/S001.vcf")
