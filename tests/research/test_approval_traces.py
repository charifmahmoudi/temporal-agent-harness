"""Record real Temporal executions. Observers never introduce awaits in harness paths."""
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
async def harmless_probe() -> str:
    return "executed"


class ObservedRunner(AgentWorkflowRunner):
    def observe(self, label, action=None, **projection):
        entry = self._status.approval_entry("call")
        if entry is not None:
            self.observations.append({"label": label, "action": action, "state": {
                "status": entry.status.value, "closed": self._closed, **projection}})

    def _pub(self, *args, **kwargs):
        super()._pub(*args, **kwargs)
        event = args[2]
        self.raw_events.append(event.model_dump(mode="json"))
        if event.type == "auto_approval_evaluation_started":
            self.observe("evaluation_started", evaluator="running", phase="evaluating")
        elif event.type == "tool_approval_resolved":
            decision = self.observed_human
            action = {'kind': 'human', 'approved': decision.approved} if decision else None
            self.observe("approval_resolved", action=action)
        elif event.type == "tool_start":
            self.observe("tool_start", phase="dispatched")

    async def _handle_tool_approval(self, decision: ToolApprovalDecision):
        # Resolution publication is synchronous in this non-remember experiment.
        # Attach the accepted input at that boundary, without another observation.
        self.observed_human = decision
        try:
            return await super()._handle_tool_approval(decision)
        finally:
            self.observed_human = None

    def _handle_close(self):
        super()._handle_close()
        self.observe("close", action={"kind": "close"})

    async def _run_auto_mode_evaluator(self, *args, **kwargs):
        result = await super()._run_auto_mode_evaluator(*args, **kwargs)
        # Observe actual return, not the earlier publication of an evaluation event.
        # Verdict application remains in the unmodified caller.
        self.observe("evaluator_runner_returned")
        return result


@agent.defn
class TraceAgent:
    @agent.init
    def __init__(self, config: AgentConfig):
        self.release = False
        self.cleanup_release = False
        self.cancel_seen = False
        self.done = False
        self.mode = "approve"
        self._runner = ObservedRunner(
            config, stream=WorkflowStream(), approval_policy_default=ToolApprovalPolicy.auto_mode(),
            auto_approval_criteria_default=AutoApprovalCriteria(
                sets={"probe": AutoApprovalCriteriaSet(effect="test", escalate_when=("test",))}, default="probe"),
            auto_mode_evaluator=self.evaluate)
        self._runner.observations = []
        self._runner.raw_events = []
        self._runner.observed_human = None

    async def evaluate(self, ctx):
        try:
            await workflow.wait_condition(lambda: self.release)
        except asyncio.CancelledError:
            self.cancel_seen = True
            self._runner.observe("cancellation_received", phase="cancelling", evaluator="cancelling")
            if self.mode == "delayed":
                await workflow.wait_condition(lambda: self.cleanup_release)
            raise
        verdict = AutoApprovalVerdict.DENY if self.mode == "deny" else AutoApprovalVerdict.APPROVE
        self._runner.observe("evaluator_completed", action={"kind": "complete", "verdict": verdict.value},
                             evaluator="done", verdict=verdict.value)
        return AutoApprovalDecision(verdict)

    @agent.accepts
    async def act(self, message: TextMessage) -> TextReply:
        """Execute the harmless probe under a controlled evaluator."""
        self.mode = message.text
        try:
            await self._runner.run_tool("call", harmless_probe)
            self._runner.observe("caller_finished", phase="dispatched")
        except ToolApprovalDenied:
            self._runner.observe("caller_rejected", phase="rejected")
        self.done = True
        return TextReply(text="finished")

    @workflow.signal
    def release_evaluator(self):
        self.release = True

    @workflow.signal
    def release_cleanup(self):
        self.cleanup_release = True

    @workflow.update
    async def release_and_approve(self):
        # Enable completion and accept a human decision within one non-suspending
        # handler. This controls readiness, not a claim about arbitrary tie-breaking.
        self.release = True
        decision = ToolApprovalDecision(tool_id="call", approved=True)
        self._runner._validate_tool_approval(decision)
        await self._runner._handle_tool_approval(decision)

    @workflow.query
    def evidence(self):
        return {"observations": self._runner.observations, "events": self._runner.raw_events,
                "done": self.done, "cancel_seen": self.cancel_seen}


@pytest_asyncio.fixture
async def temporal_probe():
    env = await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter)
    queue = f"trace-{uuid.uuid4()}"
    async with Worker(env.client, task_queue=queue, workflows=[TraceAgent],
                      workflow_runner=UnsandboxedWorkflowRunner()):
        try:
            yield env.client, queue
        finally:
            await env.shutdown()


async def until(handle, predicate):
    async with asyncio.timeout(30):
        while True:
            value = await handle.query(TraceAgent.evidence)
            if predicate(value):
                return value
            await asyncio.sleep(0.02)


@pytest.mark.parametrize("scenario", ["human_approve", "human_deny", "evaluator_approve",
    "evaluator_deny", "close", "delayed_cancel", "both_enabled"])
async def test_temporal_trace(temporal_probe, scenario):
    client, queue = temporal_probe
    h = await client.start_workflow(TraceAgent.run, AgentConfig(), id=f"trace-{uuid.uuid4()}", task_queue=queue)
    mode = "delayed" if scenario == "delayed_cancel" else "deny" if scenario == "evaluator_deny" else "approve"
    await h.execute_update("send_agent_message", AgentMessage(type="act", payload={"text": mode}))
    await until(h, lambda e: any(o["label"] == "evaluation_started" for o in e["observations"]))
    if scenario.startswith("evaluator"):
        await h.signal(TraceAgent.release_evaluator)
    elif scenario == "close":
        await h.signal("close")
    elif scenario == "both_enabled":
        await h.execute_update(TraceAgent.release_and_approve)
    else:
        await h.execute_update("tool_approval", ToolApprovalDecision(tool_id="call", approved=scenario != "human_deny"))
    if scenario == "delayed_cancel":
        before = await until(h, lambda e: e["cancel_seen"])
        assert not before["done"]
        assert not any(o["label"] == "tool_start" for o in before["observations"])
        await h.signal(TraceAgent.release_cleanup)
    evidence = await until(h, lambda e: e["done"])
    last = evidence["observations"][-1]["state"]
    denied = scenario in {"human_deny", "evaluator_deny", "close"}
    assert last["phase"] == ("rejected" if denied else "dispatched")
    assert last["status"] == ("denied" if denied else "approved")
    output = Path("research/results/traces")
    output.mkdir(parents=True, exist_ok=True)
    evidence.update(schema=2, scenario=scenario, workflow_id=h.id,
                    implementation_sha256=hashlib.sha256(Path("temporal_agent_harness/harness/agent_workflow.py").read_bytes()).hexdigest())
    (output / f"{scenario}.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if scenario != "close":
        await h.signal("close")
    await h.result()
