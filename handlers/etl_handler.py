import random
import string
from datetime import datetime


def _fake_id(prefix="pipe"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "etl.create_pipeline": _create_pipeline,
        "etl.delete_pipeline": _delete_pipeline,
        "etl.run": _run,
        "etl.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No etl handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_pipeline(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create ETL pipeline '{name}'", "would_call": "POST /glue/v1/pipelines"}
    return {"status": "success", "message": f"ETL pipeline completed", "name":name,"pipeline_id":_fake_id("pipe"), "at": datetime.utcnow().isoformat() + "Z"}

def _delete_pipeline(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete ETL pipeline '{name}'", "would_call": "DELETE /glue/v1/pipelines"}
    return {"status": "success", "message": f"ETL pipeline completed", "at": datetime.utcnow().isoformat() + "Z"}

def _run(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would run ETL pipeline '{name}'", "would_call": "POST /glue/v1/pipelines"}
    return {"status": "success", "message": f"ETL pipeline completed", "run_id":_fake_id("run"),"status":"RUNNING", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for ETL pipeline '{name}'", "would_call": "GET /glue/v1/pipelines"}
    return {"status": "success", "message": f"ETL pipeline completed", "state":"READY","last_run_status":"SUCCEEDED","last_run_duration_s":random.randint(60,7200), "at": datetime.utcnow().isoformat() + "Z"}
