"""Offline checks only: generic toy methods and SDK MockTransport fixtures.

No test provides implementations for the ten assignment methods. HTTP responses
below are explicit protocol fixtures, never evidence of a real generation run.
"""

import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from method_editing import ValidationError, apply_edit, prepare_edit
from solve_tasks import Configuration, make_request, solve_task, verify_scope


SOURCE = '''MARKER = "žltý"

class Widget:
    @staticmethod
    def combine(left: int, right: int = 2) -> int:
        """Fixture documentation."""
        pass

    def later(self):
        pass

UNCHANGED = True
'''
CODE = '''@staticmethod
def combine(left: int, right: int = 2) -> int:
    """Fixture documentation."""
    total = left + right
    return total
'''
TARGET = {"file":"sample.py", "class":"Widget", "method":"combine", "docstring":"Combine fixture values."}


class ToyRetriever:
    last_query_encoding = {"offline_unit_fixture":True}

    def __init__(self):
        self.results = [{"chunk_id":f"fixture-{i}","score":1.0-i/10,"path":"sample.py","start_line":1,"end_line":12,"text":SOURCE} for i in range(5)]

    def search(self, query, n):
        if n != 5:
            raise AssertionError("Must retrieve five chunks")
        return deepcopy(self.results)


def response_fixture(code=CODE, status="completed"):
    return {"id":"resp_offline_unit_fixture","object":"response","created_at":0,"model":"gpt-5-mini",
            "status":status,"error":None,"incomplete_details":{"reason":"max_output_tokens"} if status=="incomplete" else None,
            "output":[{"id":"msg_fixture","type":"message","role":"assistant","status":"completed",
                       "content":[{"type":"output_text","text":code,"annotations":[]}]}],
            "usage":None,"parallel_tool_calls":False,"tools":[],"tool_choice":"auto"}


class EditingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="week06-editor-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / "sample.py"
        self.path.write_text(SOURCE)

    def test_atomic_body_only_edit_preserves_headers_docs_surroundings_and_mode(self):
        self.path.chmod(0o640)
        edit = prepare_edit(self.root, TARGET, CODE)
        backup = self.root / "recovery.py"
        apply_edit(edit, backup)
        self.assertEqual(backup.read_bytes(), SOURCE.encode())
        self.assertEqual(self.path.read_text(), SOURCE.replace('        pass', '        total = left + right\n        return total', 1))
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o640)
        self.assertEqual(verify_scope(self.root, {"sample.py":SOURCE.encode()}, [TARGET]), ["sample.py"])

    def test_positions_recomputed_after_earlier_edits(self):
        apply_edit(prepare_edit(self.root, TARGET, CODE), self.root / "first_backup.py")
        later = {**TARGET,"method":"later"}
        apply_edit(prepare_edit(self.root, later, 'def later(self):\n    return "fixture"\n'), self.root / "second_backup.py")
        tree = ast.parse(self.path.read_bytes())
        self.assertEqual(tree.body[1].body[1].body[0].value.value, "fixture")

    def test_invalid_unrelated_incomplete_or_mismatched_responses_rejected(self):
        invalid = ["```python\n"+CODE+"```",CODE+'\nimport os\n',CODE.replace('combine(', 'different('),
                   CODE.replace('right: int = 2','right: int = 3'),CODE.replace('@staticmethod\n',''),
                   CODE.replace('Fixture documentation.','Changed documentation.'),
                   CODE.replace('    total = left + right\n    return total','    pass'),
                   CODE.replace('    total = left + right\n    return total','    ...'),
                   CODE.replace('    total = left + right\n    return total','    raise NotImplementedError'),
                   CODE.replace('    total = left + right\n    return total','    break'), "def combine(:"]
        for code in invalid:
            with self.subTest(code=code[:30]), self.assertRaises(ValidationError):
                prepare_edit(self.root, TARGET, code)
        self.assertEqual(self.path.read_text(), SOURCE)

    def test_multiline_literal_values_survive_indentation_conversion(self):
        code = CODE.replace('    total = left + right\n    return total', '    message = """first\nunchanged literal line\n    final"""\n    return len(message)')
        edit = prepare_edit(self.root, TARGET, code)
        expected = ast.parse(code).body[0].body[1].value.value
        actual = ast.parse(edit.after).body[1].body[0].body[1].value.value
        self.assertEqual(actual, expected)

    def test_escape_symlink_and_concurrent_edit_rejected(self):
        for path in ["../escape.py",str(self.path.resolve())]:
            with self.assertRaises(ValidationError):
                prepare_edit(self.root,{**TARGET,"file":path},CODE)
        edit = prepare_edit(self.root,TARGET,CODE)
        self.path.write_text(SOURCE+'# concurrent edit\n')
        with self.assertRaisesRegex(ValidationError,"concurrently"):
            apply_edit(edit,self.root/'backup.py')
        outside = self.root.parent / (self.root.name+'-outside.py')
        outside.write_text(SOURCE)
        self.addCleanup(outside.unlink)
        link = self.root/'link.py'
        link.symlink_to(outside)
        with self.assertRaises(ValidationError):
            prepare_edit(self.root,{**TARGET,'file':'link.py'},CODE)

    def test_returned_code_is_not_executed_during_patching(self):
        code = CODE.replace('    total = left + right\n    return total','    raise RuntimeError("not executed by editor")')
        apply_edit(prepare_edit(self.root,TARGET,code),self.root/'backup.py')
        self.assertIn('not executed by editor',self.path.read_text())


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="week06-offline-sdk-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'sample.py').write_text(SOURCE)
        self.retriever = ToyRetriever()

    def client(self, handler):
        client = OpenAI(api_key='offline-unit-fixture-key', max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        self.addCleanup(client.close)
        return client

    def solve(self, client=None, **kwargs):
        return solve_task('Combine fixture values.', TARGET, repository=self.root,retriever=self.retriever,
                          evidence_directory=self.root/'evidence',client=client,secrets=('offline-unit-fixture-key',),**kwargs)

    def test_missing_credentials_prepares_only_and_never_modifies_source(self):
        result = self.solve()
        self.assertEqual(result['status'],'blocked_missing_credentials')
        self.assertEqual(result['api_calls'],0)
        self.assertEqual((self.root/'sample.py').read_text(),SOURCE)
        prompt = json.loads((self.root/'evidence/prompt.json').read_bytes())
        supplied = json.loads(prompt['input'])['repository_context']
        self.assertEqual(len(supplied),5)
        self.assertTrue(all(r['text']==SOURCE for r in supplied))
        self.assertFalse(list((self.root/'evidence').glob('attempt-*')))

    def test_sdk_protocol_and_body_edit_with_explicit_mock_transport(self):
        requests = []
        def handler(request):
            requests.append(json.loads(request.content))
            return httpx.Response(200,json=response_fixture())
        result = self.solve(self.client(handler))
        self.assertEqual(result['status'],'applied')
        self.assertEqual(len(requests),1)
        self.assertEqual(set(requests[0]),{'model','instructions','input','max_output_tokens','store'})
        self.assertEqual(result['attempts'][0]['usage'],None)
        self.assertIn('return total',(self.root/'sample.py').read_text())
        for file in (self.root/'evidence').rglob('*'):
            if file.is_file():
                self.assertNotIn('offline-unit-fixture-key',file.read_text())

    def test_code_regeneration_keeps_same_five_chunks_and_records_feedback(self):
        requests=[]
        def handler(request):
            requests.append(json.loads(request.content))
            code = CODE.replace('combine(', 'wrong(') if len(requests)==1 else CODE
            return httpx.Response(200,json=response_fixture(code))
        result = self.solve(self.client(handler),max_regenerations=1)
        self.assertEqual([a['status'] for a in result['attempts']],['validation_failed','applied'])
        first, second = [json.loads(r['input']) for r in requests]
        self.assertEqual(first['repository_context'],second['repository_context'])
        self.assertIn('Previous response rejected',second['feedback'])
        self.assertTrue((self.root/'evidence/attempt-01/returned_code.py').is_file())

    def test_transport_retry_is_not_code_regeneration(self):
        requests=[]
        def handler(request):
            requests.append(request)
            if len(requests)==1:
                return httpx.Response(500,json={'error':{'message':'offline-unit-fixture-key','type':'server_error'}})
            return httpx.Response(200,json=response_fixture())
        with patch('solve_tasks.time.sleep'):
            result = self.solve(self.client(handler),transport_retries=1,max_regenerations=0)
        self.assertEqual(len(result['attempts']),1)
        self.assertEqual(len(result['attempts'][0]['transport']),2)
        self.assertEqual(result['api_calls'],2)
        self.assertEqual(result['status'],'applied')

    def test_incomplete_responses_are_not_applied_and_attempts_are_bounded(self):
        client = self.client(lambda request:httpx.Response(200,json=response_fixture(status='incomplete')))
        result = self.solve(client,max_regenerations=1)
        self.assertEqual(result['status'],'validation_failed')
        self.assertEqual(len(result['attempts']),2)
        self.assertEqual((self.root/'sample.py').read_text(),SOURCE)

    def test_auth_error_is_sanitized_not_retried_or_applied(self):
        client = self.client(lambda request:httpx.Response(401,json={'error':{'message':'offline-unit-fixture-key','type':'invalid_api_key'}}))
        result=self.solve(client)
        self.assertEqual(result['status'],'api_failed')
        self.assertEqual(result['api_calls'],1)
        self.assertEqual((self.root/'sample.py').read_text(),SOURCE)
        self.assertNotIn('offline-unit-fixture-key',(self.root/'evidence/result.json').read_text())

    def test_configuration_uses_only_explicit_local_env_and_enforces_allowlist(self):
        (self.root/'.gitignore').write_text('.env\n.env.*\n!.env.example\n')
        (self.root/'.env').write_text('OPENAI_API_KEY=offline-unit-fixture-key\nOPENAI_MODEL=gpt-5-mini\n')
        with patch.dict(os.environ,{},clear=True):
            config=Configuration.read(self.root)
            self.assertIsNone(config.api_key)
            config=Configuration.read(self.root,self.root/'.env')
            self.assertTrue(config.api_key)
            self.assertNotIn('offline-unit-fixture-key',repr(config))
            with self.assertRaises(ValueError):
                Configuration.read(self.root,model='not-allowed')
        with self.assertRaises(ValueError):
            Configuration.read(self.root,self.root.parent/'.env')


if __name__ == '__main__':
    unittest.main()
