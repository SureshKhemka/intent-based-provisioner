import random
import string
from datetime import datetime


def _fake_id(prefix="ami"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "image.create": _create,
        "image.delete": _delete,
        "image.share": _share,
        "image.deregister": _deregister,
        "image.list": _list,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No image handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    source=params.get("source","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create machine image '{name}' from '{source}'", "would_call": "POST /ec2/v1/images"}
    return {"status": "success", "message": f"machine image completed", "name":name,"image_id":_fake_id("ami"), "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete machine image '{name}'", "would_call": "DELETE /ec2/v1/images"}
    return {"status": "success", "message": f"machine image completed", "at": datetime.utcnow().isoformat() + "Z"}

def _share(params, dry_run):
    name=params.get("name","unknown")
    account=params.get("account","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would share image '{name}' with account '{account}'", "would_call": "POST /ec2/v1/images"}
    return {"status": "success", "message": f"machine image completed", "name":name,"account":account, "at": datetime.utcnow().isoformat() + "Z"}

def _deregister(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would deregister machine image '{name}'", "would_call": "DELETE /ec2/v1/images"}
    return {"status": "success", "message": f"machine image completed", "at": datetime.utcnow().isoformat() + "Z"}

def _list(params, dry_run):
    env=params.get("environment","all")
    if dry_run:
        return {"status": "dry_run", "message": f"Would list machine images for environment: {env}", "would_call": "GET /ec2/v1/images"}
    return {"status": "success", "message": f"machine images completed", "count":random.randint(5,100), "at": datetime.utcnow().isoformat() + "Z"}
