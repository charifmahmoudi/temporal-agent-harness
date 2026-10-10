"""CI-only, two-process exploration of DBOS #880; not a novelty benchmark."""
import dataclasses
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, default=str) + "\n")


def worker(phase, directory, suffix, mutation):
    from dbos import DBOS, DBOSClient, SetWorkflowID
    from dbos._error import DBOSException
    import sqlalchemy as sa
    from dbos._schemas.system_database import SystemSchema

    directory = Path(directory)
    url = os.environ["PROBE_DB_URL"]
    trace = directory / (phase + "-trace.jsonl")

    def emit(event, **fields):
        with trace.open("a") as f:
            f.write(json.dumps({"event": event, **fields}) + "\n")
            f.flush()
            os.fsync(f.fileno())

    @DBOS.workflow()
    def scheduled(at: datetime.datetime, context: object):
        emit("unexpected_schedule_fire")

    @DBOS.step()
    def mark(value: str):
        emit("marker_body", value=value)
        return value

    @DBOS.step()
    def mark_b(value: str):
        emit("marker_b_body", value=value)
        return value

    cron = (directory / "cron.txt").read_text()

    def create():
        DBOS.create_schedule(schedule_name="nightly", workflow_fn=scheduled, schedule=cron)

    @DBOS.workflow()
    def setup():
        try:
            create()
        except DBOSException as error:
            if "already exists" not in str(error):
                raise
            emit("branch", value="A", error=str(error))
            result = mark("A")
            if phase == "first":
                emit("crash_after_marker")
                os._exit(17)
            return result
        emit("branch", value="B")
        return mark("B") if suffix == "same" else mark_b("B")

    def snapshot(client):
        status = client.retrieve_workflow("W").get_status()
        # Raw rows retain checkpoint slot and serialized output/error, independently
        # of the convenience API's interpretation. Fresh DB contains synthetic data.
        with client._sys_db.engine.connect() as connection:
            rows = connection.execute(sa.select(SystemSchema.operation_outputs)).mappings().all()
        return {"status": dataclasses.asdict(status),
                "schedule": client.get_schedule("nightly"),
                "steps": client.list_workflow_steps("W"),
                "raw_operations": [dict(row) for row in rows]}

    if phase == "recover":
        client = DBOSClient(system_database_url=url)
        pre = snapshot(client)
        save(directory / "pre.json", pre)
        assert pre["status"]["status"] == "PENDING", pre
        assert any(s["function_name"].endswith("mark") for s in pre["steps"]), pre
        if mutation == "delete":
            client.delete_schedule("nightly")
        save(directory / "after-operator.json", {"schedule": client.get_schedule("nightly")})

    DBOS(config={"name": "incident-880", "system_database_url": url,
                 "application_version": "incident-880-v1", "executor_id": "local"})
    DBOS.launch()
    if phase == "first":
        create()
        with SetWorkflowID("W"):
            setup()
        raise AssertionError("declared crash not reached")

    end = time.monotonic() + 60
    while time.monotonic() < end:
        status = DBOS.get_workflow_status("W")
        if status and status.status in {"SUCCESS", "ERROR", "CANCELLED", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"}:
            break
        time.sleep(0.1)
    post = snapshot(client)
    post["bounded_timeout"] = post["status"]["status"] not in {"SUCCESS", "ERROR", "CANCELLED", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"}
    if not post["bounded_timeout"]:
        try:
            post["result"] = client.retrieve_workflow("W").get_result()
        except BaseException as error:
            post["exception"] = {"type": type(error).__name__, "message": str(error)}
    save(directory / "post.json", post)
    DBOS.destroy()


def main():
    if len(sys.argv) > 1:
        worker(*sys.argv[1:])
        return
    backend = os.environ["PROBE_BACKEND"]
    root = Path("research/results/incident-880") / backend
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for suffix in ("same", "different"):
        for mutation in ("retain", "delete"):
            directory = (root / f"{suffix}-{mutation}").resolve()
            directory.mkdir(parents=True, exist_ok=True)
            future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=12)
            (directory / "cron.txt").write_text(f"{future.minute} {future.hour} * * *")
            env = dict(os.environ)
            if backend == "sqlite":
                env["PROBE_DB_URL"] = "sqlite:///" + str(directory / "system.sqlite")
            else:
                import psycopg
                from psycopg import sql
                dbname = "probe_" + suffix + "_" + mutation
                with psycopg.connect(os.environ["PROBE_PG_ADMIN"], autocommit=True) as conn:
                    conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                env["PROBE_DB_URL"] = os.environ["PROBE_PG_BASE"] + "/" + dbname
            cell = {"backend": backend, "suffix": suffix, "mutation": mutation, "processes": {}}
            try:
                for phase in ("first", "recover"):
                    with (directory / (phase + ".log")).open("w") as log:
                        process = subprocess.run([sys.executable, __file__, phase, str(directory), suffix, mutation],
                                                 env=env, stdout=log, stderr=subprocess.STDOUT, timeout=100)
                    cell["processes"][phase] = process.returncode
                    assert process.returncode == (17 if phase == "first" else 0), cell
                cell["collection"] = "complete"
            except Exception as error:
                cell["collection"] = "inconclusive"
                cell["error"] = repr(error)
            results.append(cell)
            save(root / "collection.json", results)
    if any(x["collection"] != "complete" for x in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
