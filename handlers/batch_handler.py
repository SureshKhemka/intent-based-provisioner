import random
import string
from datetime import datetime


def _fake_id(prefix="job"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "batch.create_job": _create_job,
        "batch.delete_job": _delete_job,
        "batch.submit": _submit,
        "batch.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No batch handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_job(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create batch job definition '{name}'", "would_call": "POST /batch/v1/jobs"}
    return {"status": "success", "message": f"batch job completed", "name":name,"job_def_arn":f"arn:aws:batch:us-east-1:123456:job-definition/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_job(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete batch job definition '{name}'", "would_call": "DELETE /batch/v1/jobs"}
    return {"status": "success", "message": f"batch job completed", "at": datetime.utcnow().isoformat() + "Z"}

def _submit(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would submit batch job '{name}'", "would_call": "POST /batch/v1/jobs"}
    return {"status": "success", "message": f"batch job completed", "job_id":_fake_id("job"),"status":"SUBMITTED", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for batch job '{name}'", "would_call": "GET /batch/v1/jobs"}
    return {"status": "success", "message": f"batch job completed", "status":"SUCCEEDED","duration_s":random.randint(30,3600), "at": datetime.utcnow().isoformat() + "Z"}
