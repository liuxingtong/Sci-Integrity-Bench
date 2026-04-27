from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def main():
    reg = json.loads(Path('data/registry.json').read_text(encoding='utf-8'))
    if isinstance(reg, dict):
        items = [{'code': k, **v} for k, v in reg.items()]
    else:
        items = reg
    reg_df = pd.DataFrame(items)

    res_df = pd.read_csv('outputs/summary_results.csv')
    merged = res_df.merge(reg_df[['code','script_family','dev_bleu','path']], on='code', how='left')
    merged = merged[['code','script_family','train_size','val_size','test_size','dev_bleu','best_val_chrfpp','test_chrfpp']]
    merged.to_csv('outputs/selected_benchmarks_with_scores.csv', index=False)
    print(merged.to_string(index=False))


if __name__ == '__main__':
    main()
