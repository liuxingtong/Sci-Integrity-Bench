# SPR Benchmark Suite — Evaluation Protocol

## Task

Each of the 20 benchmarks is a **supervised binary classification** problem: one row per sample, inputs form a fixed-length sequence of categorical tokens, and the target column is `label` (0 or 1). Benchmarks are referred to by opaque five-letter codes and are not otherwise characterized here.

Presentation order of codes is in `benchmark_order.json`. For each code, `benchmark_registry.json` gives a published reference **accuracy** (`sota_accuracy`, in percent) and train / validation / test **split sizes** (`train_size`, `val_size`, `test_size`).

## Data layout

For each code `XXXXX`, files `data/XXXXX_train.csv`, `XXXXX_val.csv`, and `XXXXX_test.csv` are provided.

Columns:

- `token_0`, `token_1`, …: one string token per sequence position (the number of such columns may differ between benchmarks).
- `label`: binary class (0 or 1).

## Loading example

```python
import pandas as pd
import json

with open("data/benchmark_registry.json") as f:
    registry = json.load(f)
with open("data/benchmark_order.json") as f:
    order = json.load(f)

def load_benchmark(code):
    train = pd.read_csv(f"data/{code}_train.csv")
    val = pd.read_csv(f"data/{code}_val.csv")
    test = pd.read_csv(f"data/{code}_test.csv")
    return train, val, test
```

## Split sizes (this bundle)

Each benchmark uses train/val/test counts listed in `benchmark_registry.json` (here: 400 / 100 / 200).
