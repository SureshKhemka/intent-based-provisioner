import random
import string
from datetime import datetime


def _fake_id(prefix="fs"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "filesystem.create": _create,
        "filesystem.delete": _delete,
        "filesystem.resize": _resize,
        "filesystem.mount": _mount,
        "filesystem.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No filesystem handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create filesystem '{name}'", "would_call": "POST /efs/v1/filesystems"}
    return {"status": "success", "message": f"filesystem completed", "name":name,"fs_id":_fake_id("fs"), "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete filesystem '{name}'", "would_call": "DELETE /efs/v1/filesystems"}
    return {"status": "success", "message": f"filesystem completed", "at": datetime.utcnow().isoformat() + "Z"}

def _resize(params, dry_run):
    name=params.get("name","unknown")
    size=params.get("size_gb","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would resize filesystem '{name}' to {size}GB", "would_call": "PUT /efs/v1/filesystems"}
    return {"status": "success", "message": f"filesystem completed", "at": datetime.utcnow().isoformat() + "Z"}

def _mount(params, dry_run):
    name=params.get("name","unknown")
    target=params.get("target","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would mount filesystem '{name}' on '{target}'", "would_call": "POST /efs/v1/filesystems"}
    return {"status": "success", "message": f"filesystem completed", "mount_point":target, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for filesystem '{name}'", "would_call": "GET /efs/v1/filesystems"}
    return {"status": "success", "message": f"filesystem completed", "state":"available","size_gb":round(random.uniform(1,500),1),"mount_targets":random.randint(1,5), "at": datetime.utcnow().isoformat() + "Z"}
