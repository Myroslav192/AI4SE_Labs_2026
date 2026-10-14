import csv, json
from pathlib import Path
from metrics import score_records
csv.field_size_limit(1_000_000_000)
root = Path(__file__).resolve().parent
with (root.parent/'Task_2/inputs/restaurants_dataset.csv').open(encoding='utf-8',newline='') as f:
    labels = [json.loads(r['result']) for r in csv.DictReader(f)]
for tag in ['icio','rtf','co_star']:
    rows = json.loads((root.parent/'Task_2/results'/f'evaluation_{tag}.json').read_text(encoding='utf-8'))
    assert len(rows) == len(labels)
    records = [{'question_id':r['question_id'],'expected_rows':e,'predicted_rows':r['predicted_rows'],'error':r['error']} for r,e in zip(rows,labels)]
    result = score_records(records)
    (root/f'scores_{tag}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(tag, result['summary'])
