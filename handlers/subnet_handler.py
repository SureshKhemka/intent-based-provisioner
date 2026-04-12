import random
import string
from datetime import datetime


def _fake_id(prefix="subnet"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "subnet.create": _create,
        "subnet.delete": _delete,
        "subnet.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No subnet handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    cidr=params.get("cidr","10.0.1.0/24")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create subnet '{name}' with CIDR {cidr}", "would_call": "POST /vpc/v1/subnets"}
    return {"status": "success", "message": f"subnet completed", "name":name,"subnet_id":_fake_id("subnet"),"cidr":cidr, "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete subnet '{name}'", "would_call": "DELETE /vpc/v1/subnets"}
    return {"status": "success", "message": f"subnet completed", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for subnet '{name}'", "would_call": "GET /vpc/v1/subnets"}
    return {"status": "success", "message": f"subnet completed", "state":"available","available_ips":random.randint(10,250), "at": datetime.utcnow().isoformat() + "Z"}
