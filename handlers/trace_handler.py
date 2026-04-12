import random
import string
from datetime import datetime


def _fake_id(prefix="tr"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "trace.enable": _enable,
        "trace.disable": _disable,
        "trace.query": _query,
        "trace.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No trace handler for intent: {intent}"}
    return handler(params, dry_run)


def _enable(params, dry_run):
    service=params.get("service",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would enable tracing on service '{service}'", "would_call": "POST /xray/v1"}
    return {"status": "success", "message": f"tracing completed", "service":service, "at": datetime.utcnow().isoformat() + "Z"}

def _disable(params, dry_run):
    service=params.get("service",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would disable tracing on service '{service}'", "would_call": "DELETE /xray/v1"}
    return {"status": "success", "message": f"tracing completed", "at": datetime.utcnow().isoformat() + "Z"}

def _query(params, dry_run):
    service=params.get("service",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would query traces for service '{service}'", "would_call": "GET /xray/v1"}
    return {"status": "success", "message": f"traces completed", "traces_found":random.randint(10,5000),"avg_duration_ms":random.randint(10,3000), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    service=params.get("service",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch tracing status for '{service}'", "would_call": "GET /xray/v1"}
    return {"status": "success", "message": f"tracing completed", "enabled":True,"traces_24h":random.randint(1000,100000), "at": datetime.utcnow().isoformat() + "Z"}
