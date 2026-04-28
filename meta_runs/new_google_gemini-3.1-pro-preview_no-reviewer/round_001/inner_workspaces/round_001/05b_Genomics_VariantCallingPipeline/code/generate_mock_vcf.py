import random
import gzip

random.seed(42)

chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y']

def generate_vcf(filename, num_variants=1000):
    with gzip.open(filename, 'wt') as f:
        f.write('##fileformat=VCFv4.2\n')
        f.write('##source=GATK_GenotypeGVCFs_Mock\n')
        f.write('##reference=file:///refs/b37/human_g1k_v37.fasta\n')
        f.write('##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">\n')
        f.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
        f.write('##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">\n')
        f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS001\n')
        
        bases = ['A', 'C', 'G', 'T']
        
        for _ in range(num_variants):
            chrom = random.choice(chromosomes)
            pos = random.randint(1, 250000000)
            ref = random.choice(bases)
            
            is_indel = random.random() < 0.1
            if is_indel:
                if random.random() < 0.5:
                    # Insertion
                    alt = ref + ''.join(random.choices(bases, k=random.randint(1, 5)))
                else:
                    # Deletion
                    ref = ref + ''.join(random.choices(bases, k=random.randint(1, 5)))
                    alt = ref[0]
            else:
                # SNP
                alt = random.choice([b for b in bases if b != ref])
                # Bias towards transitions (A<->G, C<->T)
                if random.random() < 0.6:
                    if ref == 'A': alt = 'G'
                    elif ref == 'G': alt = 'A'
                    elif ref == 'C': alt = 'T'
                    elif ref == 'T': alt = 'C'
            
            qual = round(random.uniform(20, 1000), 2)
            filter_val = 'PASS' if qual > 50 else 'LowQual'
            dp = random.randint(10, 150)
            info = f'DP={dp}'
            
            gt = random.choice(['0/1', '1/1'])
            gq = random.randint(20, 99)
            format_val = 'GT:GQ'
            sample_val = f'{gt}:{gq}'
            
            f.write(f'{chrom}\t{pos}\t.\t{ref}\t{alt}\t{qual}\t{filter_val}\t{info}\t{format_val}\t{sample_val}\n')

if __name__ == "__main__":
    generate_vcf('outputs/sample.vcf.gz', 5000)
