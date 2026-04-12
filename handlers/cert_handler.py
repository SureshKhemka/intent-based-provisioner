import random
import string
from datetime import datetime


def _fake_id(prefix="cert"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "cert.provision": _provision,
        "cert.delete": _delete,
        "cert.renew": _renew,
        "cert.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No cert handler for intent: {intent}"}
    return handler(params, dry_run)


def _provision(params, dry_run):
    domain=params.get("domain",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would provision TLS certificate for '{domain}'", "would_call": "POST /acm/v1/certificates"}
    return {"status": "success", "message": f"TLS certificate completed", "domain":domain,"cert_arn":f"arn:aws:acm:us-east-1:123456:certificate/{_fake_id("c")}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    domain=params.get("domain",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete TLS certificate for '{domain}'", "would_call": "DELETE /acm/v1/certificates"}
    return {"status": "success", "message": f"TLS certificate completed", "at": datetime.utcnow().isoformat() + "Z"}

def _renew(params, dry_run):
    domain=params.get("domain",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would renew TLS certificate for '{domain}'", "would_call": "PUT /acm/v1/certificates"}
    return {"status": "success", "message": f"TLS certificate completed", "domain":domain,"new_expiry":"2027-04-12", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    domain=params.get("domain",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch certificate status for '{domain}'", "would_call": "GET /acm/v1/certificates"}
    return {"status": "success", "message": f"TLS certificate completed", "domain":domain,"status":"ISSUED","expiry":"2027-04-12","days_remaining":random.randint(30,365), "at": datetime.utcnow().isoformat() + "Z"}
