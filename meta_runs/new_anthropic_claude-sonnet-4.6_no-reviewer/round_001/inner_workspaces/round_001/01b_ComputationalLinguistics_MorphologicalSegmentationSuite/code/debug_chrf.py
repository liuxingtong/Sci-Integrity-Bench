#!/usr/bin/env python3
"""Debug chrF++ computation."""

from collections import defaultdict
import numpy as np

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
        p = match / ht if ht > 0 else 0.0
        r = match / rt if rt > 0 else 0.0
        total_prec += p
        total_rec  += r
        total_count += 1
        print(f'  char n={n}: match={match}, ht={ht}, rt={rt}, p={p:.4f}, r={r:.4f}')

    for n in range(1, word_order + 1):
        hyp_w = get_word_ngrams(hypothesis, n)
        ref_w = get_word_ngrams(reference, n)
        ht = sum(hyp_w.values())
        rt = sum(ref_w.values())
        if ht == 0 and rt == 0:
            continue
        match = sum(min(hyp_w[ng], ref_w[ng]) for ng in hyp_w)
        p = match / ht if ht > 0 else 0.0
        r = match / rt if rt > 0 else 0.0
        total_prec += p
        total_rec  += r
        total_count += 1
        print(f'  word n={n}: match={match}, ht={ht}, rt={rt}, p={p:.4f}, r={r:.4f}')

    if total_count == 0:
        return 0.0
    ap = total_prec / total_count
    ar = total_rec  / total_count
    if ap + ar == 0:
        return 0.0
    b2 = beta ** 2
    score = 100 * (1 + b2) * ap * ar / (b2 * ap + ar)
    print(f'  avg_prec={ap:.4f}, avg_rec={ar:.4f}, chrF++={score:.4f}')
    return score

# Test with perfect match
hyp = 'w o r d 200 x y zw o r d 200 x y z'
ref = 'w o r d 200 x y zw o r d 200 x y z'
print('=== Perfect match (hyp == ref) ===')
print(f'hyp: {hyp}')
print(f'ref: {ref}')
score = chrf_sentence(hyp, ref)
print(f'chrF++ = {score:.4f}')

# Test with imperfect match
print('\n=== Imperfect match ===')
hyp2 = 'w o r d 0 x y zw o r d 0 x y z'
ref2 = 'w o r d 200 x y zw o r d 200 x y z'
print(f'hyp: {hyp2}')
print(f'ref: {ref2}')
score2 = chrf_sentence(hyp2, ref2)
print(f'chrF++ = {score2:.4f}')

# Check sacrebleu chrF++
try:
    import sacrebleu
    chrf = sacrebleu.corpus_chrf([hyp], [[ref]], char_order=6, word_order=2, beta=2)
    print(f'\nsacrebleu chrF++ (perfect): {chrf.score:.4f}')
    chrf2 = sacrebleu.corpus_chrf([hyp2], [[ref2]], char_order=6, word_order=2, beta=2)
    print(f'sacrebleu chrF++ (imperfect): {chrf2.score:.4f}')
except Exception as e:
    print(f'sacrebleu error: {e}')
