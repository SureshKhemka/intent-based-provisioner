import random
import string
from datetime import datetime


def _fake_id(prefix="lake"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "datalake.create": _create,
        "datalake.delete": _delete,
        "datalake.set_permissions": _set_permissions,
        "datalake.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No datalake handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create data lake '{name}'", "would_call": "POST /lakeformation/v1"}
    return {"status": "success", "message": f"data lake completed", "name":name,"lake_id":_fake_id("lake"), "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete data lake '{name}'", "would_call": "DELETE /lakeformation/v1"}
    return {"status": "success", "message": f"data lake completed", "at": datetime.utcnow().isoformat() + "Z"}

def _set_permissions(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would set permissions on data lake '{name}'", "would_call": "PUT /lakeformation/v1"}
    return {"status": "success", "message": f"data lake permissions completed", "name":name, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for data lake '{name}'", "would_call": "GET /lakeformation/v1"}
    return {"status": "success", "message": f"data lake completed", "state":"active","tables":random.randint(5,200),"size_tb":round(random.uniform(0.1,50),1), "at": datetime.utcnow().isoformat() + "Z"}
