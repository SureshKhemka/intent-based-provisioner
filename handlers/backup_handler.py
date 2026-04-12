import random
import string
from datetime import datetime


def _fake_id(prefix="bkp"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "backup.create_plan": _create_plan,
        "backup.delete_plan": _delete_plan,
        "backup.run": _run,
        "backup.restore": _restore,
        "backup.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No backup handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_plan(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create backup plan '{name}'", "would_call": "POST /backup/v1"}
    return {"status": "success", "message": f"backup plan completed", "name":name,"plan_id":_fake_id("bkp"), "at": datetime.utcnow().isoformat() + "Z"}

def _delete_plan(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete backup plan '{name}'", "would_call": "DELETE /backup/v1"}
    return {"status": "success", "message": f"backup plan completed", "at": datetime.utcnow().isoformat() + "Z"}

def _run(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would run backup job for plan '{name}'", "would_call": "POST /backup/v1"}
    return {"status": "success", "message": f"backup job completed", "job_id":_fake_id("job"),"status":"RUNNING", "at": datetime.utcnow().isoformat() + "Z"}

def _restore(params, dry_run):
    name=params.get("name","unknown")
    recovery_point=params.get("recovery_point","latest")
    if dry_run:
        return {"status": "dry_run", "message": f"Would restore from backup '{name}' recovery point '{recovery_point}'", "would_call": "POST /backup/v1"}
    return {"status": "success", "message": f"from backup completed", "restore_job_id":_fake_id("rj"), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch backup status for '{name}'", "would_call": "GET /backup/v1"}
    return {"status": "success", "message": f"backup completed", "last_backup":"2026-04-11T02:00:00Z","recovery_points":random.randint(1,30),"status":"COMPLETED", "at": datetime.utcnow().isoformat() + "Z"}
