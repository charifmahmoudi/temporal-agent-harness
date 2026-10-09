"""Activity-backed approval probe shared unchanged by all implementation variants.

The ledger write is an actual activity-side filesystem effect, confined to the
experiment output directory. Workflow observations never write files or add awaits.
"""
import asyncio
from datetime import timedelta
import json
import os

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.contrib.workflow_streams import WorkflowStream

from temporal_agent_harness.harness import agent
from temporal_agent_harness.harness.agent import (
    AutoApprovalCriteria, AutoApprovalCriteriaSet, AutoApprovalDecision,
    AutoApprovalVerdict, ToolApprovalPolicy,
)
from temporal_agent_harness.harness.agent_protocol import AgentConfig, TextMessage, TextReply
from temporal_agent_harness.harness.agent_workflow import AgentWorkflowRunner, ToolApprovalDenied


@agent.activity_tool_defn(activity_config=workflow.ActivityConfig(
    start_to_close_timeout=timedelta(seconds=20),
    retry_policy=RetryPolicy(maximum_attempts=1),
))
async def ledger_probe(case_id: str) -> str:
    """Append one durable test record; no production service is contacted."""
    info = activity.info()
    record = {'case_id': case_id, 'workflow_id': info.workflow_id,
              'run_id': info.workflow_run_id, 'activity_id': info.activity_id,
              'attempt': info.attempt, 'source_sha256': os.environ['ACTIVITY_SOURCE_SHA']}
    # One append, flushed before completion. This is an observed effect, not an
    # exactly-once primitive: retries are disabled only for this experiment.
    with open(os.environ['ACTIVITY_LEDGER'], 'a') as ledger:
        ledger.write(json.dumps(record, sort_keys=True) + '\n')
        ledger.flush()
        os.fsync(ledger.fileno())
    return 'recorded'


class ActivityObserver(AgentWorkflowRunner):
    def _pub(self, *args, **kwargs):
        super()._pub(*args, **kwargs)
        self.events.append(args[2].model_dump(mode='json'))


@agent.defn
class ActivityAgent:
    @agent.init
    def __init__(self, config: AgentConfig):
        self.mode = ''
        self.case_id = ''
        self.started = False
        self.cleanup_entered = False
        self.second_cancel = False
        self.caller_cancel_requested = False
        self.caller = None
        self.outcome = None
        self.checkpoints = 0
        self._runner = ActivityObserver(
            config, stream=WorkflowStream(),
            approval_policy_default=ToolApprovalPolicy.auto_mode(),
            auto_approval_criteria_default=AutoApprovalCriteria(
                sets={'probe': AutoApprovalCriteriaSet(effect='test ledger', escalate_when=('test',))},
                default='probe'), auto_mode_evaluator=self.evaluate)
        self._runner.events = []

    async def evaluate(self, ctx):
        self.started = True
        try:
            await workflow.wait_condition(lambda: False)
        except asyncio.CancelledError:
            self.cleanup_entered = True
            if self.mode in {'second_raise', 'second_return'}:
                try:
                    await workflow.wait_condition(lambda: False)
                except asyncio.CancelledError:
                    self.second_cancel = True
                    if self.mode == 'second_return':
                        return AutoApprovalDecision(AutoApprovalVerdict.DENY)
                    raise
            raise

    @agent.accepts
    async def act(self, message: TextMessage) -> TextReply:
        """Invoke one real activity through the unchanged harness approval path."""
        self.mode, self.case_id = message.text.split(':', 1)
        self.caller = asyncio.current_task()
        try:
            await self._runner.run_tool('call', ledger_probe, self.case_id)
        except ToolApprovalDenied:
            self.outcome = 'rejected'
        except asyncio.CancelledError:
            self.outcome = 'cancelled'
        else:
            self.outcome = 'dispatched'
        return TextReply(text=self.outcome)

    @workflow.signal
    def cancel_caller(self):
        self.caller_cancel_requested = True
        self.caller.cancel()

    @workflow.signal
    def checkpoint(self):
        # A visible counter proves that the replacement processed new input.
        self.checkpoints += 1

    @workflow.query
    def evidence(self):
        entry = self._runner._status.approval_entry('call')
        return {'status': entry.status.value if entry else None,
                'started': self.started, 'cleanup_entered': self.cleanup_entered,
                'second_cancel': self.second_cancel,
                'caller_cancel_requested': self.caller_cancel_requested,
                'outcome': self.outcome, 'checkpoints': self.checkpoints,
                'events': self._runner.events}
