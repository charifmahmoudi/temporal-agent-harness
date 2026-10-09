------------------------------ MODULE Cleanup ------------------------------
EXTENDS Approval
CONSTANTS CleanupCanFinish, SwallowCallerCancel
VARIABLES callerCancelled, outcome
cleanupVars == <<vars, callerCancelled, outcome>>

\* One registered call. Caller cancellation is distinct from Close, which only
\* marks session closure. A cancelled invocation may retain approved status.
CleanupInit == Init /\ callerCancelled = FALSE /\ outcome = "none"
Environment == (Close \/ \E c \in Calls :
                  (\E d \in {"approved", "denied"} : Human(c,d))
                  \/ (\E v \in Verdicts : Complete(c,v)))
               /\ UNCHANGED <<callerCancelled,outcome>>
ConsumeStep == (\E c \in Calls : Consume(c))
               /\ UNCHANGED <<callerCancelled,outcome>>
FinishCleanup == CleanupCanFinish /\ (\E c \in Calls : Cancelled(c))
                 /\ UNCHANGED <<callerCancelled,outcome>>
\* This action abstracts cancellation arriving while cleanup is awaited and
\* the child's response ending that wait (by raising or returning). It does
\* not model an evaluator that indefinitely suppresses the second request.
CancelCaller ==
  /\ ~callerCancelled
  /\ \E c \in Calls :
      /\ phase[c] = "cancelling"
      /\ phase' = [phase EXCEPT ![c] = IF SwallowCallerCancel THEN "gate" ELSE "aborted"]
      /\ evaluator' = [evaluator EXCEPT ![c] = "stopped"]
  /\ callerCancelled' = TRUE
  /\ outcome' = IF SwallowCallerCancel THEN "none" ELSE "cancelled"
  /\ UNCHANGED <<status,verdict,closed,first,resolutions>>
FinalizeStep ==
  /\ \E c \in Calls : Finalize(c)
  /\ outcome' = IF \E c \in Calls : phase'[c] = "dispatched" THEN "dispatched" ELSE "rejected"
  /\ UNCHANGED callerCancelled
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
CallerCancellationRespected == callerCancelled => outcome # "dispatched"
CleanupProgress == ((\E c \in Calls : status[c] # "pending") \/ closed) ~> (outcome # "none")
=============================================================================
