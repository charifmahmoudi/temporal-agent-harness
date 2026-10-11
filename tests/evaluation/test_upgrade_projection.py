"""Scoring controls: incomplete evidence must never masquerade as compatibility."""
import sys
from pathlib import Path

import pytest
from temporalio.workflow import NondeterminismError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'research/scripts'))
from replay_upgrade import command_result, comparison, projection


@pytest.mark.parametrize('failure,expected', [
    (None, 'compatible'),
    (NondeterminismError('controlled mismatch'), 'nondeterministic'),
    (TimeoutError('controlled timeout'), 'experiment_error'),
    (RuntimeError('controlled setup error'), 'experiment_error'),
])
def test_command_failure_classification(failure, expected):
    assert command_result(failure) == expected


def test_semantic_change_can_coexist_with_command_compatibility():
    before = {'status': 'approved', 'outcome': 'dispatched', 'events': [
        {'type': 'auto_approval_evaluation_started'},
        {'type': 'auto_approval_evaluation_superseded'}, {'type': 'tool_start'}]}
    after = {'status': 'approved', 'outcome': 'cancelled', 'events': [
        {'type': 'auto_approval_evaluation_started'},
        {'type': 'auto_approval_evaluation_superseded'}]}
    assert command_result(None) == 'compatible'
    assert comparison(projection(before), projection(after)) == 'mismatch'
    assert projection(after)['evaluation_terminals'] == 1


def test_missing_oracle_and_missing_observation_are_distinct():
    assert comparison(None, {'outcome': 'cancelled'}) == 'unavailable'
    assert comparison({'outcome': 'cancelled'}, None) == 'missing_observation'


def test_audit_terminal_loss_is_a_semantic_mismatch():
    expected = {'status': 'approved', 'outcome': 'cancelled', 'events': [
        {'type': 'auto_approval_evaluation_superseded'}]}
    missing_terminal = dict(expected, events=[])
    assert comparison(projection(expected), projection(missing_terminal)) == 'mismatch'
