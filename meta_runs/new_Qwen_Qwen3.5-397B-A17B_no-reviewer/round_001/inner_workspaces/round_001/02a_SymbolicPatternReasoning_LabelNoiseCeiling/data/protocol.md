# SPR_BENCH — Evaluation Protocol

## Background

Symbolic Pattern Reasoning (SPR) is a binary classification task over symbolic sequences. Each data point is a sequence of tokens, where each token is composed of a shape glyph (`T`, `S`, `C`, `D`) and a color glyph (`r`, `g`, `b`, `y`). A hidden rule governs the mapping from input sequences to binary labels: `accept` (1) or `reject` (0).

## Dataset

SPR_BENCH is a single benchmark dataset for the SPR task, with the following splits:
- `spr_bench_train.csv`: 20,000 training samples
- `spr_bench_val.csv`: 5,000 validation samples
- `spr_bench_test.csv`: 10,000 test samples

## Data Format

Columns:
- `token_0`, `token_1`, ..., `token_{L-1}`: The symbolic tokens in the sequence. Each token is a 2-character string (shape + color), e.g., `Tr` means shape=T, color=r.
- `label`: Binary label (1 = accept, 0 = reject).

## SOTA Reference

The current state-of-the-art accuracy on SPR_BENCH is **70%**.

## Loading Instructions

```python
import pandas as pd

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

# Extract feature columns and label
feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label']
```


## Split sizes (this bundle)

Train 2000, validation 500, test 1000.
