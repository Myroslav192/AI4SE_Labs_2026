"""Task 3: balanced row-multiset F1. No SQL generation or reference remapping.

CLI: python metrics.py executed_queries.json --output scores_icio.json
Input is a JSON array of {question_id, expected_rows, predicted_rows, error?}.
Set predicted_rows to null for missing predictions, SQL errors or timeouts.
Rows must be ordered arrays of scalar SQL values, not dictionaries.
"""

import argparse
import json
import math
from collections import Counter
from pathlib import Path


def row_multiset(rows):
    if not isinstance(rows, (list, tuple)):
        raise ValueError('Expected a sequence of rows')
    converted = []
    for row in rows:
        if not isinstance(row, (list, tuple)):
            raise ValueError('Each row must be a sequence')
        for value in row:
            if value is not None and (isinstance(value, bool) or not isinstance(value, (str, int, float))):
                raise ValueError('Unsupported SQL scalar value')
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError('Non-finite values are unsupported')
        converted.append(tuple(row))
    return Counter(converted)


def score_question(expected_rows, predicted_rows, error=None):
    expected = row_multiset(expected_rows)
    failed = predicted_rows is None or error is not None
    actual = Counter() if failed else row_multiset(predicted_rows)
    overlap = sum((actual & expected).values())
    expected_count, actual_count = sum(expected.values()), sum(actual.values())
    if failed:
        f1 = 0.0
    elif expected_count + actual_count == 0:
        f1 = 1.0
    else:
        f1 = 2 * overlap / (expected_count + actual_count)
    return {
        'correct': bool(not failed and actual == expected),
        'row_f1': f1,
        'expected_empty': expected_count == 0,
        'expected_row_count': expected_count,
        'predicted_row_count': None if failed else actual_count,
        'execution_failed': failed,
    }


def summarize(scores):
    if not scores:
        raise ValueError('No questions to score')
    empty = [r['row_f1'] for r in scores if r['expected_empty']]
    nonempty = [r['row_f1'] for r in scores if not r['expected_empty']]
    mean_empty = sum(empty) / len(empty) if empty else None
    mean_nonempty = sum(nonempty) / len(nonempty) if nonempty else None
    return {
        'total': len(scores),
        'accuracy': sum(r['correct'] for r in scores) / len(scores),
        'macro_row_f1': sum(r['row_f1'] for r in scores) / len(scores),
        'empty_questions': len(empty),
        'nonempty_questions': len(nonempty),
        'empty_mean_f1': mean_empty,
        'nonempty_mean_f1': mean_nonempty,
        'balanced_row_f1': None if not empty or not nonempty else (mean_empty + mean_nonempty) / 2,
        'execution_failures': sum(r['execution_failed'] for r in scores),
    }


def score_records(records):
    scores, ids = [], set()
    for record in records:
        identifier = record['question_id']
        if isinstance(identifier, bool) or not isinstance(identifier, int):
            raise ValueError('question_id must be an integer')
        if identifier in ids:
            raise ValueError(f'Duplicate question_id: {identifier}')
        ids.add(identifier)
        score = score_question(record['expected_rows'], record['predicted_rows'], record.get('error'))
        scores.append({'question_id': identifier, **score})
    return {'summary': summarize(scores), 'scores': scores}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = score_records(json.loads(args.input.read_text(encoding='utf-8-sig')))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
