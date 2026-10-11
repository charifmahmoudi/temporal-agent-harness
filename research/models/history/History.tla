---------------------------- MODULE History ----------------------------
EXTENDS Naturals
CONSTANT DuplicateReplayEffect
Variants == {"baseline", "corrected", "versioned"}

\* Boundary abstraction of the isolated patches, not the Temporal SDK protocol.
FreshStop(v, cancelled) == cancelled /\ v # "baseline"
FreshCommand(v, approved, cancelled) == approved /\ ~FreshStop(v, cancelled)
FreshMarker(v, cancelled) == v = "versioned" /\ cancelled
\* V takes the old branch when replay reaches this point without its marker.
ReplayStop(v, cancelled, oldMarker) ==
  cancelled /\ (v = "corrected" \/ (v = "versioned" /\ oldMarker))
ReplayCommand(v, approved, cancelled, oldMarker) ==
  approved /\ ~ReplayStop(v, cancelled, oldMarker)
\* A non-deprecated recorded patch must be handled by version-aware code.
MarkerAccepted(v, oldMarker) == ~oldMarker \/ v = "versioned"

VARIABLES producer, target, approved, cancelled, pc, permitted,
          command, marker, effect, replayCommand, replayMarkerOK, compatible
vars == <<producer,target,approved,cancelled,pc,permitted,command,marker,
          effect,replayCommand,replayMarkerOK,compatible>>
Init == /\ producer \in Variants /\ target \in Variants
        /\ approved \in BOOLEAN /\ cancelled \in BOOLEAN
        /\ (cancelled => approved)
        /\ pc = "gate" /\ permitted = FALSE
        /\ command = FALSE /\ marker = FALSE /\ effect = 0
        /\ replayCommand = FALSE /\ replayMarkerOK = FALSE /\ compatible = FALSE
Gate == /\ pc = "gate"
        /\ permitted' = FreshCommand(producer,approved,cancelled)
        /\ pc' = "record"
        /\ UNCHANGED <<producer,target,approved,cancelled,command,marker,effect,
                       replayCommand,replayMarkerOK,compatible>>
Record == /\ pc = "record"
          /\ command' = permitted
          /\ marker' = FreshMarker(producer,cancelled)
          /\ pc' = "effect"
          /\ UNCHANGED <<producer,target,approved,cancelled,permitted,effect,
                         replayCommand,replayMarkerOK,compatible>>
\* One successful activity attempt in the retained probe; no retries/crashes.
Effect == /\ pc = "effect" /\ effect' = IF command THEN 1 ELSE 0
          /\ pc' = "replay"
          /\ UNCHANGED <<producer,target,approved,cancelled,permitted,command,marker,
                         replayCommand,replayMarkerOK,compatible>>
PlanReplay == /\ pc = "replay"
              /\ replayCommand' = ReplayCommand(target,approved,cancelled,marker)
              /\ replayMarkerOK' = MarkerAccepted(target,marker)
              /\ pc' = "compare"
              /\ UNCHANGED <<producer,target,approved,cancelled,permitted,command,
                             marker,effect,compatible>>
Compare == /\ pc = "compare"
           /\ compatible' = (replayCommand = command /\ replayMarkerOK)
           /\ effect' = IF DuplicateReplayEffect /\ replayCommand /\ compatible'
                        THEN effect + 1 ELSE effect
           /\ pc' = "done"
           /\ UNCHANGED <<producer,target,approved,cancelled,permitted,command,marker,
                          replayCommand,replayMarkerOK>>
Next == Gate \/ Record \/ Effect \/ PlanReplay \/ Compare
Spec == Init /\ [][Next]_vars
TypeOK == /\ producer \in Variants /\ target \in Variants
          /\ approved \in BOOLEAN /\ cancelled \in BOOLEAN
          /\ pc \in {"gate","record","effect","replay","compare","done"}
          /\ permitted \in BOOLEAN /\ command \in BOOLEAN /\ marker \in BOOLEAN
          /\ effect \in 0..2 /\ replayCommand \in BOOLEAN
          /\ replayMarkerOK \in BOOLEAN /\ compatible \in BOOLEAN
AuthorizedCommand == command => approved
NoReplayEffect == pc = "done" => effect = (IF command THEN 1 ELSE 0)
BaselineFreshCancellation ==
  (pc = "done" /\ producer = "baseline" /\ cancelled) => ~command
DirectFreshCancellation ==
  (pc = "done" /\ producer = "corrected" /\ cancelled) => ~command
VersionedFreshCancellation ==
  (pc = "done" /\ producer = "versioned" /\ cancelled) => ~command
DirectPreservesBaseline ==
  (pc = "done" /\ producer = "baseline" /\ target = "corrected") => compatible
VersionedPreservesBaseline ==
  (pc = "done" /\ producer = "baseline" /\ target = "versioned") => compatible
VersionedPreservesUnmarkedCorrection ==
  (pc = "done" /\ producer = "corrected" /\ target = "versioned") => compatible
=============================================================================
