#!/usr/bin/env python3
"""Verify an extracted package or safely extract/verify a ZIP. No model API calls.

Static checks need NumPy. --exercise reuses the current interpreter; cached local
retrieval additionally requires --cache-dir. No installation or weight download
is attempted. External links are reported separately from checked local targets.
"""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from urllib.parse import unquote
import zipfile

import numpy as np


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def method(tree, task):
    scope = tree
    for name in task["class"].split("."):
        scope = next(n for n in scope.body if isinstance(n, ast.ClassDef) and n.name == name)
    return next(n for n in scope.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == task["method"])


def forbidden(path):
    parts = PurePosixPath(path).parts
    return any(p in {".git", ".hg", ".svn", ".venv", "venv", "env", ".cache", "__pycache__", "node_modules"} for p in parts) or any(p.startswith(".env") and p != ".env.example" for p in parts) or PurePosixPath(path).suffix.lower() in {".zip", ".pyc", ".pyo", ".safetensors", ".pt", ".pth", ".onnx", ".bin", ".pem", ".key", ".tmp"}


def check(root, known_secrets=()):
    root = root.resolve()
    manifest = {}
    for line in (root / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert re.fullmatch(r"[a-f0-9]{64}", digest)
        assert name not in manifest and name != "SHA256SUMS"
        path = root / name
        assert path.resolve().is_relative_to(root) and path.is_file() and not path.is_symlink()
        assert not forbidden(name), f"Excluded payload member: {name}"
        assert sha(path.read_bytes()) == digest, f"Manifest mismatch: {name}"
        manifest[name] = digest
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == set(manifest) | {"SHA256SUMS"}, "Manifest does not cover the actual payload exactly"
    provenance = json.loads((root / "solution/artifacts/package_source_provenance.json").read_bytes())
    for path, digest in {**provenance["assignments"], **provenance["solved_source"]}.items():
        assert sha((root / path).read_bytes()) == digest
    tasks = json.loads((root / "Assignments/missing_code.json").read_bytes())
    assert len(tasks) == 10 and len(provenance["assignments"]) == 7
    artifacts = root / "solution/artifacts"
    chunks_raw = (artifacts / "chunks.jsonl").read_bytes()
    chunks = [json.loads(line) for line in chunks_raw.splitlines()]
    source_manifest = json.loads((artifacts / "chunks.manifest.json").read_bytes())
    metadata = json.loads((artifacts / "embeddings.metadata.json").read_bytes())
    assert len(chunks) == 55 and len({c['id'] for c in chunks}) == 55
    assert [(c['path'],c['start_line']) for c in chunks] == sorted((c['path'],c['start_line']) for c in chunks)
    assert sha(chunks_raw) == metadata['source']['chunks_sha256'] == source_manifest['chunks_sha256']
    assert sha((artifacts / metadata['source']['manifest_path']).read_bytes()) == metadata['source']['manifest_sha256']
    assert sha((artifacts / 'embeddings.npz').read_bytes()) == metadata['storage']['npz_sha256']
    with np.load(artifacts / 'embeddings.npz', allow_pickle=False) as store:
        assert set(store.files) == {'embeddings','chunk_ids'}
        vectors, ids = store['embeddings'], store['chunk_ids']
        assert vectors.shape == (55,384) and vectors.dtype == np.float32 and ids.dtype.kind == 'U'
        assert ids.tolist() == [c['id'] for c in chunks]
        assert np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5,rtol=0)
    original = {}
    tests_unchanged = 0
    for file in source_manifest['files']:
        own = [c for c in chunks if c['path'] == file['path']]
        cursor = 1
        for chunk in own:
            assert chunk['start_line'] == cursor
            assert len(chunk['text'].splitlines(keepends=True)) == chunk['end_line']-chunk['start_line']+1
            assert chunk['source_sha256'] == file['sha256']
            cursor = chunk['end_line']+1
        raw = ''.join(c['text'] for c in own).encode()
        assert sha(raw) == file['sha256'] and cursor == file['lines']+1
        original[file['path']] = raw
        if file['path'].startswith('playground/tests/'):
            assert (root / 'solution/AI4SE_Playground' / file['path']).read_bytes() == raw
            tests_unchanged += 1
    assert len(original) == 28 and tests_unchanged == 14
    for index,(row,chunk) in enumerate(zip(metadata['rows'],chunks)):
        assert row['row'] == index and row['chunk_id'] == chunk['id']
        assert sha((row['prefix']+chunk['text']).encode()) == row['embedding_text_sha256']
    pinned = provenance['original_source_commit']
    assert pinned == source_manifest['repository_commit'] == metadata['source']['repository_commit']
    evaluation = json.loads((artifacts / 'retrieval_evaluation.json').read_bytes())
    run = artifacts / 'task5_runs/run-e1ba175ad737'
    summary = json.loads((run / 'summary.json').read_bytes())
    assert summary['status'] == 'complete' and summary['applied'] == 10 and summary['api_calls'] == 14
    hits, response_count, accepted = 0, 0, 0
    rejected = []
    for number,(task,diagnostic) in enumerate(zip(tasks,evaluation['tasks']),start=1):
        old_method = method(ast.parse(original[task['file']]),task)
        start = min([old_method.lineno]+[d.lineno for d in old_method.decorator_list])
        hit = any(r['path']==task['file'] and r['start_line']<=start and r['end_line']>=old_method.end_lineno for r in diagnostic['results'])
        assert hit == diagnostic['target_method_hit'];hits += hit
        result = json.loads((run / f'task-{number:02}/result.json').read_bytes())
        assert result['status'] == 'applied' and result['query'] == diagnostic['query']
        for attempt in result['attempts']:
            response_count += 1
            directory = run / f'task-{number:02}/attempt-{attempt["generation_attempt"]:02}'
            payload = json.loads((directory / 'request.json').read_bytes())
            context = json.loads(payload['input'])['repository_context']
            assert len(context) == 5
            assert [c['chunk_id'] for c in context] == [c['chunk_id'] for c in diagnostic['results']]
            for supplied,expected in zip(context,diagnostic['results']):
                assert supplied['text'] == expected['text']
            assert attempt['response_id'] and attempt['returned_model'] == 'gpt-5-mini-2025-08-07'
            if attempt['status'] != 'applied':
                rejected.append(attempt['validation']);continue
            accepted += 1
            returned = ast.parse((directory / 'returned_code.py').read_bytes()).body[0]
            current = method(ast.parse((root/'solution/AI4SE_Playground'/task['file']).read_bytes()),task)
            assert [ast.dump(n) for n in current.body] == [ast.dump(n) for n in returned.body]
            assert not any(isinstance(n,ast.Pass) for n in ast.walk(current))
            for field in ['args','returns','decorator_list']:
                def canonical(value):
                    if isinstance(value,list):return [ast.dump(n) for n in value]
                    return ast.dump(value) if isinstance(value,ast.AST) else value
                assert canonical(getattr(current,field)) == canonical(getattr(old_method,field))
            assert ast.get_docstring(current,clean=False) == ast.get_docstring(old_method,clean=False)
    assert hits == 10 and response_count == 14 and accepted == 10 and len(rejected) == 4
    final = json.loads((artifacts / 'final_tests.status.json').read_bytes())
    assert final['exit_code'] == 0 and final['tests'] == 481 and final['failures'] == final['errors'] == 0
    assert final['baseline']['tests'] == 481 and final['baseline']['failures'] == 35 and final['baseline']['errors'] == 17
    assert (artifacts/'final_tests.log').read_bytes() == (run/'repository_tests.log').read_bytes()
    local_links = 0;external = set()
    for path in root.rglob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
            target = target.strip('<>')
            if target.startswith(('https://','http://')):
                external.add(target);continue
            if target.startswith('#'):continue
            target = unquote(target.split('#',1)[0])
            assert (path.parent/target).exists(), f'Broken local documentation link in {path.relative_to(root)}'
            local_links += 1
    signatures = [re.compile(rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    for name in manifest:
        data = (root/name).read_bytes()
        assert not any(secret and secret.encode() in data for secret in known_secrets), f'Configured credential in {name}'
        assert not any(pattern.search(data) for pattern in signatures), f'Credential-like signature in {name}'
    return {'result':'PASS','payload_files_including_manifest':len(actual),'sha256_manifest_entries':len(manifest),
            'assignments_verified':7,'original_test_files_verified':tests_unchanged,'solved_source_files_verified':len(provenance['solved_source']),
            'frozen_source_files_reconstructed':len(original),'chunks':55,'embedding_shape':[55,384],'embedding_load_allow_pickle':False,
            'target_hits_at_5':hits,'actual_generation_responses':response_count,'accepted_generated_methods':accepted,'preserved_rejections':rejected,
            'local_documentation_links_checked':local_links,'external_reference_urls_not_fetched':sorted(external),
            'excluded_files_absent':True,'configured_secret_check_performed':bool(known_secrets),'credential_signature_scan':'PASS'}


def exercise(root, cache_dir, logs):
    logs.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k not in {'OPENAI_API_KEY','OPENAI_BASE_URL','OPENAI_MODEL'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    def run(command,cwd,label):
        result=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,timeout=120)
        (logs/(label+'.log')).write_text(result.stdout+result.stderr)
        assert result.returncode==0, f'{label} failed; inspect external verification log'
        return result
    tests=run([sys.executable,'-m','unittest','discover','-s','tests','-v'],root/'solution/AI4SE_Playground/playground','repository_tests')
    assert re.search(r'^Ran 481 tests',tests.stderr,re.M) and tests.stderr.rstrip().endswith('OK')
    checks=[]
    for script in ['chunk_repository.py','verify_chunking.py','embed_repository.py','retrieve_chunks.py','evaluate_retrieval.py','solve_tasks.py']:
        command=[sys.executable,'solution/rag/'+script,'--help']
        run(command,root,'help_'+script[:-3]);checks.append({'entry_point':'solution/rag/'+script,'exit_code':0})
    run([sys.executable,'-m','unittest','discover','-s','solution/rag/tests','-p','test_solving.py','-v'],root,'pipeline_offline_tests')
    retrieval=None
    if cache_dir:
        result=run([sys.executable,'solution/rag/retrieve_chunks.py','Return the number of line items in an order.',
                    '--chunks','solution/artifacts/chunks.jsonl','--embeddings','solution/artifacts/embeddings.npz',
                    '--metadata','solution/artifacts/embeddings.metadata.json','--cache-dir',str(cache_dir),'-n','5'],root,'local_retrieval')
        retrieved=json.loads(result.stdout)
        reference=json.loads((root/'solution/artifacts/task4_cli_example.json').read_bytes())
        assert [r['chunk_id'] for r in retrieved['results']] == [r['chunk_id'] for r in reference['results']]
        np.testing.assert_allclose([r['score'] for r in retrieved['results']],[r['score'] for r in reference['results']],atol=1e-6,rtol=1e-5)
        retrieval={'returned_chunks':5,'matches_saved_cli_ids':True,'scores_within_atol_1e_minus_6_rtol_1e_minus_5':True}
    return {'repository_tests':{'tests':481,'failures':0,'errors':0,'exit_code':0},'cli_help_checks':checks,
            'pipeline_offline_tests_exit_code':0,'actual_local_retrieval':retrieval,
            'interpreter_reused':sys.executable,'existing_model_cache_reused':bool(cache_dir),'fresh_install_tested':False,'generative_api_calls':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--archive',type=Path)
    parser.add_argument('--exercise',action='store_true')
    parser.add_argument('--cache-dir',type=Path)
    parser.add_argument('--secret-env',type=Path,help='Explicit external env file for exact secret scanning; never copied or printed')
    parser.add_argument('--logs-dir',type=Path)
    args=parser.parse_args()
    known=[]
    if args.secret_env:
        from dotenv import dotenv_values
        known=[value for name,value in dotenv_values(args.secret_env,interpolate=False).items() if value and re.search('key|secret|token|password',name,re.I)]
    with tempfile.TemporaryDirectory(prefix='week06-package-extract-') as temporary:
        root=args.root.resolve()
        if args.archive:
            root=Path(temporary)/'submission';root.mkdir()
            with zipfile.ZipFile(args.archive) as archive:
                assert archive.testzip() is None
                names=archive.namelist();assert len(names)==len(set(names))
                for item in archive.infolist():
                    name=PurePosixPath(item.filename)
                    assert not name.is_absolute() and '..' not in name.parts and not forbidden(item.filename)
                    assert stat.S_ISREG(item.external_attr>>16), 'ZIP member must be an ordinary file'
                archive.extractall(root)
        result=check(root,known)
        if args.exercise:
            logs=args.logs_dir.resolve() if args.logs_dir else Path(temporary)/'logs'
            result['execution']=exercise(root,args.cache_dir.resolve() if args.cache_dir else None,logs)
        print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
