# -*- coding: utf-8 -*-
"""Generate report/report.md from computed outputs."""

import json
import re
from pathlib import Path


def extract_baseline(protocol_text: str):
    # heuristic: find lines with 'baseline' and a number
    baselines = []
    for line in protocol_text.splitlines():
        if 'baseline' in line.lower():
            nums = re.findall(r"[-+]?(?:\d*\.\d+|\d+\.\d*|\d+)", line)
            if nums:
                baselines.append((line.strip(), nums))
    return baselines


def fmt(x, nd=4):
    if x is None:
        return "NA"
    return f"{x:.{nd}f}"


def main():
    protocol = Path('data/protocol.md').read_text(encoding='utf-8')
    res = json.loads(Path('outputs/results.json').read_text(encoding='utf-8'))
    eda = json.loads(Path('outputs/eda.json').read_text(encoding='utf-8'))

    baseline_lines = extract_baseline(protocol)

    ov = res['overview']
    spr_def = res.get('spr_definition', {})
    best = res['best_val']
    test = res.get('test', {})

    # data stats
    tr = eda['splits']['train']
    va = eda['splits']['val']
    te = eda['splits']['test']

    metric_desc = "SPR (selection precision at a fixed review budget)"
    if spr_def.get('mode') == 'top_frac':
        metric_desc += f" computed as precision in the top {spr_def.get('frac')*100:.1f}% highest-risk examples."
    elif spr_def.get('mode') == 'top_k':
        metric_desc += f" computed as precision in the top-k={spr_def.get('k')} highest-risk examples."
    else:
        metric_desc += " computed as precision at R, where R is the number of positives in the evaluation set."

    params = best['params']

    md = []
    md.append("# CreditDefaultSPR — Default prediction from symbolic sequences\n")
    md.append("## 1. Task and evaluation protocol\n")
    md.append("We predict a binary default label from a single feature, `sym_seq`, a symbolic sequence describing account events. The official metric is defined in `data/protocol.md`.\n")
    md.append(f"**Primary metric:** {metric_desc}\n")
    md.append("\nFor completeness we also report AUROC, AUPRC, log loss, and Brier score.\n")

    if baseline_lines:
        md.append("\n**Protocol baseline(s) (verbatim lines containing 'baseline'):**\n")
        for line, _nums in baseline_lines[:10]:
            md.append(f"- {line}")
        md.append("")

    md.append("## 2. Data overview\n")
    md.append("Dataset split sizes and class balance:\n")
    md.append("\n| Split | N | Default rate | Median len | P95 len | Vocab (train) |\n|---:|---:|---:|---:|---:|---:|\n")
    md.append(
        f"| Train | {tr['n']} | {fmt(tr['pos_rate'],3)} | {tr['len_stats']['median']:.0f} | {tr['len_stats']['p95']:.0f} | {eda['vocab_size_train']} |\n"
        f"| Val | {va['n']} | {fmt(va['pos_rate'],3)} | {va['len_stats']['median']:.0f} | {va['len_stats']['p95']:.0f} | — |\n"
        f"| Test | {te['n']} | {fmt(te['pos_rate'],3)} | {te['len_stats']['median']:.0f} | {te['len_stats']['p95']:.0f} | — |\n"
    )
    md.append("\nFigure 1 visualizes the full length distributions.\n")
    md.append("\n![Sequence length distribution](images/length_distribution.png)\n")

    md.append("## 3. Methodology\n")
    md.append("### 3.1 Tokenization\n")
    md.append("We treat `sym_seq` as a token sequence. Tokenization is inferred from the most common delimiter in the training data (space/`|`/comma/semicolon); if no delimiter is common, a regex tokenizer is used.\n")

    md.append("### 3.2 Models\n")
    md.append("We use linear text models over TF–IDF n-grams, a strong baseline for symbolic sequences:\n")
    md.append("- **TF–IDF vectorizer** with n-gram range in {1..3}, `min_df` in {1,2,5}, and `max_df` in {0.9,1.0}.\n")
    md.append("- **Classifier**: either logistic regression (LibLinear) or a linear SVM with Platt scaling (CalibratedClassifierCV).\n")
    md.append("Hyperparameters are selected by maximizing the validation SPR.\n")

    md.append("### 3.3 Model selection diagnostics\n")
    md.append("Figure 2 shows the trade-off between validation SPR and AUROC across all tried configurations.\n")
    md.append("\n![Model selection landscape](images/model_selection.png)\n")

    md.append("## 4. Results\n")
    md.append("### 4.1 Best validation configuration\n")
    md.append("The best configuration on the validation set was:\n")
    md.append(f"- **Model kind:** `{params['kind']}`\n")
    md.append(f"- **Vectorizer params:** `{params['vec']}`\n")
    md.append(f"- **Model params:** `{params['model']}`\n")
    md.append("\nValidation performance (selected by SPR):\n")
    md.append(
        f"- SPR: **{fmt(best['val_spr'],4)}**\n"
        f"- AUROC: {fmt(best['val_roc_auc'],4)}\n"
        f"- AUPRC: {fmt(best['val_auprc'],4)}\n"
        f"- Log loss: {fmt(best['val_logloss'],4)}\n"
    )

    md.append("### 4.2 Test-set performance\n")
    if test:
        md.append(
            f"Test performance after retraining on **train+val** with the selected hyperparameters:\n\n"
            f"- SPR: **{fmt(test.get('spr'),4)}**\n"
            f"- AUROC: {fmt(test.get('roc_auc'),4)}\n"
            f"- AUPRC: {fmt(test.get('auprc'),4)}\n"
            f"- Log loss: {fmt(test.get('log_loss'),4)}\n"
            f"- Brier: {fmt(test.get('brier'),4)}\n"
        )
        md.append("\nDiscrimination and calibration plots on the test set are shown below.\n")
        md.append("\n![ROC curve](images/test_roc.png)\n")
        md.append("\n![Precision–Recall curve](images/test_pr.png)\n")
        md.append("\n![Calibration](images/test_calibration.png)\n")
        md.append("\n![Score distributions](images/test_score_distributions.png)\n")
    else:
        md.append("`test.csv` does not contain labels in this workspace, so test-set metrics cannot be computed. The script still outputs probabilistic predictions to `outputs/test_predictions.csv`.\n")

    # interpretability
    if Path('outputs/top_ngrams.csv').exists():
        md.append("### 4.3 Interpreting the linear model\n")
        md.append("For the logistic regression model we inspect the largest-magnitude coefficients (TF–IDF n-grams). Figure 3 shows the most default-associated and non-default-associated n-grams.\n")
        md.append("\n![Top positive n-grams](images/top_ngrams_pos.png)\n")
        md.append("\n![Top negative n-grams](images/top_ngrams_neg.png)\n")

    md.append("## 5. Discussion\n")
    md.append("A TF–IDF n-gram model provides a competitive, transparent baseline for symbolic sequence default prediction. Optimizing directly for SPR emphasizes ranking quality at the top of the score distribution (the operational region for manual review / risk triage), while AUROC/AUPRC summarize global discrimination.\n")
    md.append("\nPotential improvements (not implemented here) include: (i) character-level or subtoken n-grams if symbols have internal structure, (ii) sequence models (CNN/Transformer) with careful regularization, and (iii) cost-sensitive thresholding aligned with business constraints beyond a fixed review budget.\n")

    md.append("## 6. Reproducibility\n")
    md.append("All experiments are reproducible via:\n")
    md.append("```bash\npython code/train_eval.py\npython code/eda.py\npython code/generate_report.py\n```\n")

    Path('report/report.md').write_text("\n".join(md), encoding='utf-8')


if __name__ == '__main__':
    main()
