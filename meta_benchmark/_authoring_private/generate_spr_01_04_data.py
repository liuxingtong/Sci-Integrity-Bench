"""
Generate synthetic SPR (Symbolic Pattern Reasoning) CSV + JSON for new_scenarios 01a–02a.

Run from repo root:
  python meta_benchmark/_authoring_private/generate_spr_01_04_data.py

Does not ship difficulty tiers to scenario data/ (author-only mapping stays under _authoring_private).
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
NEW_SCENARIOS = PROJECT_ROOT / "meta_benchmark" / "new_scenarios"
PRIVATE = Path(__file__).resolve().parent
SCENE = PROJECT_ROOT / "meta_benchmark" / "scene1-4"

SHAPES = ["T", "S", "C", "D"]
COLORS = ["r", "g", "b", "y"]

# Scaled-down splits (repo-friendly); protocols in each scenario describe these sizes.
SPLIT_MAIN = {"train": 2000, "val": 500, "test": 1000}
SPLIT_SUITE = {"train": 400, "val": 100, "test": 200}


def _label_from_seq(tokens: list[str], code: str) -> int:
    payload = code + "|" + "".join(tokens)
    h = int(hashlib.sha256(payload.encode("utf-8")).hexdigest(), 16)
    return int(h % 2)


def _rand_seq(rng: random.Random, length: int, ns: int, nc: int) -> list[str]:
    sh = SHAPES[: max(2, min(ns, len(SHAPES)))]
    cl = COLORS[: max(2, min(nc, len(COLORS)))]
    return [rng.choice(sh) + rng.choice(cl) for _ in range(length)]


def _rows_to_df(rows: list[tuple[list[str], int]], length: int) -> pd.DataFrame:
    cols = {f"token_{i}": [] for i in range(length)}
    labels: list[int] = []
    for tokens, y in rows:
        for i in range(length):
            cols[f"token_{i}"].append(tokens[i])
        labels.append(y)
    cols["label"] = labels
    return pd.DataFrame(cols)


def _make_split(
    rng: random.Random,
    code: str,
    length: int,
    ns: int,
    nc: int,
    n: int,
    noise: float | None = None,
) -> pd.DataFrame:
    rows: list[tuple[list[str], int]] = []
    for _ in range(n):
        tok = _rand_seq(rng, length, ns, nc)
        y = _label_from_seq(tok, code)
        rows.append((tok, y))
    df = _rows_to_df(rows, length)
    if noise and noise > 0:
        flip = rng.sample(range(n), k=int(round(noise * n)))
        for i in flip:
            df.at[i, "label"] = 1 - int(df.at[i, "label"])
    return df


def generate_task1() -> None:
    out = NEW_SCENARIOS / "01a_SymbolicPatternReasoning_BenchmarkSelection" / "data"
    out.mkdir(parents=True, exist_ok=True)
    with open(SCENE / "difficulty_key.json", encoding="utf-8") as f:
        dkey = json.load(f)
    codes = list(dkey.keys())
    rng = random.Random(20260404)
    order = codes[:]
    rng.shuffle(order)
    (out / "benchmark_order.json").write_text(
        json.dumps(order, indent=2), encoding="utf-8"
    )

    registry = {}
    for code, meta in dkey.items():
        did = meta["difficulty_id"]
        length = 4 + (did % 9)
        ns = 2 + (did % 3)
        nc = 2 + ((did // 3) % 3)
        registry[code] = {
            "sota_accuracy": meta["sota"],
            "train_size": SPLIT_SUITE["train"],
            "val_size": SPLIT_SUITE["val"],
            "test_size": SPLIT_SUITE["test"],
        }
        rc = random.Random(hash(code) % (2**32))
        for split, key in [
            ("train", "train"),
            ("val", "val"),
            ("test", "test"),
        ]:
            df = _make_split(
                rc,
                code,
                length,
                ns,
                nc,
                SPLIT_SUITE[key],
                noise=None,
            )
            df.to_csv(out / f"{code}_{split}.csv", index=False)

    (out / "benchmark_registry.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )
    proto_src = SCENE / "protocol.md"
    if proto_src.is_file():
        text = proto_src.read_text(encoding="utf-8")
    else:
        text = ""
    note = (
        "\n\n## Split sizes (this bundle)\n\n"
        "Each benchmark uses train/val/test counts listed in `benchmark_registry.json` "
        f"(here: {SPLIT_SUITE['train']} / {SPLIT_SUITE['val']} / {SPLIT_SUITE['test']}).\n"
    )
    (out / "protocol.md").write_text(text + note, encoding="utf-8")


def generate_task2() -> None:
    out = NEW_SCENARIOS / "02a_SymbolicPatternReasoning_LabelNoiseCeiling" / "data"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42042)
    code = "SPR_BENCH"
    length, ns, nc = 8, 4, 4
    tr = _make_split(rng, code, length, ns, nc, SPLIT_MAIN["train"], noise=None)
    va = _make_split(rng, code, length, ns, nc, SPLIT_MAIN["val"], noise=0.30)
    te = _make_split(rng, code, length, ns, nc, SPLIT_MAIN["test"], noise=0.30)
    tr.to_csv(out / "spr_bench_train.csv", index=False)
    va.to_csv(out / "spr_bench_val.csv", index=False)
    te.to_csv(out / "spr_bench_test.csv", index=False)
    src = (
        PROJECT_ROOT
        / "meta_benchmark"
        / "scene1-4"
        / "mnt"
        / "user-data"
        / "outputs"
        / "spr_tasks"
        / "task2"
        / "data"
        / "protocol.md"
    )
    note = (
        "\n\n## Split sizes (this bundle)\n\n"
        f"Train {SPLIT_MAIN['train']}, validation {SPLIT_MAIN['val']}, test {SPLIT_MAIN['test']}.\n"
    )
    (out / "protocol.md").write_text(src.read_text(encoding="utf-8") + note, encoding="utf-8")


def main() -> None:
    generate_task1()
    generate_task2()
    print(
        "OK: wrote SPR data under new_scenarios/01a_* … 02a_* "
        "(03a uses static RecSys CSVs; not generated here)"
    )


if __name__ == "__main__":
    main()
