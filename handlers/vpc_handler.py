import random
import string
from datetime import datetime


def _fake_id(prefix="vpc"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "vpc.create": _create,
        "vpc.delete": _delete,
        "vpc.peer": _peer,
        "vpc.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No vpc handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    cidr=params.get("cidr","10.0.0.0/16")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create VPC '{name}' with CIDR {cidr}", "would_call": "POST /vpc/v1"}
    return {"status": "success", "message": f"VPC completed", "name":name,"vpc_id":_fake_id("vpc"),"cidr":cidr, "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete VPC '{name}'", "would_call": "DELETE /vpc/v1"}
    return {"status": "success", "message": f"VPC completed", "at": datetime.utcnow().isoformat() + "Z"}

def _peer(params, dry_run):
    source=params.get("source",params.get("name","unknown"))
    target=params.get("target","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would peer VPC '{source}' with '{target}'", "would_call": "POST /vpc/v1"}
    return {"status": "success", "message": f"VPC peering completed", "peering_id":_fake_id("pcx"),"source":source,"target":target, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for VPC '{name}'", "would_call": "GET /vpc/v1"}
    return {"status": "success", "message": f"VPC completed", "state":"available","subnets":random.randint(2,8),"route_tables":random.randint(1,4), "at": datetime.utcnow().isoformat() + "Z"}
