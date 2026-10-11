---------------------------- MODULE Approval ----------------------------
EXTENDS Naturals, FiniteSets
CONSTANTS Calls, AllowOverwrite, BypassGate
VARIABLES status, evaluator, verdict, phase, closed, first, resolutions
vars == <<status, evaluator, verdict, phase, closed, first, resolutions>>
Verdicts == {"approve", "deny", "escalate", "error"}
Init == /\ status = [c \in Calls |-> "pending"]
        /\ evaluator = [c \in Calls |-> "running"]
        /\ verdict = [c \in Calls |-> "none"]
        /\ phase = [c \in Calls |-> "evaluating"]
        /\ closed = FALSE
        /\ first = [c \in Calls |-> "none"]
        /\ resolutions = [c \in Calls |-> 0]

Human(c, d) ==
  /\ status[c] = "pending" \/ (AllowOverwrite /\ resolutions[c] = 1)
  /\ status' = [status EXCEPT ![c] = d]
  /\ first' = IF first[c] = "none" THEN [first EXCEPT ![c] = d] ELSE first
  /\ resolutions' = [resolutions EXCEPT ![c] = @ + 1]
  /\ UNCHANGED <<evaluator, verdict, phase, closed>>

Complete(c, v) ==
  /\ evaluator[c] = "running"
  /\ evaluator' = [evaluator EXCEPT ![c] = "done"]
  /\ verdict' = [verdict EXCEPT ![c] = v]
  /\ UNCHANGED <<status, phase, closed, first, resolutions>>

\* No normal-path await occurs between checking settlement and applying a verdict.
\* Superseded cancellation has an explicit unwinding phase; termination is fairness.
Consume(c) ==
  /\ phase[c] = "evaluating"
  /\ evaluator[c] = "done" \/ status[c] # "pending" \/ closed
  /\ LET superseded == status[c] # "pending" \/ closed
         decides == ~superseded /\ verdict[c] \in {"approve", "deny"}
         d == IF verdict[c] = "approve" THEN "approved" ELSE "denied"
     IN /\ status' = IF decides THEN [status EXCEPT ![c] = d] ELSE status
        /\ first' = IF decides THEN [first EXCEPT ![c] = d] ELSE first
        /\ resolutions' = IF decides THEN [resolutions EXCEPT ![c] = @ + 1] ELSE resolutions
        /\ evaluator' = [evaluator EXCEPT ![c] = IF superseded THEN "cancelling" ELSE "consumed"]
        /\ phase' = [phase EXCEPT ![c] = IF superseded THEN "cancelling" ELSE "gate"]
  /\ UNCHANGED <<verdict, closed>>

Cancelled(c) == /\ phase[c] = "cancelling"
                /\ phase' = [phase EXCEPT ![c] = "gate"]
                /\ evaluator' = [evaluator EXCEPT ![c] = "stopped"]
                /\ UNCHANGED <<status, verdict, closed, first, resolutions>>

Finalize(c) ==
  /\ phase[c] = "gate"
  /\ status[c] # "pending" \/ closed
  /\ LET deny == status[c] = "pending"
     IN /\ status' = IF deny THEN [status EXCEPT ![c] = "denied"] ELSE status
        /\ first' = IF deny THEN [first EXCEPT ![c] = "denied"] ELSE first
        /\ resolutions' = IF deny THEN [resolutions EXCEPT ![c] = @ + 1] ELSE resolutions
        /\ phase' = [phase EXCEPT ![c] = IF ~deny /\ status[c] = "approved"
                                         THEN "dispatched" ELSE "rejected"]
  /\ UNCHANGED <<evaluator, verdict, closed>>

Bypass(c) == /\ BypassGate /\ phase[c] = "gate" /\ status[c] = "pending"
             /\ phase' = [phase EXCEPT ![c] = "dispatched"]
             /\ UNCHANGED <<status, evaluator, verdict, closed, first, resolutions>>
Close == /\ ~closed /\ closed' = TRUE
         /\ UNCHANGED <<status, evaluator, verdict, phase, first, resolutions>>
Next == Close \/ \E c \in Calls :
          (\E d \in {"approved", "denied"} : Human(c, d))
          \/ (\E v \in Verdicts : Complete(c, v))
          \/ Consume(c) \/ Cancelled(c) \/ Finalize(c) \/ Bypass(c)
Spec == Init /\ [][Next]_vars
FairSpec == Spec /\ \A c \in Calls : WF_vars(Consume(c)) /\ WF_vars(Cancelled(c)) /\ WF_vars(Finalize(c))
TypeOK == /\ status \in [Calls -> {"pending", "approved", "denied"}]
          /\ evaluator \in [Calls -> {"running", "done", "cancelling", "stopped", "consumed"}]
          /\ verdict \in [Calls -> Verdicts \cup {"none"}]
          /\ phase \in [Calls -> {"evaluating", "cancelling", "gate", "dispatched", "rejected"}]
          /\ closed \in BOOLEAN
          /\ first \in [Calls -> {"none", "approved", "denied"}]
          /\ resolutions \in [Calls -> 0..2]
DecisionStable == \A c \in Calls : first[c] # "none" => status[c] = first[c]
SingleResolution == \A c \in Calls : resolutions[c] <= 1
AuthorizedDispatch == \A c \in Calls : phase[c] = "dispatched" => status[c] = "approved"
DeniedNeverDispatches == \A c \in Calls : status[c] = "denied" => phase[c] # "dispatched"
ResolutionProgress == \A c \in Calls :
  (status[c] # "pending" \/ closed) ~> (phase[c] \in {"dispatched", "rejected"})
=============================================================================
