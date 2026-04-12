import random
import string
from datetime import datetime


def _fake_id(prefix="nb"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "notebook.create": _create,
        "notebook.delete": _delete,
        "notebook.start": _start,
        "notebook.stop": _stop,
        "notebook.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No notebook handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    instance_type=params.get("instance_type","ml.t3.medium")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create notebook '{name}' ({instance_type})", "would_call": "POST /sagemaker/v1/notebooks"}
    return {"status": "success", "message": f"notebook completed", "name":name,"notebook_arn":f"arn:aws:sagemaker:us-east-1:123456:notebook-instance/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete notebook '{name}'", "would_call": "DELETE /sagemaker/v1/notebooks"}
    return {"status": "success", "message": f"notebook completed", "at": datetime.utcnow().isoformat() + "Z"}

def _start(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would start notebook '{name}'", "would_call": "POST /sagemaker/v1/notebooks"}
    return {"status": "success", "message": f"notebook completed", "name":name,"state":"InService", "at": datetime.utcnow().isoformat() + "Z"}

def _stop(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would stop notebook '{name}'", "would_call": "POST /sagemaker/v1/notebooks"}
    return {"status": "success", "message": f"notebook completed", "name":name,"state":"Stopped", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for notebook '{name}'", "would_call": "GET /sagemaker/v1/notebooks"}
    return {"status": "success", "message": f"notebook completed", "state":"InService","instance_type":params.get("instance_type","ml.t3.medium"),"uptime_hrs":random.randint(1,168), "at": datetime.utcnow().isoformat() + "Z"}
