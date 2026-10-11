"""Hand-specified oracles and source-mutation controls for the bounded comparison."""
from dataclasses import replace
import unittest

from compare_repair_encodings import (
    Case, MARKER, Result, compile_helper, cursor_match, explicit, helper_sources,
    merged, protocol, reduced,
)


class EncodingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = protocol()
        cls.contexts = {c['name']: c for c in cls.p['contexts']}
        cls.sources = helper_sources()
        cls.codes = {v: compile_helper(s) for v, s in cls.sources.items()}

    def case(self, variant='V', schedule=('cancel',), child='return',
             context='fresh_on', approved=True):
        return Case(variant, schedule, child, approved, context,
                    'activity:tool:arg0:options0')

    def check_all(self, case, expected):
        ctx = self.contexts[case.context]
        self.assertEqual(explicit(case, ctx, self.p), expected)
        self.assertEqual(merged(case, ctx, self.p, self.codes), expected)
        self.assertEqual(reduced(case, ctx, self.p), expected)

    def test_child_only_cancel_does_not_cancel_caller(self):
        c = self.case(variant='C', schedule=(), child='cancel')
        self.check_all(c, Result('scheduled', 0, (c.signature,)))

    def test_normal_child_return_does_not_clear_caller_request(self):
        self.check_all(self.case(variant='C'), Result('cancelled', 0, ()))

    def test_count_one_and_two_need_different_uncancel_results(self):
        one = self.case(variant='C', schedule=('cancel', 'uncancel'))
        two = self.case(variant='C', schedule=('cancel', 'cancel', 'uncancel'))
        self.check_all(one, Result('scheduled', 0, (one.signature,)))
        self.check_all(two, Result('cancelled', 0, ()))

    def test_fresh_disabled_activation_preserves_old_behavior(self):
        c = self.case(context='fresh_off')
        self.check_all(c, Result('scheduled', 1, (c.signature,)))

    def test_patch_call_is_skipped_at_zero_counter(self):
        c = self.case(schedule=())
        self.check_all(c, Result('scheduled', 0, (c.signature,)))

    def test_replay_notification_changes_patch_branch(self):
        c = self.case(context='replay_absent')
        self.check_all(c, Result('scheduled', 1, (c.signature,)))
        self.check_all(replace(c, context='replay_present'), Result('cancelled', 1, (MARKER,)))

    def test_true_memo_does_not_emit_second_marker(self):
        self.check_all(self.case(context='fresh_memo_true'), Result('cancelled', 1, ()))

    def test_word_cursor_preserves_payload_order_and_multiplicity(self):
        a = 'activity:tool:arg0:options0'
        for word in [(a, MARKER), (MARKER,), (MARKER, a, a),
                     (MARKER, 'activity:tool:arg1:options0'),
                     (MARKER, 'activity:tool:arg0:options1')]:
            self.assertFalse(cursor_match((MARKER, a), word))
        self.assertTrue(cursor_match((MARKER, a), (MARKER, a)))

    def test_unknown_operation_is_rejected(self):
        self.check_all(self.case(schedule=('unknown',)), None)

    def test_unknown_signature_is_rejected(self):
        self.check_all(replace(self.case(), signature='dynamic:unknown'), None)

    def test_source_mutation_is_detected_against_operational_oracle(self):
        # This alters executed source, not the reduced formula or reference.
        source = self.sources['C'].replace('caller.cancelling():', 'not caller.cancelling():')
        self.assertNotEqual(source, self.sources['C'])
        codes = {**self.codes, 'C': compile_helper(source)}
        c = self.case(variant='C')
        ctx = self.contexts[c.context]
        self.assertEqual(explicit(c, ctx, self.p), Result('cancelled', 0, ()))
        self.assertEqual(merged(c, ctx, self.p, codes), Result('scheduled', 0, (c.signature,)))


if __name__ == '__main__':
    unittest.main()
