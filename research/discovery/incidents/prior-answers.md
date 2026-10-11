# Nearest prior answers and limits

This is a focused overlap check for the selected operator decisions, not an exhaustive
systematic literature review or proof that no relevant work exists.

| Question | Primary prior source | Consequence for our claim |
| --- | --- | --- |
| Can duplicate requests safely repeat effects? | [RIFL, SOSP 2015 abstract and proceedings](https://sigops.org/s/conferences/sosp/2015/current/abstracts.html) | Exactly-once RPC infrastructure and preservation of its metadata already exist; generic retry deduplication is not a contribution here |
| Can recovery be specified separately from ordinary execution? | [FSCQ / Crash Hoare Logic, SOSP 2015](https://sigops.org/s/conferences/sosp/2015/current/abstracts.html) | Crash conditions and recovery procedures already have formal treatment; writing a recovery contract is insufficient novelty |
| Are workflow-level and step-level stream effects equivalent? | [DBOS Python communication contract](https://docs.dbos.dev/python/tutorials/workflow-communication) | Documented different retry semantics answer #770; current docs cannot establish historical docs quality |
| How should old workflows survive code replacement? | [DBOS upgrade guidance](https://docs.dbos.dev/python/tutorials/upgrading-workflows) | Version draining and patching answer #702's immediate operator question |
| Can a savepoint be assumed to participate in the outer SQLite transaction? | [SQLAlchemy SQLite transaction documentation](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html) | Driver transaction mode is an established confounder for a proposed repair; our probe does not implement that repair |
| Is the #880 SQLite failure/branch consequence newly observed here? | [Report and measured follow-up](https://github.com/dbos-inc/dbos-transact-py/issues/880#issuecomment-6023237623) | No. The same-name/different-name contrast and the committed schedule effect already appear upstream |
| Have healed-network failures already been sought systematically? | [Restate Jepsen report](https://github.com/restatedev/restate/issues/2655) | Yes. Recovery fault injection and post-healing observations are established baselines in the very cases reviewed |

The broader [CIDR workflow consistency paper](https://vldb.org/cidrdb/papers/2026/p9-stonebraker.pdf)
is relevant literature, but this round does not claim a new theorem relative to it or
infer coverage of the particular #880 API defect from its abstract. The immediate
technical explanation comes from the issue discussion and inspected source.

The backend probe can distinguish a SQLite-only explanation from shared success-only
checkpoint behavior. The latter is favored before testing. It is a narrow empirical
scope question, not a competition between new scientific theories. If confirmed, the
result belongs in a reproducible community note with upstream attribution. An eventual
method contribution would need a new capability/guarantee; an empirical contribution
would need substantive generalizable knowledge and a defensible sampling/evaluation
argument. Neither follows from eight controlled cells.
