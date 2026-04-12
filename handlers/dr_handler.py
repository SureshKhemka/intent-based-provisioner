import random
import string
from datetime import datetime


def _fake_id(prefix="dr"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "dr.create_plan": _create_plan,
        "dr.failover": _failover,
        "dr.failback": _failback,
        "dr.test": _test,
        "dr.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No dr handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_plan(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create DR plan '{name}'", "would_call": "POST /drs/v1"}
    return {"status": "success", "message": f"DR plan completed", "name":name,"plan_id":_fake_id("dr"), "at": datetime.utcnow().isoformat() + "Z"}

def _failover(params, dry_run):
    name=params.get("name","unknown")
    region=params.get("region","us-west-2")
    if dry_run:
        return {"status": "dry_run", "message": f"Would initiate failover for '{name}' to {region}", "would_call": "POST /drs/v1"}
    return {"status": "success", "message": f"DR failover completed", "name":name,"failover_id":_fake_id("fo"),"target_region":region, "at": datetime.utcnow().isoformat() + "Z"}

def _failback(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would initiate failback for '{name}' to primary", "would_call": "POST /drs/v1"}
    return {"status": "success", "message": f"DR failback completed", "name":name,"failback_id":_fake_id("fb"), "at": datetime.utcnow().isoformat() + "Z"}

def _test(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would run DR test drill for '{name}'", "would_call": "POST /drs/v1"}
    return {"status": "success", "message": f"DR drill completed", "test_id":_fake_id("test"),"status":"RUNNING", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch DR status for '{name}'", "would_call": "GET /drs/v1"}
    return {"status": "success", "message": f"DR plan completed", "state":"ready","rpo_minutes":random.randint(1,60),"rto_minutes":random.randint(5,120),"last_test":"2026-04-01", "at": datetime.utcnow().isoformat() + "Z"}
