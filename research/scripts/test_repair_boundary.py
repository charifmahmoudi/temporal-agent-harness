"""Negative controls for inventory scope and drift; no semantic proof claim."""
import unittest

from extract_repair_boundary import inventory, build


class BoundaryTests(unittest.TestCase):
    def test_deferred_calls_are_not_eager_calls(self):
        source = '''async def f():
    def hidden():
        workflow.execute_activity("hidden")
    await workflow.wait_condition(lambda: task.done())
'''
        row = inventory(source, 'f')
        self.assertEqual([x['text'] for x in row['calls']], ['workflow.wait_condition'])
        self.assertEqual([x['text'] for x in row['deferred']], ['hidden', '<lambda>'])

    def test_changed_exception_and_guard_are_visible(self):
        source = '''async def f(task):
    try:
        await task
    except Exception:
        pass
    if task.cancelled():
        raise RuntimeError
'''
        old = inventory(source, 'f')
        new = inventory(source.replace('except Exception:', 'except BaseException:'), 'f')
        self.assertNotEqual(old['ast_sha256'], new['ast_sha256'])
        self.assertEqual(new['handlers'][0]['text'], 'BaseException')
        self.assertEqual(old['guards'][0]['text'], 'task.cancelled()')

    def test_ambiguous_definition_is_rejected(self):
        with self.assertRaises(ValueError):
            inventory('def f(): pass\ndef f(): pass', 'f')

    def test_missing_target_is_rejected(self):
        with self.assertRaises(KeyError):
            inventory('def other(): pass', 'f')

    def test_actual_variants_expose_different_inputs(self):
        result = build()
        calls = [{x['text'] for x in v['functions'][0]['calls']} for v in result['variants']]
        self.assertNotIn('caller.cancelling', calls[0])
        self.assertIn('caller.cancelling', calls[1])
        self.assertNotIn('workflow.patched', calls[1])
        self.assertIn('workflow.patched', calls[2])
        self.assertTrue(result['analysis_status'].startswith('unsupported'))


if __name__ == '__main__':
    unittest.main()
