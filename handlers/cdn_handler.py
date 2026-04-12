import random
import string
from datetime import datetime


def _fake_id(prefix="cdn"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "cdn.create": _create,
        "cdn.delete": _delete,
        "cdn.invalidate": _invalidate,
        "cdn.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No cdn handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    origin=params.get("origin","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create CDN distribution '{name}' with origin '{origin}'", "would_call": "POST /cloudfront/v1/distributions"}
    return {"status": "success", "message": f"CDN distribution completed", "name":name,"distribution_id":_fake_id("E"),"domain_name":f"{_fake_id("d")}.cloudfront.net", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete CDN distribution '{name}'", "would_call": "DELETE /cloudfront/v1/distributions"}
    return {"status": "success", "message": f"CDN distribution completed", "at": datetime.utcnow().isoformat() + "Z"}

def _invalidate(params, dry_run):
    name=params.get("name","unknown")
    path=params.get("path","/*")
    if dry_run:
        return {"status": "dry_run", "message": f"Would invalidate CDN cache for '{name}' path={path}", "would_call": "PUT /cloudfront/v1/distributions"}
    return {"status": "success", "message": f"CDN cache completed", "invalidation_id":_fake_id("inv"),"path":path, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for CDN '{name}'", "would_call": "GET /cloudfront/v1/distributions"}
    return {"status": "success", "message": f"CDN distribution completed", "state":"Deployed","hit_rate":f"{random.randint(70,99)}%","requests_24h":random.randint(1000,1000000), "at": datetime.utcnow().isoformat() + "Z"}
