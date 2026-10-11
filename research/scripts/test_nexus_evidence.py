"""Adversarial checks for failure attribution and retained Nexus evidence."""
import base64
import copy
import io
import json
from pathlib import Path
import unittest
import zipfile

from audit_nexus_evidence import audit
from prepare_nexus_continuations import fixture
from run_nexus_context import classify
from identity_scoring import decoding_mechanism

ROOT = Path(__file__).resolve().parents[1]
CASE = "nexus_context_completed_cached"
MESSAGE = "TMPRL1100: a waker was invoked by a non-SDK source"


class AttributionTests(unittest.TestCase):
    def verdict(self, events, log="", code=1):
        return classify({"events": events}, log, code, CASE)["verdict"]

    def test_confirm_only_recorded_failure_after_result(self):
        events = [{"event_id": 1, "event_type": 50},
                  {"event_id": 2, "event_type": 9, "message": MESSAGE}]
        self.assertEqual(self.verdict(events), "confirmed_mechanism")

    def test_failure_before_result_is_not_confirmation(self):
        events = [{"event_id": 1, "event_type": 9, "message": MESSAGE},
                  {"event_id": 2, "event_type": 50}]
        self.assertEqual(self.verdict(events), "inconclusive")

    def test_unrelated_payload_string_is_not_confirmation(self):
        self.assertEqual(self.verdict([{"event_id": 1, "event_type": 50, "payload": MESSAGE}]), "inconclusive")

    def test_success_requires_operation_completion(self):
        self.assertEqual(self.verdict([{"event_id": 1, "event_type": 2}],
            f"RECOVERY_PHASE {CASE} offline=passed", 0), "inconclusive")

    def test_timeout_log_alone_is_not_confirmation(self):
        self.assertEqual(self.verdict([{"event_id": 1, "event_type": 50}], MESSAGE), "inconclusive")

    def test_camel_case_serialization(self):
        events = [{"eventId": "1", "eventType": "EVENT_TYPE_NEXUS_OPERATION_COMPLETED"},
                  {"eventId": "2", "eventType": "EVENT_TYPE_WORKFLOW_TASK_FAILED", "message": MESSAGE}]
        self.assertEqual(self.verdict(events), "confirmed_mechanism")


class RetainedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / "evaluation/open-recovery-evidence.json").read_text())

    def test_all_retained_evidence_rederives(self):
        report = audit(self.bundle)
        self.assertEqual([r["verdicts"] for r in report["arms"]],
                         [{"passed": 6, "confirmed_mechanism": 6}, {"passed": 12}])

    def test_archive_hash_drift_rejected(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["arms"][0]["archive_sha256"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "Archive hash mismatch"):
            audit(bundle)

    def test_fixture_generated_from_frozen_upstream_and_drift_rejected(self):
        raw = base64.b64decode(self.bundle["arms"][0]["archive_zip_base64"])
        source = zipfile.ZipFile(io.BytesIO(raw)).read("fixture/fixture.rs").decode()
        prefix = source[:source.index("#[workflow]\nstruct NexusContextWf")]
        generated = None
        for candidate in (prefix, prefix[:-1], prefix[:-2]):
            try:
                generated = fixture(candidate)
                break
            except ValueError:
                pass
        self.assertIsNotNone(generated, "Frozen upstream source not recovered")
        self.assertEqual(generated.count("async fn nexus_continuation_"), 8)
        with self.assertRaisesRegex(ValueError, "frozen source"):
            fixture(candidate + "\n")


class IdentityBridgeTests(unittest.TestCase):
    def test_direct_python_cause(self):
        self.assertTrue(decoding_mechanism([{"type": "TypeError", "message": "Expected value to be str, was <class 'bool'>"}]))

    def test_serialized_native_cause(self):
        from audit_local_activity_evidence import audit as audit_identity
        bundle = json.loads((ROOT / "evaluation/local-activity-evidence.json").read_text())
        report = audit_identity(bundle)
        self.assertEqual(report["arms"][0]["verdicts"], {"reported_decoding_mechanism": 3, "compatible": 3})

    def test_generic_runtime_error_is_not_confirmation(self):
        self.assertFalse(decoding_mechanism([{"type": "RuntimeError", "message": "Failed decoding arguments"}]))

    def test_quoted_type_text_without_native_cause_is_not_confirmation(self):
        self.assertFalse(decoding_mechanism([{"type": "RuntimeError", "message": 'Expected value to be str bool Failed decoding arguments r#type: "TypeError"'}]))


class ContinuationDiagnosisTests(unittest.TestCase):
    def test_first_cached_failures_precede_replay_and_eviction(self):
        from prepare_nexus_continuations import SUFFIXES
        cases = [f"nexus_continuation_{s}_{c}" for s in SUFFIXES for c in ("cached", "cold")]
        report = audit(json.loads((ROOT / "evaluation/continuation-evidence.json").read_text()), cases)
        affected = report["arms"][0]
        self.assertEqual(affected["verdicts"], {"passed": 12, "confirmed_mechanism": 12})
        self.assertEqual(report["arms"][1]["verdicts"], {"passed": 24})
        failures = [r for r in affected["rows"] if r["verdict"] == "confirmed_mechanism"]
        for row in failures:
            self.assertEqual(row["wake_failure_markers"][0], "false")
            self.assertTrue(row["timer_fired_events"])
            if row["case"].endswith("cached"):
                self.assertTrue(row["caller_activations_before_first_wake_failure"])
                self.assertEqual(set(map(tuple, row["caller_activations_before_first_wake_failure"])), {("false", "false")})


if __name__ == "__main__":
    unittest.main()
