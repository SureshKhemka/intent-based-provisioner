import random
import string
from datetime import datetime


def _fake_id(prefix="vpn"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "vpn.create": _create,
        "vpn.delete": _delete,
        "vpn.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No vpn handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create VPN connection '{name}'", "would_call": "POST /vpn/v1/connections"}
    return {"status": "success", "message": f"VPN connection completed", "name":name,"vpn_id":_fake_id("vpn"),"state":"pending", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete VPN connection '{name}'", "would_call": "DELETE /vpn/v1/connections"}
    return {"status": "success", "message": f"VPN connection completed", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for VPN '{name}'", "would_call": "GET /vpn/v1/connections"}
    return {"status": "success", "message": f"VPN connection completed", "state":"available","tunnels_up":random.randint(1,2), "at": datetime.utcnow().isoformat() + "Z"}
