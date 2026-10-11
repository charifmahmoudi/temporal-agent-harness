"""Boundary experiments on real methods; scheduling shim is NOT a Temporal emulator."""
import asyncio
from types import SimpleNamespace
import uuid

import pytest
from temporalio.exceptions import ApplicationError

from temporal_agent_harness.harness import agent_workflow as impl
from temporal_agent_harness.harness.agent import AutoApprovalDecision, AutoApprovalVerdict, ToolApprovalPolicy
from temporal_agent_harness.harness.agent_protocol import ToolApprovalDecision


def runner(monkeypatch):
    monkeypatch.setattr(impl.workflow, "uuid4", uuid.uuid4)
    r = object.__new__(impl.AgentWorkflowRunner)
    r._status = impl._WorkflowStatus(agent_id="probe", approval_policy=ToolApprovalPolicy.always_require_human_approval())
    r._closed = False
    r._pub = lambda *args, **kwargs: None
    r._status.register_pending_approval("call", "probe", {}, 1, "turn", None, inherently_safe=False)
    return r


@pytest.mark.parametrize("approved", [True, False])
async def test_accepted_human_decision_survives_close_and_duplicate(monkeypatch, approved):
    r = runner(monkeypatch)
    decision = ToolApprovalDecision(tool_id="call", approved=approved)
    r._validate_tool_approval(decision)
    await r._handle_tool_approval(decision)
    r._handle_close()
    outcome = r._status.finalize_approval("call", closed=r._closed)
    assert outcome.approved is approved
    with pytest.raises(ApplicationError, match="already"):
        r._validate_tool_approval(ToolApprovalDecision(tool_id="call", approved=not approved))


def test_close_finalizes_unresolved_entry_as_denied(monkeypatch):
    r = runner(monkeypatch)
    r._handle_close()
    assert not r._status.finalize_approval("call", closed=r._closed).approved


@pytest.mark.parametrize("verdict", list(AutoApprovalVerdict))
@pytest.mark.parametrize("competitor", ["approve", "deny", "close", None])
async def test_completed_evaluator_and_competing_resolution(monkeypatch, verdict, competitor):
    r = runner(monkeypatch)
    completed = asyncio.Event()

    async def evaluator(ctx):
        completed.set()
        return AutoApprovalDecision(verdict)

    async def controlled_wait(predicate):
        # Force the evaluator to finish before the runner resumes; optionally resolve
        # the gate in the same interval. This tests its settled-first branch.
        await completed.wait()
        await asyncio.sleep(0)
        if competitor == "close":
            r._handle_close()
        elif competitor:
            decision = ToolApprovalDecision(tool_id="call", approved=competitor == "approve")
            r._validate_tool_approval(decision)
            await r._handle_tool_approval(decision)
        assert predicate()

    r._auto_mode_evaluator = evaluator
    monkeypatch.setattr(impl.workflow, "wait_condition", controlled_wait)
    result = await r._run_auto_mode_evaluator(
        SimpleNamespace(tool_name="probe"), tool_id="call",
        stream=SimpleNamespace(turn_id="turn", turn_number=1),
    )
    if competitor:
        assert result is None
        outcome = r._status.finalize_approval("call", closed=r._closed)
        assert outcome.approved is (competitor == "approve")
    else:
        assert result.verdict is verdict
        assert not r._status.is_approval_resolved("call")
