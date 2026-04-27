from __future__ import annotations

from pathlib import Path
import pandas as pd


def main():
    exp_root = Path('outputs/experiments')
    rows=[]
    for code_dir in exp_root.iterdir():
        if not code_dir.is_dir():
            continue
        code=code_dir.name
        p=code_dir/'test_predictions.csv'
        if not p.exists():
            continue
        df=pd.read_csv(p)
        df['exact']=df.pred==df.ref
        exact=df.exact.mean()
        # crude boundary count differences
        df['ref_segs']=df.ref.str.count(' ')+1
        df['pred_segs']=df.pred.str.count(' ')+1
        df['seg_diff']=df.pred_segs-df.ref_segs
        rows.append({'code':code,'exact_match_rate':exact,'mean_seg_diff':df.seg_diff.mean()})
        # save a few hardest examples (non-exact)
        bad=df[~df.exact].copy()
        if len(bad):
            # prioritize by largest seg diff magnitude
            bad=bad.sort_values(by='seg_diff', key=lambda s: s.abs(), ascending=False).head(15)
            bad[['src','ref','pred','seg_diff']].to_csv(code_dir/'test_error_examples.csv', index=False)
    out=pd.DataFrame(rows).sort_values('code')
    out.to_csv('outputs/error_summary.csv', index=False)
    print(out.to_string(index=False))


if __name__=='__main__':
    main()
