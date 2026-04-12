import random
import string
from datetime import datetime


def _fake_id(prefix="waf"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "waf.create": _create,
        "waf.delete": _delete,
        "waf.update_rules": _update_rules,
        "waf.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No waf handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create WAF '{name}'", "would_call": "POST /waf/v1"}
    return {"status": "success", "message": f"WAF completed", "name":name,"waf_id":_fake_id("waf"),"rules_count":0, "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete WAF '{name}'", "would_call": "DELETE /waf/v1"}
    return {"status": "success", "message": f"WAF completed", "at": datetime.utcnow().isoformat() + "Z"}

def _update_rules(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would update rules on WAF '{name}'", "would_call": "PUT /waf/v1"}
    return {"status": "success", "message": f"WAF rules completed", "rules_count":random.randint(3,20), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for WAF '{name}'", "would_call": "GET /waf/v1"}
    return {"status": "success", "message": f"WAF completed", "state":"active","blocked_requests_24h":random.randint(100,50000),"rules_count":random.randint(3,20), "at": datetime.utcnow().isoformat() + "Z"}
