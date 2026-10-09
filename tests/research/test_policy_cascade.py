"""Real Temporal experiments for coupled gates; production policy paths stay intact.

Snapshots are taken after synchronous operator actions, not between individual
publications inside a cascade. Raw events independently retain publication order.
"""
import asyncio
import hashlib
import json
from pathlib import Path
import uuid

import pytest
import pytest_asyncio
from temporalio import workflow
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.contrib.workflow_streams import WorkflowStream
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from temporal_agent_harness.harness import agent
from temporal_agent_harness.harness.agent_workflow import AgentWorkflowRunner, ToolApprovalDenied
from temporal_agent_harness.harness.agent import AutoApprovalCriteria, AutoApprovalCriteriaSet, AutoApprovalDecision, AutoApprovalVerdict, ToolApprovalPolicy
from temporal_agent_harness.harness.agent_protocol import AgentConfig, AgentMessage, TextMessage, TextReply, ToolApprovalDecision


@agent.tool_defn()
async def shared_probe() -> str:
    return 'shared executed'


@agent.tool_defn()
async def other_probe() -> str:
    return 'other executed'


class CascadeObserver(AgentWorkflowRunner):
    def snapshot(self, label):
        entries = [self._status.approval_entry(c) for c in ('a', 'b')]
        if not all(entries):
            return  # The model begins after both calls are registered.
        actual_allowed = self.approval_policy.auto_approve_tools
        self.observations.append({'label': label, 'state': {
            'status': {e.tool_id: e.status.value for e in entries},
            'closed': self._closed,
            'allowed': [symbol for name, symbol in [('shared_probe', 'shared'), ('other_probe', 'other')]
                        if name in actual_allowed],
            'history': [e['tool_id'] for e in self.events if e['type'] == 'tool_approval_resolved'],
            'phase': dict(self.outcomes),
        }})

    def _pub(self, *args, **kwargs):
        super()._pub(*args, **kwargs)
        self.events.append(args[2].model_dump(mode='json'))

    def _resolve_and_publish(self, *args, **kwargs):
        super()._resolve_and_publish(*args, **kwargs)
        if not self.operator_active:
            self.snapshot('evaluation_resolution')

    async def _handle_tool_approval(self, decision: ToolApprovalDecision):
        # Preserve the registered handler's annotation: Temporal uses it to decode
        # update payloads before calling this observation-only wrapper.
        self.operator_active = True
        try:
            result = await super()._handle_tool_approval(decision)
        finally:
            self.operator_active = False
        self.snapshot('human_and_optional_cascade')
        return result

    def _handle_close(self):
        super()._handle_close()
        self.snapshot('close')


@agent.defn
class CascadeAgent:
    @agent.init
    def __init__(self, config: AgentConfig):
        self.release = False
        self.cleanup = False
        self.started = set()
        self.cancelled = set()
        self.scenario = ''
        self._runner = CascadeObserver(
            config, stream=WorkflowStream(), approval_policy_default=ToolApprovalPolicy.auto_mode(),
            auto_approval_criteria_default=AutoApprovalCriteria(
                sets={'probe': AutoApprovalCriteriaSet(effect='test', escalate_when=('test',))}, default='probe'),
            auto_mode_evaluator=self.evaluate)
        self._runner.events = []
        self._runner.observations = []
        self._runner.outcomes = {}
        self._runner.operator_active = False

    async def evaluate(self, ctx):
        # The ambient call ID remains scoped to this evaluator's spawned task.
        call = agent.AgentToolContext.for_current_tool_id().tool_id
        self.started.add(call)
        self._runner.snapshot('both_registered_evaluators_running')
        try:
            await workflow.wait_condition(lambda: self.release and call == 'a')
        except asyncio.CancelledError:
            self.cancelled.add(call)
            if self.scenario == 'tighten_after_release':
                await workflow.wait_condition(lambda: self.cleanup)
            raise
        return AutoApprovalDecision(AutoApprovalVerdict.DENY, reason='controlled evaluator denial')

    @agent.accepts
    async def act(self, message: TextMessage) -> TextReply:
        """Start two gated calls with controlled evaluation and cleanup barriers."""
        self.scenario = message.text
        async def invoke(call, tool):
            try:
                await self._runner.run_tool(call, tool)
                self._runner.outcomes[call] = 'dispatched'
            except ToolApprovalDenied:
                self._runner.outcomes[call] = 'rejected'
            self._runner.snapshot('caller_finished')
        await asyncio.gather(invoke('a', shared_probe), invoke('b', other_probe if self.scenario == 'different_tool' else shared_probe))
        return TextReply(text='finished')

    @workflow.signal
    def release_denial(self):
        self.release = True

    @workflow.signal
    def release_cleanup(self):
        self.cleanup = True

    @workflow.update
    async def replace_policy(self, allow: bool):
        # Preserve auto mode so this experiment isolates name-based eligibility.
        policy = ToolApprovalPolicy.auto_mode(pre_approved_tools=['shared_probe'] if allow else [])
        self._runner.set_approval_policy(policy)
        self._runner.snapshot('policy_replaced')

    @workflow.update
    async def close_and_remember(self, close_first: bool):
        # One non-suspending handler establishes both concrete orderings without
        # claiming the network can reliably place a separate update between them.
        if close_first:
            self._runner._handle_close()
        decision = ToolApprovalDecision(tool_id='b', approved=True, remember=True)
        self._runner._validate_tool_approval(decision)
        await self._runner._handle_tool_approval(decision)
        if not close_first:
            self._runner._handle_close()

    @workflow.query
    def evidence(self):
        return {'observations': self._runner.observations, 'events': self._runner.events,
                'started': sorted(self.started), 'cancelled': sorted(self.cancelled),
                'outcomes': self._runner.outcomes}


@pytest_asyncio.fixture
async def cascade_environment():
    env = await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter)
    queue = f'cascade-{uuid.uuid4()}'
    async with Worker(env.client, task_queue=queue, workflows=[CascadeAgent], workflow_runner=UnsandboxedWorkflowRunner()):
        try:
            yield env.client, queue
        finally:
            await env.shutdown()


async def until(handle, predicate):
    async with asyncio.timeout(30):
        while True:
            evidence = await handle.query(CascadeAgent.evidence)
            if predicate(evidence):
                return evidence
            await asyncio.sleep(0.02)


SCENARIOS = ['remember_first', 'evaluator_deny_first', 'human_deny_first', 'denied_remember',
             'policy_relax', 'tighten_after_release', 'different_tool', 'close_first', 'remember_then_close']


@pytest.mark.parametrize('scenario', SCENARIOS)
async def test_policy_cascade_trace(cascade_environment, scenario):
    client, queue = cascade_environment
    h = await client.start_workflow(CascadeAgent.run, AgentConfig(), id=f'cascade-{uuid.uuid4()}', task_queue=queue)
    await h.execute_update('send_agent_message', AgentMessage(type='act', payload={'text': scenario}))
    start = await until(h, lambda e: e['started'] == ['a', 'b'])
    registration = [e['tool_id'] for e in start['events'] if e['type'] == 'tool_approval_requested']
    assert registration == ['a', 'b']  # Model's fixed registration order is evidenced.

    async def decide(call, approved=True, remember=False):
        await h.execute_update('tool_approval', ToolApprovalDecision(tool_id=call, approved=approved, remember=remember))

    if scenario == 'evaluator_deny_first':
        await h.signal(CascadeAgent.release_denial)
        await until(h, lambda e: e['outcomes'].get('a') == 'rejected')
        await decide('b', remember=True)
    elif scenario == 'human_deny_first':
        await decide('a', approved=False)
        await decide('b', remember=True)
    elif scenario == 'denied_remember':
        await decide('b', approved=False, remember=True)
        e = await until(h, lambda e: e['outcomes'].get('b') == 'rejected')
        assert e['observations'][-1]['state']['allowed'] == []
        assert e['observations'][-1]['state']['status']['a'] == 'pending'
        await decide('a', approved=False)
    elif scenario in {'policy_relax', 'tighten_after_release'}:
        await h.execute_update(CascadeAgent.replace_policy, True)
        if scenario == 'tighten_after_release':
            await until(h, lambda e: e['cancelled'] == ['a', 'b'])
            await h.execute_update(CascadeAgent.replace_policy, False)
            e = await h.query(CascadeAgent.evidence)
            assert not e['outcomes']
            assert e['observations'][-1]['state']['status'] == {'a': 'approved', 'b': 'approved'}
            await h.signal(CascadeAgent.release_cleanup)
    elif scenario == 'different_tool':
        await decide('a', remember=True)
        e = await until(h, lambda e: e['outcomes'].get('a') == 'dispatched')
        assert e['observations'][-1]['state']['status']['b'] == 'pending'
        await decide('b', approved=False)
    elif scenario in {'close_first', 'remember_then_close'}:
        await h.execute_update(CascadeAgent.close_and_remember, scenario == 'close_first')
    else:
        await decide('b', remember=True)

    evidence = await until(h, lambda e: len(e['outcomes']) == 2)
    expected = {'a': 'dispatched', 'b': 'dispatched'}
    if scenario in {'evaluator_deny_first', 'human_deny_first'}:
        expected['a'] = 'rejected'
    elif scenario == 'denied_remember':
        expected = {'a': 'rejected', 'b': 'rejected'}
    elif scenario == 'different_tool':
        expected['b'] = 'rejected'
    assert evidence['outcomes'] == expected
    resolved = [e['tool_id'] for e in evidence['events'] if e['type'] == 'tool_approval_resolved']
    assert len(resolved) == len(set(resolved)) == 2
    if scenario in {'remember_first', 'close_first', 'remember_then_close'}:
        assert resolved == ['b', 'a']  # Cause precedes cascade despite registration order.
    output = Path('research/results/cascade-traces')
    output.mkdir(parents=True, exist_ok=True)
    evidence.update(schema=1, scenario=scenario, different_tools=scenario == 'different_tool', workflow_id=h.id,
                    implementation_sha256=hashlib.sha256(Path('temporal_agent_harness/harness/agent_workflow.py').read_bytes()).hexdigest())
    (output / f'{scenario}.json').write_text(json.dumps(evidence, indent=2) + '\n')
    if scenario not in {'close_first', 'remember_then_close'}:
        await h.signal('close')
    await h.result()
