import random
import string
from datetime import datetime


def _fake_id(prefix="asg"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "autoscale.create": _create,
        "autoscale.delete": _delete,
        "autoscale.update_policy": _update_policy,
        "autoscale.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No autoscale handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    min_size=params.get("min","2")
    max_size=params.get("max","10")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create ASG '{name}' (min={min_size}, max={max_size})", "would_call": "POST /autoscaling/v1/groups"}
    return {"status": "success", "message": f"auto-scaling group completed", "name":name,"asg_id":_fake_id("asg"),"min":min_size,"max":max_size, "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete ASG '{name}'", "would_call": "DELETE /autoscaling/v1/groups"}
    return {"status": "success", "message": f"auto-scaling group completed", "at": datetime.utcnow().isoformat() + "Z"}

def _update_policy(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would update scaling policy for ASG '{name}'", "would_call": "PUT /autoscaling/v1/groups"}
    return {"status": "success", "message": f"scaling policy completed", "name":name, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for ASG '{name}'", "would_call": "GET /autoscaling/v1/groups"}
    return {"status": "success", "message": f"auto-scaling group completed", "desired":random.randint(2,10),"running":random.randint(2,10),"min":2,"max":10, "at": datetime.utcnow().isoformat() + "Z"}
