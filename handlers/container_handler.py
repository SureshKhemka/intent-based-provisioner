import random
import string
from datetime import datetime


def _fake_id(prefix="img"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "container.push": _push,
        "container.pull": _pull,
        "container.delete": _delete,
        "container.list": _list,
        "container.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No container handler for intent: {intent}"}
    return handler(params, dry_run)


def _push(params, dry_run):
    image=params.get("image",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would push image '{image}' to registry", "would_call": "POST /ecr/v1/images"}
    return {"status": "success", "message": f"image to registry completed", "image":image,"digest":f"sha256:{_fake_id("d")}", "at": datetime.utcnow().isoformat() + "Z"}

def _pull(params, dry_run):
    image=params.get("image",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would pull image '{image}' from registry", "would_call": "GET /ecr/v1/images"}
    return {"status": "success", "message": f"image from registry completed", "image":image, "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    image=params.get("image",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete image '{image}' from registry", "would_call": "DELETE /ecr/v1/images"}
    return {"status": "success", "message": f"image from registry completed", "at": datetime.utcnow().isoformat() + "Z"}

def _list(params, dry_run):
    registry=params.get("registry",params.get("name","default"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would list images in registry '{registry}'", "would_call": "GET /ecr/v1/images"}
    return {"status": "success", "message": f"images in registry completed", "count":random.randint(5,50), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","default")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for registry '{name}'", "would_call": "GET /ecr/v1/images"}
    return {"status": "success", "message": f"container registry completed", "images":random.randint(10,200),"size_gb":round(random.uniform(1,100),1), "at": datetime.utcnow().isoformat() + "Z"}
