# -*- coding: utf-8 -*-
"""Basic EDA for CreditDefaultSPR."""

import json
import re
from collections import Counter

import numpy as np
import pandas as pd

from train_eval import infer_columns, guess_tokenizer


def seq_len_stats(seqs, tokenizer):
    lens = [len(tokenizer(s)) for s in seqs]
    arr = np.asarray(lens)
    return {
        "min": int(arr.min()),
        "p25": float(np.percentile(arr, 25)),
        "median": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p90": float(np.percentile(arr, 90)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "max": int(arr.max()),
        "mean": float(arr.mean()),
    }


def main():
    train = pd.read_csv("data/train.csv")
    val = pd.read_csv("data/val.csv")
    test = pd.read_csv("data/test.csv")

    seq_col, label_col = infer_columns(train)
    tokenizer = guess_tokenizer(train[seq_col])

    out = {
        "seq_col": seq_col,
        "label_col": label_col,
        "splits": {},
    }

    for name, df in [("train", train), ("val", val), ("test", test)]:
        seqs = df[seq_col].fillna("").astype(str).tolist()
        out["splits"][name] = {
            "n": int(len(df)),
            "pos_rate": float(df[label_col].mean()) if label_col in df.columns else None,
            "len_stats": seq_len_stats(seqs, tokenizer),
        }

    # vocab and token frequency on train
    ctr = Counter()
    for s in train[seq_col].fillna("").astype(str):
        ctr.update(tokenizer(s))
    out["vocab_size_train"] = int(len(ctr))
    out["top_tokens_train"] = ctr.most_common(30)

    with open("outputs/eda.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
