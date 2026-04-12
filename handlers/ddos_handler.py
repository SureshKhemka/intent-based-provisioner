import random
import string
from datetime import datetime


def _fake_id(prefix="ddos"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "ddos.enable": _enable,
        "ddos.disable": _disable,
        "ddos.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No ddos handler for intent: {intent}"}
    return handler(params, dry_run)


def _enable(params, dry_run):
    name=params.get("name","unknown")
    tier=params.get("tier","standard")
    if dry_run:
        return {"status": "dry_run", "message": f"Would enable {tier} DDoS protection on '{name}'", "would_call": "POST /shield/v1"}
    return {"status": "success", "message": f"DDoS protection completed", "name":name,"tier":tier,"protection_id":_fake_id("ddos"), "at": datetime.utcnow().isoformat() + "Z"}

def _disable(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would disable DDoS protection on '{name}'", "would_call": "DELETE /shield/v1"}
    return {"status": "success", "message": f"DDoS protection completed", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch DDoS protection status for '{name}'", "would_call": "GET /shield/v1"}
    return {"status": "success", "message": f"DDoS protection completed", "protected":True,"attacks_mitigated_30d":random.randint(0,50), "at": datetime.utcnow().isoformat() + "Z"}
