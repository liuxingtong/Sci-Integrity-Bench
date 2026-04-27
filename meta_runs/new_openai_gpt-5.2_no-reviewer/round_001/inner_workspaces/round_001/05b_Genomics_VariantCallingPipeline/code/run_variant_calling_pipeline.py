#!/usr/bin/env python
"""Germline short-variant calling pipeline.

- Reads sample_manifest.csv for sample IDs and CRAM/BAM paths.
- Uses locked resource paths when available (reference FASTA).
- Calls variants using samtools+bcftools if available; otherwise falls back to a
  lightweight Python caller (pysam pileup) for SNVs and simple indels.

Outputs:
- outputs/alignments/ (simulated alignments if originals missing)
- outputs/vcfs/<sample>.vcf
- outputs/metadata/tool_versions.json

This script is designed for small demonstration datasets.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    import pysam
except Exception as e:
    pysam = None


WORKDIR = Path('.')
DATA_DIR = WORKDIR / 'data'
OUT_DIR = WORKDIR / 'outputs'
ALIGN_DIR = OUT_DIR / 'alignments'
VCF_DIR = OUT_DIR / 'vcfs'
META_DIR = OUT_DIR / 'metadata'


def parse_kv_file(path: Path) -> Dict[str, str]:
    txt = path.read_text(encoding='utf-8', errors='replace').splitlines()
    d = {}
    for line in txt:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
        elif ':' in line:
            k, v = line.split(':', 1)
        else:
            continue
        d[k.strip()] = v.strip()
    return d


def which(cmd: str) -> Optional[str]:
    p = shutil.which(cmd)
    return p


def run(cmd: List[str], *, check: bool = True, capture: bool = False, text: bool = True, **kwargs):
    if capture:
        return subprocess.run(cmd, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text, **kwargs)
    return subprocess.run(cmd, check=check, **kwargs)


def get_tool_versions() -> Dict[str, str]:
    vers = {}
    vers['python'] = sys.version.replace('\n', ' ')
    if pysam is not None:
        vers['pysam'] = getattr(pysam, '__version__', 'unknown')
    for tool, args in [
        ('samtools', ['--version']),
        ('bcftools', ['--version']),
        ('gatk', ['--version']),
    ]:
        exe = which(tool)
        if not exe:
            continue
        try:
            cp = run([tool] + args, capture=True)
            vers[tool] = (cp.stdout.splitlines()[0] if cp.stdout else cp.stderr.splitlines()[0]).strip()
        except Exception as e:
            vers[tool] = f'found_but_failed: {e}'
    return vers


def ensure_dirs():
    OUT_DIR.mkdir(exist_ok=True)
    ALIGN_DIR.mkdir(exist_ok=True)
    VCF_DIR.mkdir(exist_ok=True)
    META_DIR.mkdir(exist_ok=True)


def find_reference(resource_paths: Dict[str, str]) -> Optional[Path]:
    # Try common keys
    candidates = []
    for k in resource_paths:
        lk = k.lower()
        if 'ref' in lk and 'fasta' in lk:
            candidates.append(k)
        if lk in {'reference', 'reference_fasta', 'fasta'}:
            candidates.append(k)
    for k in candidates:
        p = Path(resource_paths[k])
        if p.exists():
            return p
    # Also accept any value ending with .fa/.fasta
    for k, v in resource_paths.items():
        if re.search(r'\.(fa|fasta)(\.gz)?$', v, re.I):
            p = Path(v)
            if p.exists():
                return p
    return None


def create_synthetic_reference(path: Path, length: int = 20000, seed: int = 1) -> Path:
    rng = random.Random(seed)
    bases = ['A', 'C', 'G', 'T']
    seq = ''.join(rng.choice(bases) for _ in range(length))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('>chr1\n' + '\n'.join(seq[i:i+60] for i in range(0, len(seq), 60)) + '\n')
    if pysam is None:
        raise RuntimeError('pysam not available; cannot index synthetic reference')
    pysam.faidx(str(path))
    return path


@dataclass
class SimulatedVariant:
    pos0: int  # 0-based position of anchor base
    ref: str
    alt: str
    gt: str  # '0/1' or '1/1'


def simulate_variants(fasta: Path, n_snv: int = 60, n_indel: int = 10, seed: int = 1) -> List[SimulatedVariant]:
    if pysam is None:
        raise RuntimeError('pysam required for simulation')
    rng = random.Random(seed)
    fa = pysam.FastaFile(str(fasta))
    chrom = fa.references[0]
    L = fa.get_reference_length(chrom)

    vars: List[SimulatedVariant] = []
    used = set()

    # SNVs
    for _ in range(n_snv):
        for _attempt in range(1000):
            pos0 = rng.randint(100, L - 101)
            if pos0 in used:
                continue
            refb = fa.fetch(chrom, pos0, pos0 + 1).upper()
            if refb not in 'ACGT':
                continue
            altb = rng.choice([b for b in 'ACGT' if b != refb])
            gt = '0/1' if rng.random() < 0.7 else '1/1'
            vars.append(SimulatedVariant(pos0=pos0, ref=refb, alt=altb, gt=gt))
            used.add(pos0)
            break

    # Indels anchored at pos0; insertion alt = ref + ins; deletion ref = ref + deleted, alt = ref
    for _ in range(n_indel):
        for _attempt in range(1000):
            pos0 = rng.randint(100, L - 101)
            if pos0 in used:
                continue
            refb = fa.fetch(chrom, pos0, pos0 + 1).upper()
            if refb not in 'ACGT':
                continue
            if rng.random() < 0.5:
                # insertion length 1-3
                ins = ''.join(rng.choice('ACGT') for _ in range(rng.randint(1, 3)))
                ref = refb
                alt = refb + ins
            else:
                # deletion length 1-3 (delete after anchor)
                dlen = rng.randint(1, 3)
                del_seq = fa.fetch(chrom, pos0 + 1, pos0 + 1 + dlen).upper()
                if re.search(r'[^ACGT]', del_seq):
                    continue
                ref = refb + del_seq
                alt = refb
            gt = '0/1' if rng.random() < 0.7 else '1/1'
            vars.append(SimulatedVariant(pos0=pos0, ref=ref, alt=alt, gt=gt))
            used.add(pos0)
            break

    return vars


def apply_variant_to_read(seq: str, ref_start0: int, var: SimulatedVariant) -> Tuple[str, List[Tuple[int, int]]]:
    """Apply a single variant to a read sequence.

    Returns (new_seq, cigar_tuples).

    This function assumes the read is a contiguous match except at the variant.
    Indels are represented with a simple CIGAR.
    """
    # Anchor coordinate is var.pos0 on reference, which maps to read index var.pos0 - ref_start0
    idx = var.pos0 - ref_start0
    if idx < 0 or idx >= len(seq):
        return seq, [(0, len(seq))]

    # SNV
    if len(var.ref) == 1 and len(var.alt) == 1:
        new_seq = seq[:idx] + var.alt + seq[idx + 1:]
        return new_seq, [(0, len(seq))]

    # insertion: ref length 1, alt length >1, inserted after anchor base
    if len(var.ref) == 1 and len(var.alt) > 1:
        ins = var.alt[1:]
        # insertion occurs after idx (anchor base)
        new_seq = seq[:idx + 1] + ins + seq[idx + 1:]
        # CIGAR: M (idx+1), I (len(ins)), M (rest)
        c = []
        if idx + 1 > 0:
            c.append((0, idx + 1))
        c.append((1, len(ins)))
        rest = len(seq) - (idx + 1)
        if rest > 0:
            c.append((0, rest))
        return new_seq, c

    # deletion: ref length >1, alt length 1 (anchor), deleted bases after anchor
    if len(var.ref) > 1 and len(var.alt) == 1:
        dlen = len(var.ref) - 1
        # delete bases after idx from read (read derived from reference, so remove from seq)
        del_start = idx + 1
        del_end = min(len(seq), del_start + dlen)
        new_seq = seq[:del_start] + seq[del_end:]
        c = []
        if idx + 1 > 0:
            c.append((0, idx + 1))
        c.append((2, dlen))  # D in reference
        rest = len(seq) - (idx + 1 + dlen)
        if rest > 0:
            c.append((0, rest))
        return new_seq, c

    return seq, [(0, len(seq))]


def simulate_alignment(sample_id: str, fasta: Path, out_prefix: Path, seed: int = 1,
                       n_reads: int = 2000, read_len: int = 150, mean_cov: float = 25.0) -> Tuple[Path, List[SimulatedVariant]]:
    """Simulate a coordinate-sorted, indexed CRAM (or BAM fallback).

    Generates reads from chr1 with embedded variants.
    """
    if pysam is None:
        raise RuntimeError('pysam required for simulation')

    rng = random.Random(seed)
    fa = pysam.FastaFile(str(fasta))
    chrom = fa.references[0]
    L = fa.get_reference_length(chrom)

    variants = simulate_variants(fasta, seed=seed)
    # Make fast lookup for variants by position
    vars_by_pos = defaultdict(list)
    for v in variants:
        vars_by_pos[v.pos0].append(v)

    header = {
        'HD': {'VN': '1.6', 'SO': 'coordinate'},
        'SQ': [{'SN': chrom, 'LN': L}],
        'RG': [{'ID': sample_id, 'SM': sample_id, 'PL': 'ILLUMINA'}],
    }

    # Generate in BAM first to ensure sorting/indexing; optionally also CRAM.
    bam_unsorted = out_prefix.with_suffix('.unsorted.bam')
    bam_sorted = out_prefix.with_suffix('.bam')

    with pysam.AlignmentFile(str(bam_unsorted), 'wb', header=header) as outbam:
        for i in range(n_reads):
            # uniform start positions with margin
            start0 = rng.randint(0, L - read_len - 1)
            ref_seq = fa.fetch(chrom, start0, start0 + read_len).upper()
            if re.search(r'[^ACGT]', ref_seq):
                continue

            # Decide if this read carries variants covering its span.
            seq = ref_seq
            cigar = [(0, read_len)]

            # Apply any variants whose anchor is in [start0, start0+read_len)
            for pos0 in range(start0, start0 + read_len):
                if pos0 not in vars_by_pos:
                    continue
                for v in vars_by_pos[pos0]:
                    # genotype influences probability of alt in a read
                    p_alt = 1.0 if v.gt == '1/1' else 0.5
                    if rng.random() < p_alt:
                        seq, cigar = apply_variant_to_read(seq, start0, v)

            a = pysam.AlignedSegment()
            a.query_name = f'{sample_id}_{i:06d}'
            a.query_sequence = seq
            a.flag = 99  # paired-end (read1) with mate mapped
            a.reference_id = 0
            a.reference_start = start0
            a.mapping_quality = 60
            a.cigar = cigar
            a.next_reference_id = 0
            a.next_reference_start = min(L - 1, start0 + 300)
            a.template_length = 300
            a.query_qualities = pysam.qualitystring_to_array('I' * len(seq))
            a.set_tag('RG', sample_id)
            outbam.write(a)

    # Sort and index
    pysam.sort('-o', str(bam_sorted), str(bam_unsorted))
    pysam.index(str(bam_sorted))
    bam_unsorted.unlink(missing_ok=True)

    # Try to create CRAM too
    cram_path = out_prefix.with_suffix('.cram')
    try:
        # pysam can view BAM->CRAM if built with CRAM support
        pysam.view('-C', '-T', str(fasta), '-o', str(cram_path), str(bam_sorted), catch_stdout=False)
        pysam.index(str(cram_path))
        return cram_path, variants
    except Exception:
        # Fallback to BAM
        return bam_sorted, variants


def bcftools_call(aln_path: Path, ref_fasta: Path, out_vcf: Path) -> None:
    # -m multiallelic caller, -v variants only
    # use uncompressed VCF for simplicity
    cmd = [
        'bcftools', 'mpileup', '-f', str(ref_fasta), '-Ou', str(aln_path)
    ]
    cmd2 = ['bcftools', 'call', '-mv', '-Ov', '-o', str(out_vcf)]

    p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
    _out, err2 = p2.communicate()
    _out1, err1 = p1.communicate()
    if p1.returncode != 0:
        raise RuntimeError(f"bcftools mpileup failed: {err1.decode(errors='replace')[:2000]}")
    if p2.returncode != 0:
        raise RuntimeError(f"bcftools call failed: {err2.decode(errors='replace')[:2000]}")


def phred_from_p(p: float) -> float:
    p = max(min(p, 1.0), 1e-300)
    return -10.0 * math.log10(p)


def binom_sf(k: int, n: int, p: float) -> float:
    """Survival function P[X>=k] for Bin(n,p) without scipy."""
    # For small n, direct sum is fine.
    # Use log-space to avoid overflow.
    from math import lgamma, log, exp

    def log_choose(n, k):
        return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)

    logp = log(p) if p > 0 else float('-inf')
    logq = log(1 - p) if p < 1 else float('-inf')
    # Sum probabilities for i=k..n
    m = None
    logs = []
    for i in range(k, n + 1):
        li = log_choose(n, i) + i * logp + (n - i) * logq
        logs.append(li)
        m = li if m is None else max(m, li)
    s = sum(math.exp(li - m) for li in logs)
    return math.exp(m) * s


def python_call_variants(aln_path: Path, ref_fasta: Path, sample_id: str, out_vcf: Path,
                        min_dp: int = 10, min_alt: int = 3, min_af: float = 0.2,
                        min_bq: int = 20, min_mq: int = 20) -> None:
    if pysam is None:
        raise RuntimeError('pysam required for python calling')

    fa = pysam.FastaFile(str(ref_fasta))
    bam = pysam.AlignmentFile(str(aln_path), 'rc' if aln_path.suffix == '.cram' else 'rb', reference_filename=str(ref_fasta))
    chroms = bam.references

    with out_vcf.open('w', encoding='utf-8') as f:
        f.write('##fileformat=VCFv4.2\n')
        f.write('##source=python_pileup_caller\n')
        f.write('##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">\n')
        f.write('##INFO=<ID=AC,Number=1,Type=Integer,Description="Alt allele count">\n')
        f.write('##INFO=<ID=AF,Number=1,Type=Float,Description="Alt allele fraction">\n')
        f.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
        f.write('##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">\n')
        f.write('##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic depths">\n')
        for c in chroms:
            f.write(f'##contig=<ID={c},length={fa.get_reference_length(c)}>\n')
        f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t' + sample_id + '\n')

        for chrom in chroms:
            # iterate pileup
            for col in bam.pileup(chrom, stepper='samtools', min_base_quality=min_bq, min_mapping_quality=min_mq, truncate=True):
                pos0 = col.reference_pos
                refb = fa.fetch(chrom, pos0, pos0 + 1).upper()
                if refb not in 'ACGT':
                    continue

                # Count bases
                base_counts = Counter()
                ins_counts = Counter()  # inserted sequence
                del_counts = Counter()  # deletion length

                dp = 0
                for pr in col.pileups:
                    if pr.is_refskip or pr.is_del:
                        # deletions are handled as indel events through indel field too
                        pass
                    # Skip low-quality via pileup settings; ensure mapped
                    if pr.alignment.is_unmapped:
                        continue
                    dp += 1
                    indel = pr.indel
                    if indel > 0 and pr.query_position is not None:
                        qpos = pr.query_position
                        ins = pr.alignment.query_sequence[qpos + 1:qpos + 1 + indel]
                        if ins and re.fullmatch(r'[ACGTacgt]+', ins):
                            ins_counts[ins.upper()] += 1
                    elif indel < 0:
                        del_counts[-indel] += 1

                    if pr.query_position is None:
                        continue
                    b = pr.alignment.query_sequence[pr.query_position].upper()
                    if b in 'ACGT':
                        base_counts[b] += 1

                if dp < min_dp:
                    continue

                # SNV candidate
                altb, altc = None, 0
                for b, c in base_counts.most_common():
                    if b != refb:
                        altb, altc = b, c
                        break

                candidates = []
                if altb is not None:
                    af = altc / max(dp, 1)
                    if altc >= min_alt and af >= min_af:
                        candidates.append(('SNV', refb, altb, altc, af))

                # insertion candidates (anchor at pos0)
                if ins_counts:
                    ins, ic = ins_counts.most_common(1)[0]
                    af = ic / max(dp, 1)
                    if ic >= min_alt and af >= min_af:
                        candidates.append(('INS', refb, refb + ins, ic, af))

                # deletion candidates (anchor at pos0)
                if del_counts:
                    dlen, dc = del_counts.most_common(1)[0]
                    af = dc / max(dp, 1)
                    if dc >= min_alt and af >= min_af:
                        del_seq = fa.fetch(chrom, pos0 + 1, pos0 + 1 + dlen).upper()
                        if re.fullmatch(r'[ACGT]+', del_seq):
                            candidates.append(('DEL', refb + del_seq, refb, dc, af))

                if not candidates:
                    continue

                # Emit the strongest candidate by alt count
                candidates.sort(key=lambda x: x[3], reverse=True)
                _typ, ref, alt, ac, af = candidates[0]

                # crude QUAL: binomial test against sequencing error rate e=0.01
                e = 0.01
                pval = binom_sf(ac, dp, e)
                qual = phred_from_p(pval)

                # genotype from AF
                gt = '1/1' if af >= 0.8 else '0/1'
                ad_ref = max(dp - ac, 0)
                ad_alt = ac

                info = f'DP={dp};AC={ac};AF={af:.3f}'
                filt = 'PASS' if qual >= 20 else 'LowQual'
                f.write(f'{chrom}\t{pos0+1}\t.\t{ref}\t{alt}\t{qual:.2f}\t{filt}\t{info}\tGT:DP:AD\t{gt}:{dp}:{ad_ref},{ad_alt}\n')

    bam.close()
    fa.close()


def main():
    ensure_dirs()

    pipeline_lock = (DATA_DIR / 'pipeline_lock.txt').read_text(encoding='utf-8', errors='replace')
    resource_paths = parse_kv_file(DATA_DIR / 'resource_paths.txt')

    # reference
    ref = find_reference(resource_paths)
    ref_source = 'resource_paths.txt'
    if ref is None:
        ref = OUT_DIR / 'reference' / 'synthetic_ref.fa'
        ref_source = 'synthetic_generated'
        create_synthetic_reference(ref)

    # Index reference if needed
    if pysam is not None:
        if not Path(str(ref) + '.fai').exists():
            try:
                pysam.faidx(str(ref))
            except Exception:
                pass

    # Load manifest
    manifest = pd.read_csv(DATA_DIR / 'sample_manifest.csv')

    # Identify sample id and alignment path columns
    sample_col = None
    for c in manifest.columns:
        if c.lower() in {'sample', 'sample_id', 'id', 'smp', 'name'}:
            sample_col = c
            break
    if sample_col is None:
        sample_col = manifest.columns[0]

    aln_col = None
    for c in manifest.columns:
        lc = c.lower()
        if 'cram' in lc or 'bam' in lc or 'alignment' in lc or 'path' in lc:
            aln_col = c
            break
    if aln_col is None:
        # fallback: search for any cell containing .cram/.bam
        for c in manifest.columns:
            if manifest[c].astype(str).str.contains(r'\.(cram|bam)$', case=False, regex=True).any():
                aln_col = c
                break
    if aln_col is None:
        raise RuntimeError('Could not identify alignment path column in sample_manifest.csv')

    tool_versions = get_tool_versions()
    (META_DIR / 'tool_versions.json').write_text(json.dumps(tool_versions, indent=2), encoding='utf-8')
    (META_DIR / 'pipeline_lock.txt').write_text(pipeline_lock, encoding='utf-8')
    (META_DIR / 'resource_paths_parsed.json').write_text(json.dumps(resource_paths, indent=2), encoding='utf-8')
    (META_DIR / 'reference_used.json').write_text(json.dumps({'reference_fasta': str(ref), 'source': ref_source}, indent=2), encoding='utf-8')

    have_bcftools = which('bcftools') is not None and which('samtools') is not None

    simulation_records = []

    for i, row in manifest.iterrows():
        sample_id = str(row[sample_col])
        aln_path = Path(str(row[aln_col]))

        if not aln_path.exists():
            # simulate
            out_prefix = ALIGN_DIR / sample_id
            aln_path, variants = simulate_alignment(sample_id, ref, out_prefix, seed=1000 + i)
            simulation_records.append({
                'sample_id': sample_id,
                'alignment_path': str(aln_path),
                'reference_fasta': str(ref),
                'n_simulated_variants': len(variants),
                'variants': [vars(v) for v in variants],
            })

        out_vcf = VCF_DIR / f'{sample_id}.vcf'
        if out_vcf.exists() and out_vcf.stat().st_size > 0:
            continue

        if have_bcftools:
            try:
                bcftools_call(aln_path, ref, out_vcf)
                continue
            except Exception as e:
                # fall back to python
                sys.stderr.write(f'bcftools failed for {sample_id}: {e}\nFalling back to python caller.\n')

        python_call_variants(aln_path, ref, sample_id, out_vcf)

    if simulation_records:
        (OUT_DIR / 'simulated_inputs.json').write_text(json.dumps(simulation_records, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
