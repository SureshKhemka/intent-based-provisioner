import random
import string
from datetime import datetime


def _fake_id(prefix="reg"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "registry.create": _create,
        "registry.delete": _delete,
        "registry.push": _push,
        "registry.pull": _pull,
        "registry.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No registry handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create registry '{name}'", "would_call": "POST /registry/v1"}
    return {"status": "success", "message": f"registry completed", "name":name,"registry_uri":f"{_fake_id("r")}.dkr.ecr.us-east-1.amazonaws.com/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete registry '{name}'", "would_call": "DELETE /registry/v1"}
    return {"status": "success", "message": f"registry completed", "at": datetime.utcnow().isoformat() + "Z"}

def _push(params, dry_run):
    name=params.get("name","unknown")
    artifact=params.get("artifact","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would push artifact to registry '{name}'", "would_call": "POST /registry/v1"}
    return {"status": "success", "message": f"artifact to registry completed", "name":name,"digest":f"sha256:{_fake_id("d")}", "at": datetime.utcnow().isoformat() + "Z"}

def _pull(params, dry_run):
    name=params.get("name","unknown")
    artifact=params.get("artifact","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would pull artifact from registry '{name}'", "would_call": "GET /registry/v1"}
    return {"status": "success", "message": f"artifact from registry completed", "name":name, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for registry '{name}'", "would_call": "GET /registry/v1"}
    return {"status": "success", "message": f"registry completed", "images":random.randint(5,200),"size_gb":round(random.uniform(0.5,50),1), "at": datetime.utcnow().isoformat() + "Z"}
