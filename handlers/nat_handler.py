import random
import string
from datetime import datetime


def _fake_id(prefix="nat"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "nat.provision": _provision,
        "nat.delete": _delete,
        "nat.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No nat handler for intent: {intent}"}
    return handler(params, dry_run)


def _provision(params, dry_run):
    name=params.get("name",_fake_id())
    subnet=params.get("subnet","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would provision NAT gateway '{name}' in subnet '{subnet}'", "would_call": "POST /vpc/v1/nat-gateways"}
    return {"status": "success", "message": f"NAT gateway completed", "name":name,"nat_id":_fake_id("nat"),"subnet":subnet, "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete NAT gateway '{name}'", "would_call": "DELETE /vpc/v1/nat-gateways"}
    return {"status": "success", "message": f"NAT gateway completed", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for NAT gateway '{name}'", "would_call": "GET /vpc/v1/nat-gateways"}
    return {"status": "success", "message": f"NAT gateway completed", "state":"available","bytes_processed":random.randint(1000000,9999999999), "at": datetime.utcnow().isoformat() + "Z"}
