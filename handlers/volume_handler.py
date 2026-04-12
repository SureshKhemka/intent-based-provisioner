import random
import string
from datetime import datetime


def _fake_id(prefix="vol"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "volume.create": _create,
        "volume.delete": _delete,
        "volume.resize": _resize,
        "volume.attach": _attach,
        "volume.detach": _detach,
        "volume.snapshot": _snapshot,
        "volume.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No volume handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    size=params.get("size_gb",params.get("size","100"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would create {size}GB volume '{name}'", "would_call": "POST /ebs/v1/volumes"}
    return {"status": "success", "message": f"volume completed", "name":name,"volume_id":_fake_id("vol"),"size_gb":size, "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete volume '{name}'", "would_call": "DELETE /ebs/v1/volumes"}
    return {"status": "success", "message": f"volume completed", "at": datetime.utcnow().isoformat() + "Z"}

def _resize(params, dry_run):
    name=params.get("name","unknown")
    size=params.get("size_gb","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would resize volume '{name}' to {size}GB", "would_call": "PUT /ebs/v1/volumes"}
    return {"status": "success", "message": f"volume completed", "name":name, "at": datetime.utcnow().isoformat() + "Z"}

def _attach(params, dry_run):
    name=params.get("name","unknown")
    instance=params.get("instance","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would attach volume '{name}' to instance '{instance}'", "would_call": "POST /ebs/v1/volumes"}
    return {"status": "success", "message": f"volume to instance completed", "name":name,"instance":instance,"device":"/dev/xvdf", "at": datetime.utcnow().isoformat() + "Z"}

def _detach(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would detach volume '{name}'", "would_call": "DELETE /ebs/v1/volumes"}
    return {"status": "success", "message": f"volume from instance completed", "name":name, "at": datetime.utcnow().isoformat() + "Z"}

def _snapshot(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create snapshot of volume '{name}'", "would_call": "POST /ebs/v1/volumes"}
    return {"status": "success", "message": f"volume snapshot completed", "name":name,"snapshot_id":_fake_id("snap"), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for volume '{name}'", "would_call": "GET /ebs/v1/volumes"}
    return {"status": "success", "message": f"volume completed", "state":"in-use","size_gb":random.randint(10,2000),"iops":random.randint(100,16000), "at": datetime.utcnow().isoformat() + "Z"}
