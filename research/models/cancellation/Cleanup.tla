------------------------------ MODULE Cleanup ------------------------------
EXTENDS Approval
CONSTANTS CleanupCanFinish, SwallowCallerCancel
VARIABLES callerCancelled, outcome, cleanupPending
cleanupVars == <<vars, callerCancelled, outcome, cleanupPending>>

\* One registered call. Caller cancellation is distinct from Close, which only
\* marks session closure. A cancelled invocation may retain approved status.
CleanupInit == Init /\ callerCancelled = FALSE /\ outcome = "none"
               /\ cleanupPending = FALSE
Environment == (Close \/ \E c \in Calls :
                  (\E d \in {"approved", "denied"} : Human(c,d))
                  \/ (\E v \in Verdicts : Complete(c,v)))
               /\ UNCHANGED <<callerCancelled,outcome,cleanupPending>>
\* Base Consume gives every superseded evaluator an abstract cancellation phase.
\* Remember whether its task was actually still running: awaiting a done task
\* cannot introduce an unbounded cleanup wait in the concrete helper.
ConsumeStep == (\E c \in Calls :
                 /\ Consume(c)
                 /\ cleanupPending' = (phase'[c] = "cancelling" /\ evaluator[c] = "running"))
               /\ UNCHANGED <<callerCancelled,outcome>>
FinishCleanup == (CleanupCanFinish \/ ~cleanupPending)
                 /\ (\E c \in Calls : Cancelled(c))
                 /\ cleanupPending' = FALSE
                 /\ UNCHANGED <<callerCancelled,outcome>>
\* This action abstracts cancellation arriving while cleanup is awaited and
\* the child's response ending that wait (by raising or returning). It does
\* not model an evaluator that indefinitely suppresses the second request.
CancelCaller ==
  /\ ~callerCancelled
  /\ cleanupPending
  /\ \E c \in Calls :
      /\ phase[c] = "cancelling"
      /\ phase' = [phase EXCEPT ![c] = IF SwallowCallerCancel THEN "gate" ELSE "aborted"]
      /\ evaluator' = [evaluator EXCEPT ![c] = "stopped"]
  /\ callerCancelled' = TRUE
  /\ outcome' = IF SwallowCallerCancel THEN "none" ELSE "cancelled"
  /\ cleanupPending' = FALSE
  /\ UNCHANGED <<status,verdict,closed,first,resolutions>>
FinalizeStep ==
  /\ \E c \in Calls : Finalize(c)
  /\ outcome' = IF \E c \in Calls : phase'[c] = "dispatched" THEN "dispatched" ELSE "rejected"
  /\ UNCHANGED <<callerCancelled,cleanupPending>>
CleanupNext == Environment \/ ConsumeStep \/ FinishCleanup \/ CancelCaller \/ FinalizeStep
CleanupSpec == CleanupInit /\ [][CleanupNext]_cleanupVars
CleanupFairSpec == CleanupSpec /\ WF_cleanupVars(ConsumeStep)
                                /\ WF_cleanupVars(FinishCleanup)
                                /\ WF_cleanupVars(FinalizeStep)
CleanupTypeOK ==
  /\ status \in [Calls -> {"pending","approved","denied"}]
  /\ evaluator \in [Calls -> {"running","done","cancelling","stopped","consumed"}]
  /\ verdict \in [Calls -> Verdicts \cup {"none"}]
  /\ phase \in [Calls -> {"evaluating","cancelling","gate","aborted","dispatched","rejected"}]
  /\ closed \in BOOLEAN
  /\ first \in [Calls -> {"none","approved","denied"}]
  /\ resolutions \in [Calls -> 0..1]
  /\ callerCancelled \in BOOLEAN
  /\ outcome \in {"none","dispatched","rejected","cancelled"}
  /\ cleanupPending \in BOOLEAN
CallerCancellationRespected == callerCancelled => outcome # "dispatched"
ReadyTaskNotBlocked ==
  (\E c \in Calls : phase[c] = "cancelling" /\ ~cleanupPending) => ENABLED FinishCleanup
PendingCleanupPhase == cleanupPending => (\E c \in Calls : phase[c] = "cancelling")
CleanupProgress == ((\E c \in Calls : status[c] # "pending") \/ closed) ~> (outcome # "none")
=============================================================================
