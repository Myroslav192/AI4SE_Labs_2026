"""Evaluate existing model-generated SQL. No SQL generation or answer correction.

Run from any directory: python evaluate_all.py
Uses only Python's standard library. All paths are relative to this file.
"""

import csv
import hashlib
import importlib.util
import json
import math
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
csv.field_size_limit(1_000_000_000)


def load_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def multiset(rows):
    return Counter(map(tuple, rows))


def authorize(action, arg1, arg2, db, trigger):
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_RECURSIVE):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and (arg2 or '').lower() != 'load_extension':
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def main():
    spec = importlib.util.spec_from_file_location('teacher', ROOT / 'evaluate_teacher_patched.py')
    teacher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(teacher)
    questions = json.loads((ROOT / 'inputs/questions.json').read_text(encoding='utf-8'))
    labels = load_csv(ROOT / 'inputs/restaurants_dataset.csv')
    assert len(labels) == len(questions) == 155
    assert [q['question_id'] for q in questions] == list(range(1, 156))
    assert [q['question'] for q in questions] == [q['question'] for q in labels]
    expected = [json.loads(row['result']) for row in labels]
    all_summaries, all_records, validations = {}, {}, {}
    for tag in ['icio', 'rtf', 'co_star']:
        path = ROOT / 'predictions' / f'predictions_{tag}.csv'
        records = load_csv(path)
        assert len(records) == len(labels), (tag, 'prediction count')
        assert [int(r['question_id']) for r in records] == list(range(1,156)), (tag, 'IDs')
        assert [r['question'] for r in records] == [r['question'] for r in labels], (tag, 'question text')
        assert all(r['prompt_id'] == f'{tag}_v1' and r['model'] == 'GPT-6.1 Sol' and r['reasoning'] == 'Medium' for r in records)
        timing = json.loads((ROOT / 'timings' / f'timing_{tag}.json').read_text(encoding='utf-8'))
        start = timing.get('start', timing.get('start_utc'))
        end = timing.get('end', timing.get('end_utc'))
        delta = (datetime.fromisoformat(end.replace('Z','+00:00')) - datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds()
        assert abs(delta - timing['elapsed_seconds']) < .00001
        assert timing['model'] == 'GPT-6.1 Sol' and timing['reasoning'] == 'Medium' and timing['prompt_id'] == f'{tag}_v1'
        compatible = ROOT / 'predictions' / f'{tag}_two_columns.csv'
        with compatible.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['question','predicted_sql'])
            writer.writeheader()
            writer.writerows({key:r[key] for key in writer.fieldnames} for r in records)
        # Database is immutable during execution. Each query runs on a fresh copy
        # of the teacher-built database; no data or key remapping is performed.
        base = teacher.load_database()
        base.commit()
        evaluations = []
        for record, wanted in zip(records, expected):
            db = sqlite3.connect(':memory:')
            base.backup(db)
            db.execute('PRAGMA query_only = ON')
            db.set_authorizer(authorize)
            deadline = time.monotonic() + 5.0
            db.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
            got, error = None, None
            try:
                got = db.execute(record['predicted_sql']).fetchall()
            except sqlite3.Error as exc:
                error = str(exc)
            finally:
                db.close()
            correct = error is None and multiset(got) == multiset(wanted)
            expected_empty = len(wanted) == 0
            overlap = 0 if got is None else sum((multiset(got) & multiset(wanted)).values())
            count = 0 if got is None else len(got)
            f1 = 0.0 if error else (1.0 if count + len(wanted) == 0 else 2*overlap/(count+len(wanted)))
            evaluations.append({'question_id':int(record['question_id']), 'question':record['question'],
                                'predicted_sql':record['predicted_sql'], 'correct':correct,
                                'expected_empty':expected_empty, 'expected_row_count':len(wanted),
                                'predicted_row_count':None if got is None else count,
                                'error':error, 'row_f1':f1, 'predicted_rows':got})
        base.close()
        correct = sum(r['correct'] for r in evaluations)
        errors = sum(r['error'] is not None for r in evaluations)
        summary = {'prompt':tag, 'total':len(evaluations), 'correct':correct, 'accuracy':correct/len(evaluations),
                   'execution_errors':errors, 'elapsed_agent_seconds':timing['elapsed_seconds'],
                   'empty_correct':sum(r['correct'] and r['expected_empty'] for r in evaluations),
                   'empty_total':sum(r['expected_empty'] for r in evaluations),
                   'nonempty_correct':sum(r['correct'] and not r['expected_empty'] for r in evaluations),
                   'nonempty_total':sum(not r['expected_empty'] for r in evaluations)}
        (ROOT / 'results' / f'evaluation_{tag}.json').write_text(json.dumps(evaluations, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Run the minimally patched teacher CLI unchanged on valid predictions.
        if not errors:
            process = subprocess.run([sys.executable, str(ROOT/'evaluate_teacher_patched.py'), str(compatible)], capture_output=True, text=True)
            assert process.returncode == 0, process.stderr
            assert f'Correct: {correct}/{len(evaluations)}' in process.stdout
            (ROOT / 'results' / f'teacher_validation_{tag}.txt').write_text(process.stdout, encoding='utf-8')
        else:
            (ROOT / 'results' / f'teacher_validation_{tag}.txt').write_text('Teacher CLI would halt on an SQL error. Per-question adapter results used; error is counted as incorrect.\n', encoding='utf-8')
        all_summaries[tag], all_records[tag] = summary, evaluations
        validations[tag] = {'questions_verified':len(records), 'question_text_order_and_ids_match':True,
                            'metadata_verified':True, 'timestamps_verified':True,
                            'teacher_cli_agreement':not bool(errors)}
    # Diagnose reference IDs without modifying any reference or prediction.
    db = teacher.load_database()
    id_names = set(db.execute('SELECT ID,NAME FROM RESTAURANT'))
    names = set(row[0] for row in db.execute('SELECT NAME FROM RESTAURANT'))
    diagnostics = []
    for i, rows in enumerate(expected,1):
        if rows and all(len(r)==2 and isinstance(r[0],int) and isinstance(r[1],str) for r in rows):
            absent = sum(tuple(r) not in id_names for r in rows)
            known_names = sum(r[1] in names for r in rows)
            diagnostics.append({'question_id':i,'reference_rows':len(rows),'id_name_pairs_absent_from_restaurant':absent,'names_present_in_restaurant':known_names})
    db.close()
    hashes = {tag:{'sql_text_sha256':hashlib.sha256('\n'.join(r['predicted_sql'] for r in rows).encode()).hexdigest()} for tag,rows in all_records.items()}
    agreement = {}
    for a,b in [('icio','rtf'),('icio','co_star'),('rtf','co_star')]:
        agreement[f'{a}_vs_{b}'] = {'identical_sql_text':sum(x['predicted_sql']==y['predicted_sql'] for x,y in zip(all_records[a],all_records[b])),
                                   'same_executed_result':sum(x['error'] is None and y['error'] is None and multiset(x['predicted_rows'])==multiset(y['predicted_rows']) for x,y in zip(all_records[a],all_records[b]))}
    result = {'summaries':all_summaries,'validation':validations,'prediction_hashes':hashes,'pairwise_agreement':agreement,
              'reference_diagnostics':diagnostics,
              'reference_diagnostic_summary':{'nonempty_restaurant_pair_questions':len(diagnostics),
                 'questions_with_any_absent_reference_pair':sum(r['id_name_pairs_absent_from_restaurant']>0 for r in diagnostics),
                 'reference_pairs_total':sum(r['reference_rows'] for r in diagnostics),
                 'reference_pairs_absent':sum(r['id_name_pairs_absent_from_restaurant'] for r in diagnostics)}}
    (ROOT / 'results/summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'summaries':all_summaries,'agreement':agreement,'reference_diagnostics':result['reference_diagnostic_summary']},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
