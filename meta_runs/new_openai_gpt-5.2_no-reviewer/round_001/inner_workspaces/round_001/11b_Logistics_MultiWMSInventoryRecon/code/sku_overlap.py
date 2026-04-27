import os
import pandas as pd

OUTPUT_DIR='outputs'

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    a=pd.read_csv('data/wms_alpha.csv')
    b=pd.read_csv('data/wms_beta.csv')

    # simple robust sku detection
    def find_sku_col(df):
        norm={c:''.join(ch.lower() if ch.isalnum() else '_' for ch in str(c)).strip('_') for c in df.columns}
        inv={v:k for k,v in norm.items()}
        for cand in ['sku','item','item_sku','item_id','product','product_id','material','part_number']:
            if cand in inv:
                return inv[cand]
        return df.columns[0]

    sku_a=find_sku_col(a)
    sku_b=find_sku_col(b)

    sa=set(a[sku_a].astype('string').str.strip().str.upper().dropna().unique())
    sb=set(b[sku_b].astype('string').str.strip().str.upper().dropna().unique())

    inter=sa & sb
    only_a=sa - sb
    only_b=sb - sa

    summary={
        'alpha_sku_col': sku_a,
        'beta_sku_col': sku_b,
        'alpha_unique_skus': len(sa),
        'beta_unique_skus': len(sb),
        'skus_in_both': len(inter),
        'skus_only_in_alpha': len(only_a),
        'skus_only_in_beta': len(only_b),
        'jaccard': len(inter)/len(sa|sb) if (sa|sb) else None,
    }

    pd.DataFrame([summary]).to_csv(os.path.join(OUTPUT_DIR,'sku_overlap_summary.csv'), index=False)

    pd.Series(sorted(list(only_a))[:200], name='sku').to_csv(os.path.join(OUTPUT_DIR,'skus_only_in_alpha_sample.csv'), index=False)
    pd.Series(sorted(list(only_b))[:200], name='sku').to_csv(os.path.join(OUTPUT_DIR,'skus_only_in_beta_sample.csv'), index=False)


if __name__=='__main__':
    main()
