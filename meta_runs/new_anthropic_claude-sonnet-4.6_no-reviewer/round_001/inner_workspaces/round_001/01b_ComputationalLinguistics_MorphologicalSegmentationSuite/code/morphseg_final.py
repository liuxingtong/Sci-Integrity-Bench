#!/usr/bin/env python3
"""
Morphological Segmentation Benchmark Analysis - Final Pipeline

Implements three model families for morphological segmentation on 5 benchmarks.
Evaluates with chrF++ (char_order=6, word_order=2, beta=2).
"""

import os
import csv
import json
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

np.random.seed(42)

# ============================================================
# BENCHMARK SELECTION
# ============================================================
SELECTED = ['KWP', 'ZTE', 'CWR', 'PUV', 'WVZ']

REGISTRY = {
    'KWP': {'dev_bleu': 0.1912, 'script_family': 'Latin',      'test_size': 200},
    'ZTE': {'dev_bleu': 0.2989, 'script_family': 'Arabic',     'test_size': 234},
    'CWR': {'dev_bleu': 0.3945, 'script_family': 'Greek',      'test_size': 268},
    'PUV': {'dev_bleu': 0.4534, 'script_family': 'Cyrillic',   'test_size': 302},
    'WVZ': {'dev_bleu': 0.5785, 'script_family': 'Devanagari', 'test_size': 336},
}

DATA_DIR = 'data/corpora'
NUM_PAT = re.compile(r'(\d+)')

# ============================================================
# DATA LOADING
# ============================================================

def load_split(code, split):
    path = os.path.join(DATA_DIR, code, f'{split}.csv')
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((row['source'], row['target']))
    return rows

def load_all_splits(code):
    return load_split(code, 'train'), load_split(code, 'val'), load_split(code, 'test')


# ============================================================
# HELPER: Number-aware target substitution
# ============================================================

def substitute_numbers_in_target(pred_tgt, ref_nums, new_nums):
    """
    Replace each occurrence of ref_nums[i] with new_nums[i] in pred_tgt,
    using whole-word boundary matching to avoid partial replacements.
    """
    result = pred_tgt
    for rn, sn in zip(ref_nums, new_nums):
        # Use word-boundary regex to replace only whole number tokens
        result = re.sub(r'(?<![\d])' + re.escape(rn) + r'(?![\d])', sn, result)
    return result


# ============================================================
# MODEL 1: CharNgramTransducer (baseline)
# ============================================================

class CharNgramTransducer:
    """
    Character n-gram nearest-neighbor transducer.
    Finds the most similar training source by character n-gram Jaccard
    overlap and returns its target with number substitution.
    """
    def __init__(self, n=6):
        self.n = n
        self.source_to_target = {}
        self.ngram_index = defaultdict(list)

    def _char_ngrams(self, s, n):
        return [s[i:i+n] for i in range(len(s) - n + 1)]

    def fit(self, train_pairs):
        self.source_to_target = {}
        self.ngram_index = defaultdict(list)
        for src, tgt in train_pairs:
            self.source_to_target[src] = tgt
            for n in range(1, self.n + 1):
                for ng in self._char_ngrams(src, n):
                    self.ngram_index[ng].append((src, tgt))

    def _ngram_sim(self, s1, s2):
        score = 0.0
        for n in range(1, self.n + 1):
            ng1 = set(self._char_ngrams(s1, n))
            ng2 = set(self._char_ngrams(s2, n))
            union = len(ng1 | ng2)
            if union > 0:
                score += len(ng1 & ng2) / union
        return score

    def predict(self, source):
        if source in self.source_to_target:
            return self.source_to_target[source]
        candidates = {}
        for n in range(self.n, 0, -1):
            for ng in self._char_ngrams(source, n):
                for src, tgt in self.ngram_index.get(ng, []):
                    candidates[src] = tgt
        if not candidates:
            candidates = self.source_to_target
        best = max(candidates, key=lambda s: self._ngram_sim(source, s))
        best_tgt = candidates[best]
        # Apply number substitution
        src_nums = NUM_PAT.findall(source)
        ref_nums = NUM_PAT.findall(best)
        if src_nums and ref_nums:
            return substitute_numbers_in_target(best_tgt, ref_nums, src_nums)
        return best_tgt

    def predict_batch(self, sources):
        return [self.predict(s) for s in sources]


# ============================================================
# MODEL 2: EditDistanceTransducer
# ============================================================

class EditDistanceTransducer:
    """
    Edit-distance nearest-neighbor transducer with number substitution.
    Finds the closest training source by character edit distance,
    then substitutes numeric tokens from the query into the target.
    """
    def __init__(self):
        self.source_to_target = {}

    def _edit_distance(self, s1, s2):
        m, n = len(s1), len(s2)
        if m > 60 or n > 60:
            return abs(m - n) + sum(c1 != c2 for c1, c2 in zip(s1[:20], s2[:20]))
        dp = list(range(n + 1))
        for i in range(1, m + 1):
            prev = dp[0]
            dp[0] = i
            for j in range(1, n + 1):
                temp = dp[j]
                dp[j] = prev if s1[i-1] == s2[j-1] else 1 + min(prev, dp[j], dp[j-1])
                prev = temp
        return dp[n]

    def fit(self, train_pairs):
        self.source_to_target = {src: tgt for src, tgt in train_pairs}

    def predict(self, source):
        if source in self.source_to_target:
            return self.source_to_target[source]
        best_src = min(self.source_to_target, key=lambda s: self._edit_distance(source, s))
        best_tgt = self.source_to_target[best_src]
        src_nums = NUM_PAT.findall(source)
        ref_nums = NUM_PAT.findall(best_src)
        if src_nums and ref_nums:
            return substitute_numbers_in_target(best_tgt, ref_nums, src_nums)
        return best_tgt

    def predict_batch(self, sources):
        return [self.predict(s) for s in sources]


# ============================================================
# MODEL 3: StructuralTransducer (rule-learning)
# ============================================================

class StructuralTransducer:
    """
    Structural transducer that learns the segmentation template from
    training data by abstracting over numeric tokens.
    
    It replaces all numbers in source/target with a placeholder,
    learns the template mapping, then instantiates with query numbers.
    This is analogous to paradigm-based morphological analysis.
    """
    def __init__(self):
        self.templates = []  # list of (src_template, tgt_template)
        self.source_to_target = {}

    def _abstract(self, s):
        """Replace all digit sequences with NUM placeholder."""
        return NUM_PAT.sub('NUM', s)

    def fit(self, train_pairs):
        self.source_to_target = {src: tgt for src, tgt in train_pairs}
        # Build template table
        template_map = {}
        for src, tgt in train_pairs:
            src_tmpl = self._abstract(src)
            tgt_tmpl = self._abstract(tgt)
            template_map[src_tmpl] = tgt_tmpl
        self.templates = list(template_map.items())

    def predict(self, source):
        if source in self.source_to_target:
            return self.source_to_target[source]
        src_tmpl = self._abstract(source)
        src_nums = NUM_PAT.findall(source)
        # Find matching template
        for tmpl_src, tmpl_tgt in self.templates:
            if tmpl_src == src_tmpl:
                # Instantiate template with query numbers
                result = tmpl_tgt
                for num in src_nums:
                    result = result.replace('NUM', num, 1)
                return result
        # Fallback: find closest template by edit distance
        if self.templates:
            best_tmpl_src, best_tmpl_tgt = min(
                self.templates,
                key=lambda t: sum(c1 != c2 for c1, c2 in zip(t[0], src_tmpl))
            )
            result = best_tmpl_tgt
            for num in src_nums:
                result = result.replace('NUM', num, 1)
            return result
        return ' '.join(list(source))

    def predict_batch(self, sources):
        return [self.predict(s) for s in sources]


# ============================================================
# chrF++ IMPLEMENTATION
# ============================================================

def get_char_ngrams(text, n):
    counts = defaultdict(int)
    chars = text.replace(' ', '')
    for i in range(len(chars) - n + 1):
        counts[chars[i:i+n]] += 1
    return counts

def get_word_ngrams(text, n):
    counts = defaultdict(int)
    words = text.split()
    for i in range(len(words) - n + 1):
        counts[tuple(words[i:i+n])] += 1
    return counts

def chrf_sentence(hypothesis, reference, char_order=6, word_order=2, beta=2):
    """
    chrF++ (Popovic, 2017): character n-gram F-score + word n-grams.
    beta=2 weights recall twice as much as precision.
    Returns score in [0, 100].
    """
    total_prec = 0.0
    total_rec = 0.0
    total_count = 0
    for n in range(1, char_order + 1):
        hyp_c = get_char_ngrams(hypothesis, n)
        ref_c = get_char_ngrams(reference, n)
        ht = sum(hyp_c.values())
        rt = sum(ref_c.values())
        if ht == 0 and rt == 0:
            continue
        match = sum(min(hyp_c[ng], ref_c[ng]) for ng in hyp_c)
        total_prec += match / ht if ht > 0 else 0.0
        total_rec  += match / rt if rt > 0 else 0.0
        total_count += 1
    for n in range(1, word_order + 1):
        hyp_w = get_word_ngrams(hypothesis, n)
        ref_w = get_word_ngrams(reference, n)
        ht = sum(hyp_w.values())
        rt = sum(ref_w.values())
        if ht == 0 and rt == 0:
            continue
        match = sum(min(hyp_w[ng], ref_w[ng]) for ng in hyp_w)
        total_prec += match / ht if ht > 0 else 0.0
        total_rec  += match / rt if rt > 0 else 0.0
        total_count += 1
    if total_count == 0:
        return 0.0
    ap = total_prec / total_count
    ar = total_rec  / total_count
    if ap + ar == 0:
        return 0.0
    b2 = beta ** 2
    return 100 * (1 + b2) * ap * ar / (b2 * ap + ar)

def chrf_corpus(hypotheses, references):
    scores = [chrf_sentence(h, r) for h, r in zip(hypotheses, references)]
    return float(np.mean(scores)), scores


# ============================================================
# TRAINING AND EVALUATION
# ============================================================

def run_benchmark(code, model_class, model_kwargs=None):
    if model_kwargs is None:
        model_kwargs = {}
    train, val, test = load_all_splits(code)
    model = model_class(**model_kwargs)
    model.fit(train)

    val_preds = model.predict_batch([s for s, t in val])
    val_refs  = [t for s, t in val]
    val_chrf, val_scores = chrf_corpus(val_preds, val_refs)

    test_preds = model.predict_batch([s for s, t in test])
    test_refs  = [t for s, t in test]
    test_chrf, test_scores = chrf_corpus(test_preds, test_refs)

    exact_match = sum(p == r for p, r in zip(test_preds, test_refs))

    return {
        'code': code,
        'train_size': len(train),
        'val_size': len(val),
        'test_size': len(test),
        'val_chrf': val_chrf,
        'val_scores': val_scores,
        'test_chrf': test_chrf,
        'test_scores': test_scores,
        'test_preds': test_preds,
        'test_refs': test_refs,
        'test_sources': [s for s, t in test],
        'exact_match': exact_match,
        'exact_match_pct': exact_match / len(test) * 100,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print('Morphological Segmentation Benchmark Analysis')
    print('=' * 65)

    model_families = {
        'CharNgram':    (CharNgramTransducer,    {'n': 6}),
        'EditDist':     (EditDistanceTransducer,  {}),
        'Structural':   (StructuralTransducer,    {}),
    }

    all_results = {}
    for mname, (mcls, mkwargs) in model_families.items():
        all_results[mname] = {}
        print(f'\n--- Model: {mname} ---')
        for code in SELECTED:
            r = run_benchmark(code, mcls, mkwargs)
            all_results[mname][code] = r
            print(f'  {code} ({REGISTRY[code]["script_family"]:12s}): '
                  f'val={r["val_chrf"]:6.2f}  test={r["test_chrf"]:6.2f}  '
                  f'exact={r["exact_match_pct"]:5.1f}%')
            # Show predictions
            for i, (src, tgt, pred) in enumerate(zip(
                    r['test_sources'], r['test_refs'], r['test_preds'])):
                match_sym = 'OK' if pred == tgt else 'XX'
                print(f'    [{match_sym}] src={src[:30]}  pred={pred[:40]}  ref={tgt[:40]}')

    # Primary model: Structural (best)
    primary_model = 'Structural'
    primary = all_results[primary_model]

    # Save results
    os.makedirs('outputs', exist_ok=True)
    save_data = {}
    for mname, mresults in all_results.items():
        save_data[mname] = {}
        for code, r in mresults.items():
            save_data[mname][code] = {
                'script_family': REGISTRY[code]['script_family'],
                'dev_bleu': REGISTRY[code]['dev_bleu'],
                'train_size': r['train_size'],
                'val_chrf': r['val_chrf'],
                'test_chrf': r['test_chrf'],
                'test_scores': r['test_scores'],
                'exact_match_pct': r['exact_match_pct'],
            }
    with open('outputs/all_results.json', 'w') as f:
        json.dump(save_data, f, indent=2)
    print('\nSaved outputs/all_results.json')

    # ============================================================
    # FIGURES
    # ============================================================
    os.makedirs('report/images', exist_ok=True)
    palette = {
        'Latin': '#4C72B0', 'Arabic': '#DD8452', 'Greek': '#55A868',
        'Cyrillic': '#C44E52', 'Devanagari': '#8172B2'
    }
    codes = SELECTED
    script_families = [REGISTRY[c]['script_family'] for c in codes]
    colors = [palette[sf] for sf in script_families]

    # ---- Figure 1: Primary test chrF++ per benchmark ----
    fig, ax = plt.subplots(figsize=(9, 5))
    test_chrfs = [primary[c]['test_chrf'] for c in codes]
    bars = ax.bar(codes, test_chrfs, color=colors, edgecolor='black', linewidth=0.8, width=0.6)
    for bar, score in zip(bars, test_chrfs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
                f'{score:.1f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    legend_patches = [mpatches.Patch(color=palette[sf], label=sf) for sf in palette]
    ax.legend(handles=legend_patches, title='Script Family', loc='lower right', fontsize=9)
    ax.set_xlabel('Benchmark Code', fontsize=12)
    ax.set_ylabel('chrF++ Score (%)', fontsize=12)
    ax.set_title('Test chrF++ Scores by Benchmark\n(Structural Transducer Model)', fontsize=13)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig1_test_chrf_scores.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig1_test_chrf_scores.png')

    # ---- Figure 2: Model comparison grouped bar chart ----
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(codes))
    n_models = len(model_families)
    width = 0.25
    model_colors = ['#5B9BD5', '#ED7D31', '#70AD47']
    model_names = list(model_families.keys())
    for mi, mname in enumerate(model_names):
        scores = [all_results[mname][c]['test_chrf'] for c in codes]
        offset = (mi - n_models/2 + 0.5) * width
        bars = ax.bar(x + offset, scores, width, label=mname,
                      color=model_colors[mi], edgecolor='black', linewidth=0.6)
        for bar, score in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{score:.0f}', ha='center', va='bottom', fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{c}\n({REGISTRY[c]["script_family"]})' for c in codes], fontsize=10)
    ax.set_xlabel('Benchmark', fontsize=12)
    ax.set_ylabel('Test chrF++ (%)', fontsize=12)
    ax.set_title('Model Family Comparison: Test chrF++ per Benchmark', fontsize=13)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=9, loc='lower right')
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig2_model_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig2_model_comparison.png')

    # ---- Figure 3: chrF++ vs dev_bleu scatter ----
    fig, ax = plt.subplots(figsize=(7, 5))
    dev_bleus = [REGISTRY[c]['dev_bleu'] for c in codes]
    for code, db, tc, sf in zip(codes, dev_bleus, test_chrfs, script_families):
        ax.scatter(db, tc, color=palette[sf], s=140, edgecolors='black', linewidth=0.8, zorder=5)
        ax.annotate(code, (db, tc), textcoords='offset points', xytext=(7, 4), fontsize=11)
    if len(dev_bleus) > 1:
        z = np.polyfit(dev_bleus, test_chrfs, 1)
        p = np.poly1d(z)
        xl = np.linspace(min(dev_bleus)-0.03, max(dev_bleus)+0.03, 100)
        ax.plot(xl, p(xl), 'k--', alpha=0.4, linewidth=1.5, label='Linear trend')
    legend_patches = [mpatches.Patch(color=palette[sf], label=sf) for sf in palette]
    ax.legend(handles=legend_patches, title='Script Family', fontsize=9)
    ax.set_xlabel('Dev BLEU (registry)', fontsize=12)
    ax.set_ylabel('Test chrF++ (%)', fontsize=12)
    ax.set_title('Test chrF++ vs. Dev BLEU\nCorrelation across Selected Benchmarks', fontsize=13)
    ax.grid(alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig3_chrf_vs_devbleu.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig3_chrf_vs_devbleu.png')

    # ---- Figure 4: Per-sample chrF++ distribution ----
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, code in enumerate(codes):
        subset = np.array(primary[code]['test_scores'])
        jitter = np.random.uniform(-0.12, 0.12, len(subset))
        ax.scatter([i + j for j in jitter], subset,
                   color=palette[REGISTRY[code]['script_family']],
                   s=90, edgecolors='black', linewidth=0.6, alpha=0.9, zorder=5)
        ax.hlines(np.mean(subset), i-0.25, i+0.25, colors='black', linewidth=2.5, zorder=6)
    ax.set_xticks(range(len(codes)))
    ax.set_xticklabels(codes, fontsize=11)
    ax.set_xlabel('Benchmark Code', fontsize=12)
    ax.set_ylabel('chrF++ Score (%)', fontsize=12)
    ax.set_title('Per-Sample Test chrF++ Distribution\n(horizontal bar = mean)', fontsize=13)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    legend_patches = [mpatches.Patch(color=palette[sf], label=sf) for sf in palette]
    ax.legend(handles=legend_patches, title='Script Family', loc='lower right', fontsize=9)
    plt.tight_layout()
    plt.savefig('report/images/fig4_per_sample_chrf.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig4_per_sample_chrf.png')

    # ---- Figure 5: Val vs Test chrF++ ----
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(codes))
    width = 0.35
    val_scores = [primary[c]['val_chrf'] for c in codes]
    b1 = ax.bar(x - width/2, val_scores, width, label='Val chrF++',
                color='#5B9BD5', edgecolor='black', linewidth=0.7)
    b2 = ax.bar(x + width/2, test_chrfs, width, label='Test chrF++',
                color='#ED7D31', edgecolor='black', linewidth=0.7)
    for bar, score in zip(b1, val_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{score:.1f}', ha='center', va='bottom', fontsize=9)
    for bar, score in zip(b2, test_chrfs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{score:.1f}', ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(codes, fontsize=11)
    ax.set_xlabel('Benchmark Code', fontsize=12)
    ax.set_ylabel('chrF++ Score (%)', fontsize=12)
    ax.set_title('Validation vs. Test chrF++ per Benchmark', fontsize=13)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig5_val_vs_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig5_val_vs_test.png')

    # ---- Figure 6: Registry overview ----
    with open('data/registry.json') as f:
        registry_full = json.load(f)['benchmarks']
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    sf_bleus = defaultdict(list)
    for b in registry_full:
        sf_bleus[b['script_family']].append(b['dev_bleu'])
    sf_order = ['Latin', 'Cyrillic', 'Arabic', 'Devanagari', 'Greek']
    bp_data = [sf_bleus[sf] for sf in sf_order]
    bp = ax.boxplot(bp_data, patch_artist=True, notch=False)
    for patch, sf in zip(bp['boxes'], sf_order):
        patch.set_facecolor(palette[sf])
        patch.set_alpha(0.8)
    ax.set_xticklabels(sf_order, rotation=15, fontsize=9)
    ax.set_ylabel('Dev BLEU', fontsize=11)
    ax.set_title('Dev BLEU Distribution\nby Script Family (all 18 benchmarks)', fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax = axes[1]
    for b in registry_full:
        sf = b['script_family']
        is_selected = b['code'] in SELECTED
        ax.scatter(b['dev_bleu'], b['test_size'],
                   color=palette[sf], s=80 if not is_selected else 160,
                   edgecolors='black' if is_selected else 'gray',
                   linewidth=1.5 if is_selected else 0.5,
                   zorder=5 if is_selected else 3,
                   marker='*' if is_selected else 'o')
        if is_selected:
            ax.annotate(b['code'], (b['dev_bleu'], b['test_size']),
                        textcoords='offset points', xytext=(5, 3), fontsize=9, fontweight='bold')
    legend_patches = [mpatches.Patch(color=palette[sf], label=sf) for sf in sf_order]
    legend_patches.append(plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='gray',
                                      markersize=10, label='Selected', markeredgecolor='black'))
    ax.legend(handles=legend_patches, fontsize=8, loc='upper left')
    ax.set_xlabel('Dev BLEU', fontsize=11)
    ax.set_ylabel('Test Size', fontsize=11)
    ax.set_title('Test Size vs. Dev BLEU\n(stars = selected benchmarks)', fontsize=11)
    ax.grid(alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig6_registry_overview.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig6_registry_overview.png')

    # ---- Figure 7: Exact match vs chrF++ ----
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(codes))
    width = 0.35
    exact_pcts = [primary[c]['exact_match_pct'] for c in codes]
    b1 = ax.bar(x - width/2, exact_pcts, width, label='Exact Match (%)',
                color='#70AD47', edgecolor='black', linewidth=0.7)
    b2 = ax.bar(x + width/2, test_chrfs, width, label='chrF++ (%)',
                color='#ED7D31', edgecolor='black', linewidth=0.7)
    for bar, score in zip(b1, exact_pcts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{score:.0f}', ha='center', va='bottom', fontsize=9)
    for bar, score in zip(b2, test_chrfs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{score:.1f}', ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(codes, fontsize=11)
    ax.set_xlabel('Benchmark Code', fontsize=12)
    ax.set_ylabel('Score (%)', fontsize=12)
    ax.set_title('Exact Match vs. chrF++ on Test Set\n(Structural Transducer)', fontsize=13)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig7_exact_vs_chrf.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig7_exact_vs_chrf.png')

    # ============================================================
    # PRINT FINAL SUMMARY
    # ============================================================
    print('\n' + '='*70)
    print('FINAL RESULTS SUMMARY (Structural Transducer)')
    print('='*70)
    print(f'{"Code":<6} {"Script":<12} {"DevBLEU":<10} {"ValchrF++":<12} {"TestchrF++":<12} {"ExactMatch":<12}')
    print('-'*70)
    for code in SELECTED:
        r = primary[code]
        print(f'{code:<6} {REGISTRY[code]["script_family"]:<12} '
              f'{REGISTRY[code]["dev_bleu"]:<10.4f} '
              f'{r["val_chrf"]:<12.2f} {r["test_chrf"]:<12.2f} '
              f'{r["exact_match_pct"]:<12.1f}')
    print('='*70)

    return all_results


if __name__ == '__main__':
    all_results = main()
