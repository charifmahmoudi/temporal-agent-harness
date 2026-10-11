---------------------------- MODULE Cascade ----------------------------
EXTENDS Approval, Sequences
CONSTANTS a, b, ToolOf, CallOrder, LeakScope, OverwriteSettled, ReverseCause
VARIABLES allowed, history, causes, scopeViolation
cascadeVars == <<vars, allowed, history, causes, scopeViolation>>
OrderedCalls == <<a, b>>
ReversedCalls == <<b, a>>
SameTool == [c \in Calls |-> "shared"]
DifferentTools == [c \in Calls |-> IF c = a THEN "shared" ELSE "other"]
Tools == {ToolOf[c] : c \in Calls}
CascadeInit == Init /\ allowed = {} /\ history = <<>>
               /\ causes = {} /\ scopeViolation = FALSE

\* Capture resolutions from the original single-gate actions without reimplementing
\* their evaluator, cancellation, close, or dispatch semantics.
BaseStep == /\ Next
            /\ history' = history \o SelectSeq(CallOrder,
                 LAMBDA c : status[c] = "pending" /\ status'[c] # "pending")
            /\ UNCHANGED <<allowed, causes, scopeViolation>>

\* Targets are pending eligible calls. Fault switches intentionally corrupt scope
\* or preservation of settled decisions; all normal configurations disable them.
Targets(policy) == {c \in Calls :
  (status[c] = "pending" \/ (OverwriteSettled /\ resolutions[c] = 1))
  /\ (ToolOf[c] \in policy \/ LeakScope)}
Remember(c) ==
  /\ status[c] = "pending"
  /\ LET policy == allowed \cup {ToolOf[c]}
         siblings == Targets(policy) \ {c}
         changed == siblings \cup {c}
         siblingOrder == SelectSeq(CallOrder, LAMBDA s : s \in siblings)
     IN /\ allowed' = policy
        /\ status' = [s \in Calls |-> IF s \in changed THEN "approved" ELSE status[s]]
        /\ first' = [s \in Calls |-> IF s \in changed /\ first[s] = "none"
                                   THEN "approved" ELSE first[s]]
        /\ resolutions' = [s \in Calls |-> IF s \in changed THEN resolutions[s] + 1 ELSE resolutions[s]]
        /\ history' = history \o (IF ReverseCause THEN siblingOrder \o <<c>> ELSE <<c>> \o siblingOrder)
        /\ causes' = causes \cup {<<c, s>> : s \in siblings}
        /\ scopeViolation' = (scopeViolation \/ (\E s \in siblings : ToolOf[s] \notin policy))
  /\ UNCHANGED <<evaluator, verdict, phase, closed>>

\* Policy replacement and synchronous cascade are one atomic action. Restriction
\* changes future eligibility but never revokes previously accepted outcomes.
Update(policy) ==
  /\ policy \subseteq Tools
  /\ LET changed == Targets(policy)
     IN /\ allowed' = policy
        /\ status' = [s \in Calls |-> IF s \in changed THEN "approved" ELSE status[s]]
        /\ first' = [s \in Calls |-> IF s \in changed /\ first[s] = "none"
                                   THEN "approved" ELSE first[s]]
        /\ resolutions' = [s \in Calls |-> IF s \in changed THEN resolutions[s] + 1 ELSE resolutions[s]]
        /\ history' = history \o SelectSeq(CallOrder, LAMBDA s : s \in changed)
        /\ scopeViolation' = (scopeViolation \/ (\E s \in changed : ToolOf[s] \notin policy))
  /\ UNCHANGED <<evaluator, verdict, phase, closed, causes>>
CascadeNext == BaseStep \/ (\E c \in Calls : Remember(c)) \/ (\E policy \in SUBSET Tools : Update(policy))
CascadeSpec == CascadeInit /\ [][CascadeNext]_cascadeVars
CascadeFairSpec == CascadeSpec /\ \A c \in Calls :
  WF_cascadeVars(BaseStep /\ Consume(c))
  /\ WF_cascadeVars(BaseStep /\ Cancelled(c))
  /\ WF_cascadeVars(BaseStep /\ Finalize(c))
CascadeTypeOK == TypeOK /\ allowed \subseteq Tools /\ history \in Seq(Calls)
                 /\ causes \subseteq (Calls \X Calls) /\ scopeViolation \in BOOLEAN
ScopePreserved == ~scopeViolation
CauseBeforeCascade == \A pair \in causes :
  \E i, j \in 1..Len(history) : i < j /\ history[i] = pair[1] /\ history[j] = pair[2]
=============================================================================
