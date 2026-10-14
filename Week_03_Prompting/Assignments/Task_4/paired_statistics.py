"""Task 4: paired question-level comparisons, without external dependencies.

CLI: python paired_statistics.py --scores ICIO=scores_icio.json RTF=scores_rtf.json
     CO-STAR=scores_co_star.json --output statistics.json
Inputs are outputs of metrics.py for the same complete set of questions.
"""

import argparse
import itertools
import json
import math
import random
from pathlib import Path


def exact_mcnemar(a, b):
    if len(a) != len(b) or not a:
        raise ValueError('Nonempty paired vectors of equal length are required')
    a_only = sum(bool(x) and not bool(y) for x, y in zip(a, b))
    b_only = sum(bool(y) and not bool(x) for x, y in zip(a, b))
    n = a_only + b_only
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a_only, b_only) + 1)) / 2**n)
    return {'a_only_correct': a_only, 'b_only_correct': b_only, 'p_value': p}


def holm_adjust(p_values):
    if any(not 0 <= p <= 1 for p in p_values):
        raise ValueError('Invalid p-value')
    result, previous = [0.0] * len(p_values), 0.0
    for rank, index in enumerate(sorted(range(len(p_values)), key=p_values.__getitem__)):
        previous = max(previous, min(1.0, (len(p_values) - rank) * p_values[index]))
        result[index] = previous
    return result


def mean(values):
    return sum(values) / len(values)


def balanced_difference(differences, empty_flags):
    empty = [d for d, flag in zip(differences, empty_flags) if flag]
    nonempty = [d for d, flag in zip(differences, empty_flags) if not flag]
    if not empty or not nonempty:
        raise ValueError('Both reference-result strata must exist')
    return (mean(empty) + mean(nonempty)) / 2


def paired_permutation(differences, empty_flags, repetitions=19999, seed=20261014):
    if repetitions < 1 or len(differences) != len(empty_flags):
        raise ValueError('Invalid permutation parameters')
    n_empty = sum(empty_flags)
    n_nonempty = len(empty_flags) - n_empty
    if not n_empty or not n_nonempty:
        raise ValueError('Both strata required')
    contributions = [d / (2 * (n_empty if flag else n_nonempty))
                     for d, flag in zip(differences, empty_flags) if d != 0]
    observed = abs(sum(contributions))
    if not contributions:
        return {'p_value': 1.0, 'method': 'exact paired permutation', 'permutations': 1}
    if len(contributions) <= 16:
        values = (sum(c * s for c, s in zip(contributions, signs))
                  for signs in itertools.product((-1, 1), repeat=len(contributions)))
        count = sum(abs(v) >= observed - 1e-12 for v in values)
        return {'p_value': count / 2**len(contributions), 'method': 'exact paired permutation',
                'permutations': 2**len(contributions)}
    rng = random.Random(seed)
    count = 0
    for _ in range(repetitions):
        permuted = sum(c if rng.getrandbits(1) else -c for c in contributions)
        count += abs(permuted) >= observed - 1e-12
    return {'p_value': (count + 1) / (repetitions + 1), 'method': 'Monte Carlo paired permutation',
            'permutations': repetitions, 'seed': seed}


def quantile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return sorted_values[lower] + (position - lower) * (sorted_values[upper] - sorted_values[lower])


def paired_bootstrap(differences, empty_flags, balanced=False, repetitions=10000, seed=20261014):
    if repetitions < 1 or not differences or len(differences) != len(empty_flags):
        raise ValueError('Invalid bootstrap parameters')
    rng = random.Random(seed)
    groups = [[d for d, flag in zip(differences, empty_flags) if flag == value] for value in (True, False)]
    if balanced and any(not group for group in groups):
        raise ValueError('Both strata required')
    samples = []
    for _ in range(repetitions):
        if balanced:
            samples.append(sum(mean(rng.choices(group, k=len(group))) for group in groups) / 2)
        else:
            samples.append(mean(rng.choices(differences, k=len(differences))))
    samples.sort()
    return {'lower': quantile(samples, .025), 'upper': quantile(samples, .975),
            'confidence': .95, 'method': 'paired percentile bootstrap' + (' stratified by reference emptiness' if balanced else ''),
            'repetitions': repetitions, 'seed': seed}


def validate_scores(scores):
    mapped = {}
    for score in scores:
        key = score['question_id']
        if isinstance(key, bool) or not isinstance(key, int) or key in mapped:
            raise ValueError('Question IDs must be unique integers')
        if type(score['correct']) is not bool or type(score['expected_empty']) is not bool:
            raise ValueError('correct and expected_empty must be booleans')
        if isinstance(score['row_f1'], bool) or not isinstance(score['row_f1'], (int, float)) or not 0 <= score['row_f1'] <= 1:
            raise ValueError('row_f1 must be between zero and one')
        mapped[key] = score
    if not mapped:
        raise ValueError('Empty score set')
    return mapped


def compare(named_scores, bootstrap_repetitions=10000, permutation_repetitions=19999):
    if len(named_scores) != 3:
        raise ValueError('Provide exactly three prompt score sets')
    indexed = {name: validate_scores(scores) for name, scores in named_scores.items()}
    first = next(iter(indexed.values()))
    ids = sorted(first)
    flags = [first[i]['expected_empty'] for i in ids]
    for values in indexed.values():
        if set(values) != set(ids):
            raise ValueError('All prompts must have identical question IDs; do not drop failures')
        if [values[i]['expected_empty'] for i in ids] != flags:
            raise ValueError('Reference-result strata disagree between prompts')
    comparisons = []
    for a, b in itertools.combinations(indexed, 2):
        x, y = indexed[a], indexed[b]
        correct_a, correct_b = [x[i]['correct'] for i in ids], [y[i]['correct'] for i in ids]
        accuracy_diffs = [int(u) - int(v) for u, v in zip(correct_a, correct_b)]
        f1_diffs = [x[i]['row_f1'] - y[i]['row_f1'] for i in ids]
        comparisons.append({'prompt_a': a, 'prompt_b': b, 'metric': 'accuracy',
                            'difference_a_minus_b': mean(accuracy_diffs),
                            'test': 'two-sided exact McNemar', **exact_mcnemar(correct_a, correct_b),
                            'difference_ci': paired_bootstrap(accuracy_diffs, flags, repetitions=bootstrap_repetitions)})
        comparisons.append({'prompt_a': a, 'prompt_b': b, 'metric': 'balanced_row_f1',
                            'difference_a_minus_b': balanced_difference(f1_diffs, flags),
                            'test': 'two-sided paired permutation',
                            **paired_permutation(f1_diffs, flags, repetitions=permutation_repetitions),
                            'difference_ci': paired_bootstrap(f1_diffs, flags, balanced=True, repetitions=bootstrap_repetitions)})
    adjusted = holm_adjust([r['p_value'] for r in comparisons])
    for row, p in zip(comparisons, adjusted):
        row.update(p_value_holm=p, significant_at_0_05=p < .05)
    return {'question_count': len(ids), 'alpha': .05,
            'multiplicity': 'Holm adjustment across all six tests (three pairs, two metrics)',
            'comparisons': comparisons,
            'limitations': ['Question-level tests do not measure variation between independent agent runs.',
                           'Related question templates may violate independent-question assumptions.',
                           'No significance test of timings: one observed duration per prompt.',
                           'Percentile intervals are unadjusted descriptive 95% intervals; significance uses Holm-adjusted p-values.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scores', nargs=3, required=True, metavar='NAME=FILE')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    scores = {}
    for item in args.scores:
        name, path = item.split('=', 1)
        if name in scores:
            raise ValueError('Duplicate prompt name')
        scores[name] = json.loads(Path(path).read_text(encoding='utf-8-sig'))['scores']
    args.output.write_text(json.dumps(compare(scores), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
