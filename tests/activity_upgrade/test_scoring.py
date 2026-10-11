"""Keep durable scheduling, effects, and explicit nondeterminism distinct."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'research/scripts'))
from run_activity_study import history_projection
from replay_upgrade import command_result
from temporalio.workflow import NondeterminismError


class History:
    def __init__(self, events):
        self.events = events

    def to_json(self):
        return json.dumps({'events': self.events})


def test_scheduling_does_not_require_completion_or_effect_evidence():
    projection = history_projection(History([
        {'eventId': '3', 'eventType': 'EVENT_TYPE_WORKFLOW_EXECUTION_SIGNALED',
         'workflowExecutionSignaledEventAttributes': {'signalName': 'cancel_caller'}},
        {'eventId': '7', 'eventType': 'EVENT_TYPE_ACTIVITY_TASK_SCHEDULED'},
    ]))
    assert projection['scheduled'] == [7]
    assert projection['completed'] == []
    assert projection['caller_signals'][0] < projection['scheduled'][0]


def test_only_explicit_nondeterminism_is_scored_as_incompatibility():
    projection = history_projection(History([
        {'eventId': '8', 'eventType': 'EVENT_TYPE_WORKFLOW_TASK_FAILED',
         'workflowTaskFailedEventAttributes': {'cause': 'WORKFLOW_TASK_FAILED_CAUSE_UNHANDLED_COMMAND'}},
        {'eventId': '11', 'eventType': 'EVENT_TYPE_WORKFLOW_TASK_FAILED',
         'workflowTaskFailedEventAttributes': {'cause': 'WORKFLOW_TASK_FAILED_CAUSE_NON_DETERMINISTIC_ERROR'}},
    ]))
    assert projection['nondeterministic_tasks'] == [11]
    assert command_result(TimeoutError()) == 'experiment_error'
    assert command_result(NondeterminismError('controlled')) == 'nondeterministic'


def test_checkpoint_is_not_caller_cancellation():
    projection = history_projection(History([
        {'eventId': '2', 'eventType': 'EVENT_TYPE_WORKFLOW_EXECUTION_SIGNALED',
         'workflowExecutionSignaledEventAttributes': {'signalName': 'checkpoint'}},
    ]))
    assert projection['caller_signals'] == []
