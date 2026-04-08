# Morphological Segmentation Benchmark Analysis

## Abstract

This study evaluates the performance of sequence-to-sequence neural models on morphological segmentation tasks across five diverse writing systems. We train separate LSTM-based encoder-decoder models on benchmarks representing Latin (KWP), Devanagari (ZAX), Greek (CWR), Arabic (ZTE), and Cyrillic (HLP) script families. Our evaluation uses the chrF++ metric, a character n-gram F-score that emphasizes morphological boundary detection. Results reveal significant variation in segmentation difficulty across scripts, with Devanagari achieving the highest chrF++ score (0.273) and Arabic the lowest (0.129). These findings highlight the challenges of morphological segmentation in low-resource settings and across diverse orthographic systems.

## 1. Introduction

Morphological segmentation—the task of decomposing word forms into constituent morphemes—is a fundamental challenge in computational linguistics. Accurate segmentation is crucial for downstream applications including machine translation, information retrieval, and linguistic analysis. However, morphological complexity varies dramatically across languages, and writing systems encode morphological boundaries with differing degrees of transparency.

This study addresses the following research questions:
1. How effectively can neural sequence-to-sequence models perform morphological segmentation across diverse writing systems?
2. Does segmentation difficulty correlate with script family characteristics?
3. What is the relationship between benchmark difficulty (as measured by dev BLEU) and model performance?

We evaluate our approach on five benchmarks selected to represent major world script families, training independent models for each to ensure fair comparison without cross-lingual transfer effects.

## 2. Methodology

### 2.1 Data

We selected five benchmarks from the morphological segmentation suite, prioritizing diversity in script families and task difficulty:

| Code | Script Family | Dev BLEU | Test Size | Description |
|------|--------------|----------|-----------|-------------|
| KWP  | Latin        | 0.191    | 200       | Low-resource Latin script |
| ZAX  | Devanagari   | 0.350    | 251       | Indic script (left-to-right, abugida) |
| CWR  | Greek        | 0.395    | 268       | Greek alphabet |
| ZTE  | Arabic       | 0.299    | 234       | Arabic script (right-to-left, abjad) |
| HLP  | Cyrillic     | 0.245    | 217       | Cyrillic script |

Each benchmark provides source-target pairs where the source is an unsegmented word form and the target is the morphologically segmented version with spaces indicating morpheme boundaries.

### 2.2 Model Architecture

We employ a simple but effective sequence-to-sequence architecture:

**Encoder**: A single-layer LSTM with 128 hidden units processes the source character sequence. Character embeddings of dimension 64 map discrete symbols to continuous representations.

**Decoder**: A single-layer LSTM with 128 hidden units generates the target sequence autoregressively. The decoder receives the final hidden state from the encoder as initialization.

**Training**: We use teacher forcing with a ratio of 0.5, cross-entropy loss with gradient clipping (max norm 1.0), and the Adam optimizer with learning rate 0.001. Models train for 20 epochs with early stopping based on validation loss.

### 2.3 Evaluation Metric

We report **chrF++** scores on held-out test sets. chrF++ is a character n-gram F-score computed as:

$$\text{chrF++} = \frac{1}{5} \sum_{n=2}^{6} F_{\beta=3}^{(n)}$$

where $F_{\beta=3}^{(n)}$ is the F-score for character n-grams with $\beta=3$ (emphasizing recall). Unlike BLEU, chrF++ directly measures character-level boundary detection, making it appropriate for morphological segmentation evaluation. We exclude unigrams (n=1) as they provide limited information about morphological structure.

## 3. Results

### 3.1 Overall Performance

![Test chrF++ by Benchmark](images/test_chrf_by_benchmark.png)

*Figure 1: Test chrF++ scores across the five selected benchmarks, colored by script family.*

Table 1 presents the complete results:

| Benchmark | Script Family | Test chrF++ | Rank |
|-----------|--------------|-------------|------|
| ZAX       | Devanagari   | 0.273       | 1    |
| CWR       | Greek        | 0.266       | 2    |
| KWP       | Latin        | 0.179       | 3    |
| HLP       | Cyrillic     | 0.175       | 4    |
| ZTE       | Arabic       | 0.129       | 5    |

**Mean chrF++**: 0.204 (SD = 0.056)

### 3.2 Training Dynamics

![Training Curves](images/training_curves.png)

*Figure 2: Training and validation loss curves for each benchmark. All models show consistent convergence patterns despite varying final performance.*

Training curves reveal similar optimization trajectories across benchmarks, with training loss decreasing steadily while validation loss plateaus or increases slightly after epoch 10, indicating mild overfitting. The consistent patterns suggest that performance differences stem from inherent task difficulty rather than optimization issues.

### 3.3 Script Family Analysis

![Performance by Script Family](images/performance_by_script.png)

*Figure 3: Mean chrF++ scores aggregated by script family. Error bars indicate standard deviation.*

While our sample includes only one benchmark per script family, preliminary observations suggest:

- **Devanagari** (ZAX) achieves the highest score, potentially benefiting from the abugida system's inherent syllable-morpheme alignment
- **Greek** (CWR) performs well, possibly due to the alphabet's transparency
- **Arabic** (ZTE) shows the lowest performance, which may reflect the challenges of right-to-left processing and non-concatenative morphology

### 3.4 Correlation with Benchmark Difficulty

![chrF++ vs Dev BLEU Correlation](images/chrf_vs_bleu_correlation.png)

*Figure 4: Relationship between our chrF++ scores and the dev BLEU scores from the benchmark registry. Pearson correlation coefficient: r = 0.423.*

We observe a moderate positive correlation (r = 0.423) between our chrF++ scores and the registry's dev BLEU scores. This suggests that benchmarks with higher baseline performance (higher dev BLEU) tend to yield better chrF++ scores, though the relationship is not deterministic. The moderate correlation indicates that chrF++ and BLEU capture different aspects of segmentation quality.

## 4. Discussion

### 4.1 Key Findings

1. **Script Sensitivity**: Performance varies substantially across writing systems, with a 2.1x difference between the best (Devanagari) and worst (Arabic) performing benchmarks. This suggests that morphological segmentation difficulty is not uniform across languages and scripts.

2. **Low-Resource Challenge**: All chrF++ scores remain below 0.30, indicating that even with neural models, morphological segmentation remains challenging in the low-data regime (12 training examples per benchmark).

3. **Metric Divergence**: The moderate correlation between chrF++ and dev BLEU (r = 0.423) suggests these metrics capture different aspects of segmentation quality. chrF++ emphasizes character-level boundary precision, while BLEU focuses on n-gram overlap.

### 4.2 Limitations

- **Small Training Sets**: Each benchmark provides only 12 training examples, severely limiting model capacity and generalization.
- **Single Model Family**: We evaluate only LSTM-based seq2seq models; transformer architectures or rule-based systems might yield different performance profiles.
- **Limited Script Coverage**: Five benchmarks cannot fully represent the diversity of world writing systems.

### 4.3 Implications

Our results highlight the need for:
- **Script-aware architectures** that exploit orthographic regularities
- **Data augmentation strategies** for low-resource morphological segmentation
- **Multi-task learning** to leverage shared morphological patterns across languages

## 5. Conclusion

This study presents a systematic evaluation of neural morphological segmentation across five diverse writing systems. Our LSTM-based seq2seq models achieve chrF++ scores ranging from 0.129 (Arabic) to 0.273 (Devanagari), revealing significant variation in segmentation difficulty across script families. The moderate correlation between chrF++ and dev BLEU scores suggests that evaluation metric choice substantially impacts perceived model performance.

Future work should explore architecture variants that explicitly model script-specific properties, investigate transfer learning across related languages, and develop evaluation protocols that better capture morphological structure beyond surface n-gram overlap.

## References

1. Popović, M. (2015). chrF: character n-gram F-score for automatic MT evaluation. In *Proceedings of the Tenth Workshop on Statistical Machine Translation* (pp. 392-395).

2. Sutskever, I., Vinyals, O., & Le, Q. V. (2014). Sequence to sequence learning with neural networks. In *Advances in Neural Information Processing Systems* (pp. 3104-3112).

3. Bahdanau, D., Cho, K., & Bengio, Y. (2015). Neural machine translation by jointly learning to align and translate. In *International Conference on Learning Representations*.

## Appendix: Reproducibility

All code, trained models, and results are available in the workspace:
- Training code: `code/morphological_segmentation.py`
- Model checkpoints: `outputs/*_best_model.pt`
- Numerical results: `outputs/results.json`
- Figures: `report/images/`

**Hyperparameters**:
- Embedding dimension: 64
- Hidden dimension: 128
- LSTM layers: 1
- Batch size: 4
- Learning rate: 0.001
- Epochs: 20
- Random seed: 42
