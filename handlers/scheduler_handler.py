import random
import string
from datetime import datetime


def _fake_id(prefix="sched"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "scheduler.create": _create,
        "scheduler.delete": _delete,
        "scheduler.enable": _enable,
        "scheduler.disable": _disable,
        "scheduler.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No scheduler handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    schedule=params.get("schedule",params.get("cron","rate(1 hour)"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would create schedule '{name}' ({schedule})", "would_call": "POST /scheduler/v1/schedules"}
    return {"status": "success", "message": f"schedule completed", "name":name,"schedule_arn":f"arn:aws:scheduler:us-east-1:123456:schedule/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete schedule '{name}'", "would_call": "DELETE /scheduler/v1/schedules"}
    return {"status": "success", "message": f"schedule completed", "at": datetime.utcnow().isoformat() + "Z"}

def _enable(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would enable schedule '{name}'", "would_call": "POST /scheduler/v1/schedules"}
    return {"status": "success", "message": f"schedule completed", "name":name,"state":"ENABLED", "at": datetime.utcnow().isoformat() + "Z"}

def _disable(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would disable schedule '{name}'", "would_call": "DELETE /scheduler/v1/schedules"}
    return {"status": "success", "message": f"schedule completed", "name":name,"state":"DISABLED", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for schedule '{name}'", "would_call": "GET /scheduler/v1/schedules"}
    return {"status": "success", "message": f"schedule completed", "state":"ENABLED","next_run":"2026-04-13T02:00:00Z","last_run":"2026-04-12T02:00:00Z", "at": datetime.utcnow().isoformat() + "Z"}
