import random
import string
from datetime import datetime


def _fake_id(prefix="snap"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "snapshot.create": _create,
        "snapshot.delete": _delete,
        "snapshot.copy": _copy,
        "snapshot.restore": _restore,
        "snapshot.list": _list,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No snapshot handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",params.get("source","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would create snapshot of '{name}'", "would_call": "POST /ec2/v1/snapshots"}
    return {"status": "success", "message": f"snapshot completed", "snapshot_id":_fake_id("snap"),"source":name, "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name",params.get("snapshot_id","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete snapshot '{name}'", "would_call": "DELETE /ec2/v1/snapshots"}
    return {"status": "success", "message": f"snapshot completed", "at": datetime.utcnow().isoformat() + "Z"}

def _copy(params, dry_run):
    name=params.get("name",params.get("snapshot_id","unknown"))
    region=params.get("region","us-west-2")
    if dry_run:
        return {"status": "dry_run", "message": f"Would copy snapshot '{name}' to {region}", "would_call": "POST /ec2/v1/snapshots"}
    return {"status": "success", "message": f"snapshot to region completed", "new_snapshot_id":_fake_id("snap"),"destination_region":region, "at": datetime.utcnow().isoformat() + "Z"}

def _restore(params, dry_run):
    name=params.get("name",params.get("snapshot_id","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would restore from snapshot '{name}'", "would_call": "POST /ec2/v1/snapshots"}
    return {"status": "success", "message": f"from snapshot completed", "resource_id":_fake_id("i"), "at": datetime.utcnow().isoformat() + "Z"}

def _list(params, dry_run):
    env=params.get("environment","all")
    if dry_run:
        return {"status": "dry_run", "message": f"Would list snapshots for environment: {env}", "would_call": "GET /ec2/v1/snapshots"}
    return {"status": "success", "message": f"snapshots completed", "count":random.randint(5,50), "at": datetime.utcnow().isoformat() + "Z"}
