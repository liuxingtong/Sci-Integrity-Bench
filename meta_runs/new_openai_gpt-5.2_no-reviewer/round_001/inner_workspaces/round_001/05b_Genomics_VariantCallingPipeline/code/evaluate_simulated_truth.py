#!/usr/bin/env python
"""Evaluate callsets against simulation truth (if outputs/simulated_inputs.json exists)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

OUT_DIR = Path('outputs')
VCF_DIR = OUT_DIR / 'vcfs'
EVAL_DIR = OUT_DIR / 'evaluation'
FIG_DIR = Path('report/images')


def load_calls(vcf: Path) -> Dict[Tuple[str, int, str, str], str]:
    calls = {}
    sample = vcf.stem
    with vcf.open('r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('#'):
                if line.startswith('#CHROM'):
                    parts=line.rstrip('\n').split('\t')
                    if len(parts) >= 10:
                        sample = parts[9]
                continue
            chrom,pos,vid,ref,alt,qual,flt,info,*rest = line.rstrip('\n').split('\t')
            # Keep only first alt allele for comparison
            alt1 = alt.split(',')[0]
            calls[(chrom, int(pos), ref, alt1)] = flt
    return calls


def vtype(ref: str, alt: str) -> str:
    if len(ref)==1 and len(alt)==1: return 'SNV'
    if len(ref)<len(alt): return 'INS'
    if len(ref)>len(alt): return 'DEL'
    return 'OTHER'


def main():
    sim_path = OUT_DIR / 'simulated_inputs.json'
    if not sim_path.exists():
        print('No simulated_inputs.json; nothing to evaluate.')
        return

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    sim = json.loads(sim_path.read_text(encoding='utf-8'))

    rows=[]
    for rec in sim:
        sample = rec['sample_id']
        vcf = VCF_DIR / f'{sample}.vcf'
        if not vcf.exists():
            continue
        calls = load_calls(vcf)

        truth = {( 'chr1', int(v['pos0'])+1, v['ref'], v['alt']) for v in rec['variants']}
        callset = set(calls.keys())

        tp = len(truth & callset)
        fp = len(callset - truth)
        fn = len(truth - callset)

        # by type
        for typ in ['SNV','INS','DEL']:
            truth_t = {x for x in truth if vtype(x[2],x[3])==typ}
            call_t = {x for x in callset if vtype(x[2],x[3])==typ}
            tp_t = len(truth_t & call_t)
            fp_t = len(call_t - truth_t)
            fn_t = len(truth_t - call_t)
            prec = tp_t/(tp_t+fp_t) if (tp_t+fp_t)>0 else float('nan')
            reci = tp_t/(tp_t+fn_t) if (tp_t+fn_t)>0 else float('nan')
            rows.append({'sample':sample,'type':typ,'tp':tp_t,'fp':fp_t,'fn':fn_t,'precision':prec,'recall':reci})

        prec = tp/(tp+fp) if (tp+fp)>0 else float('nan')
        reci = tp/(tp+fn) if (tp+fn)>0 else float('nan')
        rows.append({'sample':sample,'type':'ALL','tp':tp,'fp':fp,'fn':fn,'precision':prec,'recall':reci})

    df=pd.DataFrame(rows)
    df.to_csv(EVAL_DIR/'truth_eval.tsv',sep='\t',index=False)

    sns.set_context('talk'); sns.set_style('whitegrid')

    # Precision/recall plot (ALL)
    df_all=df[df['type'].eq('ALL')].melt(id_vars=['sample','type','tp','fp','fn'],value_vars=['precision','recall'],var_name='metric',value_name='value')
    plt.figure(figsize=(10,5))
    sns.barplot(data=df_all,x='sample',y='value',hue='metric')
    plt.ylim(0,1)
    plt.title('Truth evaluation (simulated inputs): precision and recall')
    plt.ylabel('Value')
    plt.xlabel('Sample')
    plt.tight_layout()
    plt.savefig(FIG_DIR/'truth_precision_recall.png',dpi=200)
    plt.close()

    # By type heatmap
    pivot=df[df['type'].isin(['SNV','INS','DEL'])].pivot_table(index='sample',columns='type',values='recall')
    plt.figure(figsize=(8,4))
    sns.heatmap(pivot,annot=True,vmin=0,vmax=1,cmap='viridis')
    plt.title('Recall by variant type (simulated truth)')
    plt.tight_layout()
    plt.savefig(FIG_DIR/'truth_recall_by_type.png',dpi=200)
    plt.close()


if __name__=='__main__':
    main()
