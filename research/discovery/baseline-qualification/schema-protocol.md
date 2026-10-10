# Metric-schema follow-up protocol

Published after qualification run 38066672086, before the following experiment.

The CLI returned DER=0 and MER=0 while the dedicated reproduction script and
independent paired-verdict aggregation returned 1,444 duplicate and 284 missing
trials. Inspecting a duplicate CRM row shows its nested oracle verdict contains
boolean properties but no duplicate_effects_count or missing_effects_count.
The CLI legacy reader passes that object through; its aggregation defaults the
absent count fields to zero. The pair-level verdict retains the counts.

Prediction: in a temporary copy, adding only the two count fields to the nested
fault oracle, copied from each pair's existing verdict, will restore CLI counts
to 1,444/2,880 and 284/2,880 without changing 2,406 controls, 1,124 recoveries,
CRSR or EOR. Original data and upstream source remain unchanged.

Run the official evaluator on original and transformed data in GitHub CI. Report
all absent-key counts and reject conflicting existing keys rather than overwrite
them. The adapter must reject a contradictory count and a missing source count.
A matching result localizes a schema-adaptation defect in this pinned entry point;
it neither invalidates the paper's main result nor certifies the semantic oracles.
Retain exact input hash, summaries, sample pair IDs and rejection outcomes.
