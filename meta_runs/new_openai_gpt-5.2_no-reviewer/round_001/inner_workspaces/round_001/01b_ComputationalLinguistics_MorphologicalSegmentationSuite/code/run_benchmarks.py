"""Train char-level Transformer seq2seq models on 5 selected benchmarks.

Outputs:
- outputs/experiments/{CODE}/
  - config.json
  - train_log.jsonl
  - best_model.pt
  - val_predictions.csv
  - test_predictions.csv
  - scores.json
- outputs/summary_results.csv

Also generates figures under report/images/ via code/make_figures.py.

Reproducible: fixed random seed per run.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from seq2seq_char_transformer import CharVocab, TransformerSeq2Seq, make_batches


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def compute_chrfpp(preds: List[str], refs: List[str]) -> float:
    """chrF++ (character n-gram F-score with word n-grams up to 2).

    Uses sacrebleu if available. Returns score in [0,100].
    """
    try:
        import sacrebleu

        # corpus_chrf expects list of hypotheses and list-of-list references
        # Keep whitespace: in segmentation, boundaries are encoded as spaces.
        score = sacrebleu.corpus_chrf(
            preds,
            [refs],
            char_order=6,
            word_order=2,  # chrF++
            beta=2,
            remove_whitespace=False,
        ).score
        return float(score)
    except Exception:
        # lightweight fallback: character-only F-score (chrF) as approximation
        # Documented in report if used; but we attempt to ensure sacrebleu is installed.
        from collections import Counter

        def ngrams(s: str, n: int):
            return [s[i : i + n] for i in range(len(s) - n + 1)] if len(s) >= n else []

        # compute averaged F over n=1..6 with beta=2
        beta2 = 4.0
        total_f = 0.0
        for n in range(1, 7):
            match = 0
            pred_count = 0
            ref_count = 0
            for p, r in zip(preds, refs):
                pn = Counter(ngrams(p, n))
                rn = Counter(ngrams(r, n))
                pred_count += sum(pn.values())
                ref_count += sum(rn.values())
                match += sum((pn & rn).values())
            prec = match / pred_count if pred_count else 0.0
            rec = match / ref_count if ref_count else 0.0
            denom = beta2 * prec + rec
            f = (1 + beta2) * prec * rec / denom if denom else 0.0
            total_f += f
        return 100.0 * total_f / 6.0


@dataclass
class Config:
    code: str
    seed: int = 13
    d_model: int = 128
    nhead: int = 4
    num_layers: int = 2
    dim_feedforward: int = 256
    dropout: float = 0.1
    batch_size: int = 64
    lr: float = 1e-3
    max_epochs: int = 30
    patience: int = 5
    max_decode_len: int = 128
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


def load_split(code: str, split: str) -> pd.DataFrame:
    path = Path("data") / "corpora" / code / f"{split}.csv"
    df = pd.read_csv(path)
    assert set(df.columns) >= {"src", "tgt"}
    df = df[["src", "tgt"]].astype(str)
    return df


def build_vocabs(train_df: pd.DataFrame) -> Tuple[CharVocab, CharVocab]:
    src_vocab = CharVocab.build(train_df.src.tolist())
    tgt_vocab = CharVocab.build(train_df.tgt.tolist())
    return src_vocab, tgt_vocab


def encode_pairs(df: pd.DataFrame, src_vocab: CharVocab, tgt_vocab: CharVocab) -> List[Tuple[List[int], List[int]]]:
    pairs = []
    for s, t in df[["src", "tgt"]].itertuples(index=False):
        src_ids = src_vocab.encode(s, add_bos=False, add_eos=True)
        tgt_ids = tgt_vocab.encode(t, add_bos=True, add_eos=True)
        pairs.append((src_ids, tgt_ids))
    return pairs


@torch.no_grad()
def predict_df(model: TransformerSeq2Seq, df: pd.DataFrame, src_vocab: CharVocab, tgt_vocab: CharVocab, cfg: Config) -> pd.DataFrame:
    device = torch.device(cfg.device)
    pairs = encode_pairs(df, src_vocab, tgt_vocab)
    # batch by fixed size; we only need src
    preds = []
    refs = []
    srcs = []

    # simple batching
    for start in range(0, len(pairs), cfg.batch_size):
        batch_pairs = pairs[start : start + cfg.batch_size]
        src_seqs = [p[0] for p in batch_pairs]
        # pad
        max_len = max(len(s) for s in src_seqs)
        src = torch.full((len(src_seqs), max_len), src_vocab.pad_id, dtype=torch.long, device=device)
        for i, s in enumerate(src_seqs):
            src[i, : len(s)] = torch.tensor(s, dtype=torch.long, device=device)

        ys = model.greedy_decode(src, bos_id=tgt_vocab.bos_id, eos_id=tgt_vocab.eos_id, max_len=cfg.max_decode_len)
        for i in range(ys.size(0)):
            pred = tgt_vocab.decode(ys[i].tolist(), stop_at_eos=True, skip_special=True)
            preds.append(pred)

    refs = df.tgt.tolist()
    srcs = df.src.tolist()
    out = pd.DataFrame({"src": srcs, "ref": refs, "pred": preds})
    return out


def train_one(code: str, out_dir: Path, cfg: Config) -> Dict:
    set_seed(cfg.seed)

    train_df = load_split(code, "train")
    val_df = load_split(code, "val")
    test_df = load_split(code, "test")

    src_vocab, tgt_vocab = build_vocabs(train_df)

    train_pairs = encode_pairs(train_df, src_vocab, tgt_vocab)
    val_pairs = encode_pairs(val_df, src_vocab, tgt_vocab)

    device = torch.device(cfg.device)
    model = TransformerSeq2Seq(
        src_vocab_size=len(src_vocab.stoi),
        tgt_vocab_size=len(tgt_vocab.stoi),
        d_model=cfg.d_model,
        nhead=cfg.nhead,
        num_layers=cfg.num_layers,
        dim_feedforward=cfg.dim_feedforward,
        dropout=cfg.dropout,
        max_len=max(cfg.max_decode_len, 256),
        pad_id=tgt_vocab.pad_id,
    ).to(device)

    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    loss_fn = nn.CrossEntropyLoss(ignore_index=tgt_vocab.pad_id)

    best_val = -1e9
    best_path = out_dir / "best_model.pt"
    bad_epochs = 0

    log_path = out_dir / "train_log.jsonl"
    log_f = open(log_path, "w", encoding="utf-8")

    for epoch in range(1, cfg.max_epochs + 1):
        model.train()
        total_loss = 0.0
        n_tokens = 0

        for batch in make_batches(train_pairs, pad_id=src_vocab.pad_id, batch_size=cfg.batch_size, shuffle=True, device=device):
            opt.zero_grad(set_to_none=True)
            logits = model(batch.src, batch.tgt_inp)
            # logits: (B, T, V), tgt_out: (B, T)
            loss = loss_fn(logits.reshape(-1, logits.size(-1)), batch.tgt_out.reshape(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            # approximate token count (non-pad)
            tok = batch.tgt_out.ne(tgt_vocab.pad_id).sum().item()
            total_loss += loss.item() * tok
            n_tokens += tok

        train_loss = total_loss / max(1, n_tokens)

        # validation chrF++ via decoding (costly but datasets are small)
        val_pred_df = predict_df(model, val_df, src_vocab, tgt_vocab, cfg)
        val_chrf = compute_chrfpp(val_pred_df.pred.tolist(), val_pred_df.ref.tolist())

        rec = {
            "code": code,
            "epoch": epoch,
            "train_loss": train_loss,
            "val_chrfpp": val_chrf,
        }
        log_f.write(json.dumps(rec) + "\n")
        log_f.flush()

        if val_chrf > best_val + 1e-6:
            best_val = val_chrf
            bad_epochs = 0
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "src_vocab": src_vocab.stoi,
                    "tgt_vocab": tgt_vocab.stoi,
                    "cfg": asdict(cfg),
                    "best_val_chrfpp": best_val,
                    "epoch": epoch,
                },
                best_path,
            )
        else:
            bad_epochs += 1
            if bad_epochs >= cfg.patience:
                break

    log_f.close()

    # Load best model for final eval
    ckpt = torch.load(best_path, map_location=device)
    src_vocab = CharVocab(ckpt["src_vocab"])
    tgt_vocab = CharVocab(ckpt["tgt_vocab"])
    model.load_state_dict(ckpt["model_state"])

    val_pred_df = predict_df(model, val_df, src_vocab, tgt_vocab, cfg)
    test_pred_df = predict_df(model, test_df, src_vocab, tgt_vocab, cfg)

    val_chrf = compute_chrfpp(val_pred_df.pred.tolist(), val_pred_df.ref.tolist())
    test_chrf = compute_chrfpp(test_pred_df.pred.tolist(), test_pred_df.ref.tolist())

    val_pred_df.to_csv(out_dir / "val_predictions.csv", index=False)
    test_pred_df.to_csv(out_dir / "test_predictions.csv", index=False)

    scores = {
        "code": code,
        "best_val_chrfpp": float(val_chrf),
        "test_chrfpp": float(test_chrf),
        "train_size": int(len(train_df)),
        "val_size": int(len(val_df)),
        "test_size": int(len(test_df)),
        "device": cfg.device,
    }
    with open(out_dir / "scores.json", "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)

    return scores


def main():
    # Fixed selection (documented in report).
    selected = [
        "BJP",
        "CWR",
        "KWP",
        "OSV",
        "ZTE",
    ]

    out_root = Path("outputs") / "experiments"
    out_root.mkdir(parents=True, exist_ok=True)

    all_scores = []
    for code in selected:
        out_dir = out_root / code
        out_dir.mkdir(parents=True, exist_ok=True)
        cfg = Config(code=code)
        with open(out_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(asdict(cfg), f, indent=2)
        scores = train_one(code, out_dir, cfg)
        all_scores.append(scores)

    df = pd.DataFrame(all_scores).sort_values("code")
    df.to_csv(Path("outputs") / "summary_results.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
