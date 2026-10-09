"""Supported-API cancellation experiments with evidence retained before assertions.

No production await is added. Baseline and isolated correction share these stimuli;
only the explicit caller-cancellation expectation differs between the variants.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import uuid

import pytest
import pytest_asyncio
from temporalio import workflow
from temporalio.client import WorkflowExecutionStatus
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.contrib.workflow_streams import WorkflowStream
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, UnsandboxedWorkflowRunner, Worker

from temporal_agent_harness.harness import agent
from temporal_agent_harness.harness.agent import AutoApprovalCriteria, AutoApprovalCriteriaSet, AutoApprovalDecision, AutoApprovalVerdict, ToolApprovalPolicy
from temporal_agent_harness.harness.agent_protocol import AgentConfig, AgentMessage, TextMessage, TextReply, ToolApprovalDecision
from temporal_agent_harness.harness.agent_workflow import AgentWorkflowRunner, ToolApprovalDenied

VARIANT = os.environ.get('CANCELLATION_VARIANT', 'baseline')
OUTPUT = Path('research/results/cancellation') / VARIANT


@agent.tool_defn()
async def cleanup_probe() -> str:
    return 'executed'


class CleanupObserver(AgentWorkflowRunner):
    def _pub(self, *args, **kwargs):
        super()._pub(*args, **kwargs)
        self.events.append(args[2].model_dump(mode='json'))


@agent.defn
class CleanupAgent:
    @agent.init
    def __init__(self, config: AgentConfig):
        self.mode = 'propagate'
        self.started = False
        self.cleanup_entered = False
        self.cleanup_release = False
        self.second_cancel = False
        self.caller_cancel_requested = False
        self.caller = None
        self.outcome = None
        self.done = False
        self._runner = CleanupObserver(
            config, stream=WorkflowStream(), approval_policy_default=ToolApprovalPolicy.auto_mode(),
            auto_approval_criteria_default=AutoApprovalCriteria(
                sets={'probe': AutoApprovalCriteriaSet(effect='test', escalate_when=('test',))}, default='probe'),
            auto_mode_evaluator=self.evaluate)
        self._runner.events = []

    async def evaluate(self, ctx):
        self.started = True
        try:
            await workflow.wait_condition(lambda: False)
        except asyncio.CancelledError:
            self.cleanup_entered = True
            if self.mode == 'raise':
                raise RuntimeError('controlled cleanup exception')
            if self.mode == 'return':
                return AutoApprovalDecision(AutoApprovalVerdict.DENY)
            if self.mode in {'delayed', 'second_raise', 'second_return'}:
                try:
                    await workflow.wait_condition(lambda: self.cleanup_release)
                except asyncio.CancelledError:
                    self.second_cancel = True
                    if self.mode == 'second_return':
                        return AutoApprovalDecision(AutoApprovalVerdict.DENY)
                    raise
            raise

    @agent.accepts
    async def act(self, message: TextMessage) -> TextReply:
        """Run one gated probe with controlled evaluator cleanup."""
        self.mode = message.text
        self.caller = asyncio.current_task()
        try:
            await self._runner.run_tool('call', cleanup_probe)
        except ToolApprovalDenied:
            self.outcome = 'rejected'
        except asyncio.CancelledError:
            self.outcome = 'cancelled'
        else:
            self.outcome = 'dispatched'
        self.done = True
        return TextReply(text=self.outcome)

    @workflow.signal
    def release_cleanup(self):
        self.cleanup_release = True

    @workflow.signal
    def cancel_caller(self):
        # Standard SDK-supported asyncio task cancellation, not a private handler.
        # The caller is still waiting inside run_tool when this signal arrives.
        self.caller_cancel_requested = True
        self.caller.cancel()

    @workflow.signal
    def checkpoint(self):
        """Schedule a workflow task after worker replacement without changing state."""
        pass

    @workflow.query
    def evidence(self):
        entry = self._runner._status.approval_entry('call')
        return {'status': entry.status.value if entry else None, 'closed': self._runner._closed,
                'started': self.started, 'cleanup_entered': self.cleanup_entered,
                'second_cancel': self.second_cancel, 'caller_cancel_requested': self.caller_cancel_requested,
                'outcome': self.outcome, 'done': self.done, 'events': self._runner.events}


@pytest_asyncio.fixture
async def environment():
    env = await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter)
    queue = 'cleanup-'+uuid.uuid4().hex
    try:
        yield env.client, queue
    finally:
        await env.shutdown()


def worker(client, queue):
    return Worker(client, task_queue=queue, workflows=[CleanupAgent],
                  workflow_runner=UnsandboxedWorkflowRunner())


async def until(handle, predicate):
    async with asyncio.timeout(30):
        while True:
            value = await handle.query(CleanupAgent.evidence)
            if predicate(value):
                return value
            await asyncio.sleep(0.02)


async def start(client, queue, mode):
    handle = await client.start_workflow(CleanupAgent.run, AgentConfig(),
                                        id='cleanup-'+uuid.uuid4().hex, task_queue=queue)
    await handle.execute_update('send_agent_message', AgentMessage(type='act', payload={'text': mode}))
    await until(handle, lambda e: e['started'])
    return handle


async def settle(handle, decision):
    if decision == 'close':
        await handle.signal('close')
    else:
        await handle.execute_update('tool_approval', ToolApprovalDecision(tool_id='call', approved=decision=='approve'))


def retain(name, evidence):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    evidence = dict(evidence)
    evidence.update(variant=VARIANT, source_sha256=hashlib.sha256(
        Path('temporal_agent_harness/harness/agent_workflow.py').read_bytes()).hexdigest())
    (OUTPUT/(name+'.json')).write_text(json.dumps(evidence,indent=2)+'\n')


async def finish_and_replay(handle, name):
    await handle.result()
    history = await handle.fetch_history()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT/(name+'.history.json')).write_text(history.to_json())
    result = await Replayer(workflows=[CleanupAgent], workflow_runner=UnsandboxedWorkflowRunner(),
                            data_converter=pydantic_data_converter).replay_workflow(history)
    retain(name+'-replay', {'workflow_id': handle.id, 'replay_failure': str(result.replay_failure) if result.replay_failure else None,
                          'history_events': len(history.events)})
    assert result.replay_failure is None


@pytest.mark.parametrize('mode', ['propagate','raise','return'])
@pytest.mark.parametrize('decision', ['approve','deny','close'])
async def test_cleanup_preserves_settlement(environment, mode, decision):
    client, queue = environment
    async with worker(client,queue):
        handle = await start(client,queue,mode)
        await settle(handle,decision)
        evidence = await until(handle,lambda e:e['done'])
        name = decision+'-'+mode
        retain(name,evidence)
        assert evidence['outcome'] == ('dispatched' if decision=='approve' else 'rejected')
        assert evidence['status'] == ('approved' if decision=='approve' else 'denied')
        terminals = [e for e in evidence['events'] if e['type']=='auto_approval_evaluation_superseded']
        assert len(terminals)==1
        if decision!='close':
            await handle.signal('close')
        await finish_and_replay(handle,name)


@pytest.mark.parametrize('decision',['approve','deny','close'])
async def test_close_waits_for_cleanup_barrier(environment,decision):
    client,queue=environment
    async with worker(client,queue):
        handle=await start(client,queue,'delayed')
        await settle(handle,decision)
        before=await until(handle,lambda e:e['cleanup_entered'])
        await handle.signal('close')
        closed=await until(handle,lambda e:e['closed'])
        retain('blocked-'+decision,{'before':before,'closed':closed})
        assert not closed['done']
        assert not any(e['type']=='tool_start' for e in closed['events'])
        assert (await handle.describe()).status == WorkflowExecutionStatus.RUNNING
        await handle.signal(CleanupAgent.release_cleanup)
        after=await until(handle,lambda e:e['done'])
        retain('released-'+decision,after)
        assert after['outcome']==('dispatched' if decision=='approve' else 'rejected')
        await finish_and_replay(handle,'delayed-'+decision)


@pytest.mark.parametrize('mode',['second_raise','second_return'])
async def test_caller_cancellation_during_cleanup(environment,mode):
    client,queue=environment
    async with worker(client,queue):
        handle=await start(client,queue,mode)
        await settle(handle,'approve')
        before=await until(handle,lambda e:e['cleanup_entered'])
        await handle.signal(CleanupAgent.cancel_caller)
        after=await until(handle,lambda e:e['done'])
        retain('caller-'+mode,{'before':before,'after':after})
        assert after['caller_cancel_requested'] and after['second_cancel']
        assert after['status']=='approved'
        assert after['outcome']==('cancelled' if VARIANT=='corrected' else 'dispatched')
        assert any(e['type']=='tool_start' for e in after['events']) is (VARIANT=='baseline')
        await handle.signal('close')
        await finish_and_replay(handle,'caller-'+mode)


async def test_worker_restart_during_cleanup(environment):
    client,queue=environment
    async with worker(client,queue):
        handle=await start(client,queue,'delayed')
        await settle(handle,'approve')
        before=await until(handle,lambda e:e['cleanup_entered'])
        retain('restart-before',before)
    # A new Worker has a fresh workflow cache and must reconstruct the waiting state.
    async with worker(client,queue):
        # A query alone can target the retired worker's sticky queue. An explicit
        # no-state-change signal schedules a workflow task and permits fallback.
        await handle.signal(CleanupAgent.checkpoint)
        recovered=await until(handle,lambda e:e['cleanup_entered'])
        retain('restart-recovered',recovered)
        assert recovered==before
        await handle.signal(CleanupAgent.release_cleanup)
        after=await until(handle,lambda e:e['done'])
        retain('restart-after',after)
        assert after['outcome']=='dispatched'
        await handle.signal('close')
        await finish_and_replay(handle,'restart')


async def test_workflow_cancellation_is_separate(environment):
    client,queue=environment
    async with worker(client,queue):
        handle=await start(client,queue,'delayed')
        await settle(handle,'approve')
        before=await until(handle,lambda e:e['cleanup_entered'])
        await handle.cancel()
        from temporalio.client import WorkflowFailureError
        with pytest.raises(WorkflowFailureError):
            async with asyncio.timeout(30):
                await handle.result()
        description=await handle.describe()
        retain('workflow-cancel',{'before':before,'terminal_status':description.status.name})
        assert description.status==WorkflowExecutionStatus.CANCELED
        history=await handle.fetch_history()
        OUTPUT.mkdir(parents=True,exist_ok=True)
        (OUTPUT/'workflow-cancel.history.json').write_text(history.to_json())
        result=await Replayer(workflows=[CleanupAgent],workflow_runner=UnsandboxedWorkflowRunner(),
                              data_converter=pydantic_data_converter).replay_workflow(history)
        retain('workflow-cancel-replay',{'replay_failure':str(result.replay_failure) if result.replay_failure else None,
                                       'history_events':len(history.events)})
        assert result.replay_failure is None
