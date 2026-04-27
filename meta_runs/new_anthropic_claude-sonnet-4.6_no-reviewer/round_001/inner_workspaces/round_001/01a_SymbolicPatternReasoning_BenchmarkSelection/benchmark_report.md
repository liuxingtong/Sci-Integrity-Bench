# SPR Benchmark Report

## Selection Rationale

Four benchmarks were selected from the 20-benchmark SPR suite to maximize diversity across difficulty levels and sequence complexity:

| Code  | SOTA (%) | Seq. Length | Vocab Size | Rationale |
|-------|----------|-------------|------------|-----------|
| OQMEA | 92.9     | 5 tokens    | 6 types    | High-SOTA reference benchmark |
| ILULR | 78.0     | 4 tokens    | 4 types    | Medium difficulty, shortest sequence |
| RHHQD | 70.5     | 8 tokens    | 9 types    | Below-average SOTA, medium sequence |
| FDLOT | 60.4     | 12 tokens   | 16 types   | Hardest benchmark, longest sequence |

Selection criteria: (1) span the full SOTA range (60.4%–92.9%), (2) cover diverse sequence lengths (4–12 tokens), (3) include varying vocabulary sizes to probe combinatorial complexity.

## Test Accuracy vs Published SOTA

| Code  | SOTA (%) | Test Acc. (%) | Δ (pp)  | Best Model            | Feature Approach     |
|-------|----------|---------------|---------|-----------------------|----------------------|
| OQMEA | 92.9     | 51.0          | −41.9   | SVM (RBF, C=1.0)      | Ordinal Encoding     |
| ILULR | 78.0     | **90.5**      | **+12.5** | Decision Tree (∞ depth) | Rich Features      |
| RHHQD | 70.5     | 56.0          | −14.5   | GBT (100 est., d=3)   | Ordinal Encoding     |
| FDLOT | 60.4     | 50.0          | −10.4   | Extra Trees (100 est.)| Rich Features        |

*pp = percentage points. Models trained on Train split, selected by Validation accuracy, evaluated once on Test.*

## Brief Discussion

**ILULR (+12.5 pp above SOTA):** The only benchmark where standard ML substantially exceeds published SOTA. With just 4 token positions and a 4-type vocabulary, the combinatorial space (4⁴ = 256 sequences) is small enough for a decision tree to learn the exact rule from 400 training examples. Rich feature engineering (bigrams, same-token indicators) exposed the underlying pattern directly.

**OQMEA (−41.9 pp below SOTA):** The most striking failure — despite having the highest SOTA and only 5 token positions, all 14 candidate models cluster near random chance (44–55% validation accuracy). The classification rule appears to require a form of symbolic reasoning (e.g., non-adjacent dependencies, exact relational matching) that neither ordinal encoding nor engineered features can capture.

**RHHQD (−14.5 pp) and FDLOT (−10.4 pp):** Both show negative gaps, with FDLOT's smaller absolute gap despite lower SOTA suggesting near-chance benchmarks are inherently noisy. The 9- and 16-type vocabularies introduce additional color dimensions (blue, yellow) absent in easier benchmarks, likely requiring color-specific relational reasoning beyond our feature representations.

**Key insight:** SOTA accuracy is not a reliable proxy for learnability by standard ML. OQMEA (highest SOTA) is the hardest to learn; ILULR (medium SOTA) is the easiest. The hidden symbolic rule structure — not sequence length or vocabulary size — is the primary determinant of learnability.
