import random
import string
from datetime import datetime


def _fake_id(prefix="comp"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "compliance.run_scan": _run_scan,
        "compliance.create_policy": _create_policy,
        "compliance.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No compliance handler for intent: {intent}"}
    return handler(params, dry_run)


def _run_scan(params, dry_run):
    scope=params.get("scope",params.get("name","all"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would run compliance scan on '{scope}'", "would_call": "POST /securityhub/v1"}
    return {"status": "success", "message": f"compliance scan completed", "scan_id":_fake_id("scan"),"status":"RUNNING", "at": datetime.utcnow().isoformat() + "Z"}

def _create_policy(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create compliance policy '{name}'", "would_call": "POST /securityhub/v1"}
    return {"status": "success", "message": f"compliance policy completed", "name":name,"policy_arn":f"arn:aws:securityhub:us-east-1:123456:policy/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch compliance status", "would_call": "GET /securityhub/v1"}
    return {"status": "success", "message": f"compliance completed", "score":random.randint(60,100),"critical":random.randint(0,5),"high":random.randint(0,20),"passed":random.randint(50,200), "at": datetime.utcnow().isoformat() + "Z"}
