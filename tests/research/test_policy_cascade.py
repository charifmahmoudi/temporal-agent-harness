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
    def snapshot(self, label, action=None):
        entries = [self._status.approval_entry(c) for c in ('a', 'b')]
        if not all(entries):
            return  # The model begins after both calls are registered.
        actual_allowed = self.approval_policy.auto_approve_tools
        self.observations.append({'label': label, 'action': action, 'state': {
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
        self.snapshot('human_and_optional_cascade', {'kind': 'remember' if decision.approved and decision.remember else 'human',
                                                   'call': decision.tool_id, 'approved': decision.approved})
        return result

    def _handle_close(self):
        super()._handle_close()
        self.snapshot('close', {'kind': 'close'})


@agent.defn
class CascadeAgent:
    @agent.init
    def __init__(self, config: AgentConfig):
        self.release = False
        self.cleanup = False
        self.started = set()
        self.cancelled = set()
        self.scenario = ''
        self.registration_order = ['a', 'b']
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
        if self.scenario == 'invalid_superseded':
            # Force accepted settlement and malformed completion to be observable
            # together. This controls the internal branch, not network request order.
            decision = ToolApprovalDecision(tool_id=call, approved=True)
            self._runner._validate_tool_approval(decision)
            await self._runner._handle_tool_approval(decision)
            return None
        try:
            await workflow.wait_condition(lambda: self.release and call == 'a')
        except asyncio.CancelledError:
            self.cancelled.add(call)
            if self.scenario == 'tighten_after_release':
                await workflow.wait_condition(lambda: self.cleanup)
            raise
        verdict = {'evaluator_approve_first': 'approve', 'evaluator_escalate_first': 'escalate',
                   'evaluator_error_first': 'error'}.get(self.scenario, 'deny')
        # No await separates this marker from returning/raising. Completion is
        # recorded explicitly so the checker cannot invent evaluator verdicts.
        self._runner.snapshot('evaluator_return', {'kind': 'complete', 'call': call, 'verdict': verdict})
        if verdict == 'error':
            raise RuntimeError('controlled evaluator failure')
        return AutoApprovalDecision(AutoApprovalVerdict(verdict), reason='controlled evaluator result')

    @agent.accepts
    async def act(self, message: TextMessage) -> TextReply:
        """Start two gated calls with controlled evaluation and cleanup barriers."""
        self.scenario, order = message.text.split(':')
        self.registration_order = list(order)
        async def invoke(call, tool):
            try:
                await self._runner.run_tool(call, tool)
                self._runner.outcomes[call] = 'dispatched'
            except ToolApprovalDenied:
                self._runner.outcomes[call] = 'rejected'
            except AttributeError:
                if self.scenario != 'invalid_superseded':
                    raise
                # Preserve the failure as evidence instead of waiting for a timeout.
                self._runner.outcomes[call] = 'failed'
            self._runner.snapshot('caller_finished')
        tools = {'a': shared_probe, 'b': other_probe if self.scenario == 'different_tool' else shared_probe}
        await asyncio.gather(*(invoke(call, tools[call]) for call in self.registration_order))
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
        # Policy replacement resolves eligible siblings synchronously. Record its
        # stable boundary, while _pub retains every intermediate raw event.
        self._runner.operator_active = True
        try:
            self._runner.set_approval_policy(policy)
        finally:
            self._runner.operator_active = False
        self._runner.snapshot('policy_replaced', {'kind': 'policy', 'allowed': ['shared'] if allow else []})

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
             'policy_relax', 'tighten_after_release', 'different_tool', 'close_first', 'remember_then_close',
             'evaluator_approve_first', 'evaluator_escalate_first', 'evaluator_error_first']


@pytest.mark.parametrize('order', ['ab', 'ba'])
@pytest.mark.parametrize('scenario', SCENARIOS)
async def test_policy_cascade_trace(cascade_environment, scenario, order):
    client, queue = cascade_environment
    h = await client.start_workflow(CascadeAgent.run, AgentConfig(), id=f'cascade-{uuid.uuid4()}', task_queue=queue)
    await h.execute_update('send_agent_message', AgentMessage(type='act', payload={'text': f'{scenario}:{order}'}))
    start = await until(h, lambda e: e['started'] == ['a', 'b'])
    registration = [e['tool_id'] for e in start['events'] if e['type'] == 'tool_approval_requested']
    assert registration == list(order)  # Evidence determines the model's registration order.

    async def decide(call, approved=True, remember=False):
        await h.execute_update('tool_approval', ToolApprovalDecision(tool_id=call, approved=approved, remember=remember))

    if scenario in {'evaluator_approve_first', 'evaluator_escalate_first', 'evaluator_error_first'}:
        await h.signal(CascadeAgent.release_denial)
        if scenario == 'evaluator_approve_first':
            await until(h, lambda e: e['outcomes'].get('a') == 'dispatched')
        else:
            terminal = 'auto_approval_evaluation_error' if scenario == 'evaluator_error_first' else 'auto_approval_evaluation_ended'
            e = await until(h, lambda e: any(x['type'] == terminal and x.get('tool_id') == 'a' for x in e['events']))
            assert not e['outcomes']  # Error/escalation must not release a call.
            assert e['observations'][-1]['state']['status']['a'] == 'pending'
        await decide('b', remember=True)
    elif scenario == 'evaluator_deny_first':
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
    if scenario in {'policy_relax', 'tighten_after_release'}:
        assert resolved == list(order)  # Synchronous siblings follow registration order.
    if scenario in {'remember_first', 'close_first', 'remember_then_close'}:
        assert resolved == ['b', 'a']  # Cause precedes cascade despite registration order.
    output = Path('research/results/cascade-traces')
    output.mkdir(parents=True, exist_ok=True)
    evidence.update(schema=2, scenario=scenario, registration_order=list(order), different_tools=scenario == 'different_tool', workflow_id=h.id,
                    implementation_sha256=hashlib.sha256(Path('temporal_agent_harness/harness/agent_workflow.py').read_bytes()).hexdigest())
    (output / f'{scenario}_{order}.json').write_text(json.dumps(evidence, indent=2) + '\n')
    if scenario not in {'close_first', 'remember_then_close'}:
        await h.signal('close')
    await h.result()


async def test_malformed_superseded_result_real_temporal(cascade_environment):
    """A completed malformed evaluator cannot abort a gate already approved."""
    client, queue = cascade_environment
    h = await client.start_workflow(CascadeAgent.run, AgentConfig(), id=f'malformed-{uuid.uuid4()}', task_queue=queue)
    await h.execute_update('send_agent_message', AgentMessage(type='act', payload={'text': 'invalid_superseded:ab'}))
    evidence = await until(h, lambda e: len(e['outcomes']) == 2)
    output = Path('research/results/malformed-evaluator')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'temporal.json').write_text(json.dumps(evidence, indent=2) + '\n')
    assert evidence['outcomes'] == {'a': 'dispatched', 'b': 'dispatched'}
    terminals = [e for e in evidence['events'] if e['type'].startswith('auto_approval_evaluation_') and e['type'] != 'auto_approval_evaluation_started']
    assert len(terminals) == 2
    assert all(e['type'] == 'auto_approval_evaluation_superseded' and e['verdict'] is None for e in terminals)
    await h.signal('close')
    await h.result()
