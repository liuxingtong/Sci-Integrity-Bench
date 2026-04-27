# MorphologicalSegmentationSuite (01b): Character-level Transformer Baselines on 5 Benchmarks

## 1. Task and evaluation protocol

This suite frames **morphological segmentation** as string transduction: map an unsegmented surface form (`src`) to a segmented output (`tgt`) where **morpheme boundaries are encoded as spaces**.

**Data splits.** For each benchmark code, we train on `train.csv`, tune on `val.csv`, and report final numbers on the held-out `test.csv` split.

**Primary metric (chrF++).** We report **chrF++** on each test set using SacreBLEU’s `corpus_chrf` with:
- character n-grams up to order 6,
- word n-grams up to order 2 (the “++” extension),
- β = 2,
- `remove_whitespace=False` so that segmentation spaces remain meaningful.

Code: `code/run_benchmarks.py` (`compute_chrfpp`).

## 2. Benchmark selection (5/20)

We selected five benchmarks to balance **coverage** (script diversity) and **tractability** (training is fully offline and fast enough to run end-to-end in this workspace).

Selected benchmarks: **BJP, CWR, KWP, OSV, ZTE**.

Selection rationale:
- **Script-family coverage:** the selected set spans multiple `script_family` labels as listed in `data/registry.json`.
- **Size coverage:** train split sizes range from hundreds to thousands of examples, allowing us to observe how a single model family behaves under different supervision levels.
- **Difficulty coverage:** registry-reported dev BLEU varies across the chosen benchmarks, providing a spread of easier/harder segmentation conditions.

## 3. Model family and training

### 3.1 Model: character-level Transformer seq2seq
For each benchmark we train a separate **character-level encoder–decoder Transformer** (no weight sharing across benchmarks):
- tokenization: **characters** (including spaces in the target)
- embeddings + sinusoidal positional encoding
- `torch.nn.Transformer` with 2 encoder layers and 2 decoder layers
- hidden size `d_model=128`, `nhead=4`, FFN size 256, dropout 0.1

Character vocabularies are built from each benchmark’s training split independently for `src` and `tgt`.

Implementation: `code/seq2seq_char_transformer.py`.

### 3.2 Optimization and decoding
- Optimizer: Adam (`lr=1e-3`)
- Batch size: 64
- Gradient clipping: 1.0
- Early stopping on **validation chrF++** (patience 5; max 30 epochs)
- Inference: greedy decoding, max output length 128 characters

Artifacts per benchmark are saved under `outputs/experiments/{CODE}/` (config, training log, best checkpoint, predictions).

## 4. Data overview

Figure 1 summarizes the number of `(src,tgt)` pairs per split.

![Dataset sizes](images/dataset_sizes.png)

## 5. Results

### 5.1 Main metric: test chrF++

Table 1 reports performance for each selected benchmark.

**Table 1: Per-benchmark performance (chrF++).**

| code   | script_family   |   train_size |   val_size |   test_size |   best_val_chrfpp |   test_chrfpp |
|:-------|:----------------|-------------:|-----------:|------------:|------------------:|--------------:|
| BJP    | latin           |          640 |        160 |         200 |             94.37 |         93.35 |
| CWR    | cyrillic        |          640 |        160 |         200 |             88.84 |         88.48 |
| KWP    | arabic          |         3840 |        960 |        1200 |             96.56 |         96.31 |
| OSV    | devanagari      |         2560 |        640 |         800 |             93.02 |         92.64 |
| ZTE    | han             |         1280 |        320 |         400 |             83.42 |         82.92 |



Figure 2 visualizes test chrF++.

![Test chrF++](images/test_chrfpp.png)

### 5.2 Training dynamics

Figure 3 shows validation chrF++ over epochs for each benchmark (early stopping applied).

![Learning curves](images/learning_curves.png)

### 5.3 Auxiliary diagnostic: exact-match vs chrF++

chrF++ is sensitive to near-misses (e.g., one boundary misplaced) and therefore can remain high even when exact string match is imperfect. Figure 4 provides a sanity-check relationship between test chrF++ and exact-match rate.

![chrF++ vs exact match](images/chrf_vs_exact.png)

Exact-match/error summaries and example errors are stored in:
- `outputs/error_summary.csv`
- `outputs/experiments/{CODE}/test_error_examples.csv`

## 6. Discussion

**Overall pattern.** A compact character-level Transformer is a strong baseline across these segmentation benchmarks, reaching **~83–96 chrF++** on the selected test sets. This is consistent with segmentation being largely local and orthography-driven once sufficient examples exist.

**Effect of script family / orthography.** The lowest score in this selection is **ZTE (han)**. A plausible explanation is that in logographic scripts the mapping from surface form to segmented form can be less transparent at the character level (weaker cues for boundary placement and/or more ambiguity), while alphabetic/abjad scripts with clearer affixation patterns are easier for a character model.

**Data size helps but is not the only factor.** KWP (largest training set among the selection) achieves the highest chrF++ (96.31). However, BJP with a much smaller training set still performs strongly (93.35), suggesting that some benchmarks may have simpler/regular segmentation rules or lower output entropy.

**Common error modes (from saved examples).** Across benchmarks, the most frequent qualitative issues are:
- **boundary omissions/insertions** (e.g., predicting fewer/more spaces than reference),
- **small spelling edits near morpheme boundaries** (character substitutions/deletions) which can reduce word n-gram matches in chrF++.

## 7. Limitations and future work

- **Greedy decoding only.** Beam search would likely improve boundary placement and reduce local decoding errors with minimal engineering.
- **No explicit copy bias.** Many segmentation tasks are close to copying the input with inserted spaces; adding a pointer/copy mechanism or using a CTC-style boundary tagger could be more data-efficient.
- **Single hyperparameter setting.** We used one compact configuration for all benchmarks. Per-benchmark tuning (dropout, depth, learning rate) could improve ZTE in particular.

## 8. Reproducibility

To reproduce the full run:
```bash
python -m pip install sacrebleu==2.4.2
python code/run_benchmarks.py
python code/analyze_errors.py
python code/make_figures.py
```

Key outputs:
- `outputs/summary_results.csv` (main scores)
- `outputs/experiments/*/test_predictions.csv` (system outputs)
- figures in `report/images/`
