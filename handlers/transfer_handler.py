import random
import string
from datetime import datetime


def _fake_id(prefix="dms"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "transfer.create_job": _create_job,
        "transfer.delete_job": _delete_job,
        "transfer.start": _start,
        "transfer.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No transfer handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_job(params, dry_run):
    name=params.get("name",_fake_id())
    source=params.get("source","")
    target=params.get("target","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create transfer job '{name}' ({source} → {target})", "would_call": "POST /dms/v1/tasks"}
    return {"status": "success", "message": f"transfer job completed", "name":name,"task_arn":f"arn:aws:dms:us-east-1:123456:task:{_fake_id("t")}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_job(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete transfer job '{name}'", "would_call": "DELETE /dms/v1/tasks"}
    return {"status": "success", "message": f"transfer job completed", "at": datetime.utcnow().isoformat() + "Z"}

def _start(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would start transfer job '{name}'", "would_call": "POST /dms/v1/tasks"}
    return {"status": "success", "message": f"transfer job completed", "name":name,"status":"running", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for transfer job '{name}'", "would_call": "GET /dms/v1/tasks"}
    return {"status": "success", "message": f"transfer job completed", "status":"running","tables_loaded":random.randint(1,100),"rows_transferred":random.randint(1000,10000000),"replication_lag_s":round(random.uniform(0,10),1), "at": datetime.utcnow().isoformat() + "Z"}
