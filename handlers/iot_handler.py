import random
import string
from datetime import datetime


def _fake_id(prefix="iot"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "iot.create_thing": _create_thing,
        "iot.delete_thing": _delete_thing,
        "iot.create_rule": _create_rule,
        "iot.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No iot handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_thing(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would register IoT thing '{name}'", "would_call": "POST /iot/v1"}
    return {"status": "success", "message": f"IoT thing completed", "name":name,"thing_arn":f"arn:aws:iot:us-east-1:123456:thing/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_thing(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete IoT thing '{name}'", "would_call": "DELETE /iot/v1"}
    return {"status": "success", "message": f"IoT thing completed", "at": datetime.utcnow().isoformat() + "Z"}

def _create_rule(params, dry_run):
    name=params.get("name",_fake_id("rule"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would create IoT rule '{name}'", "would_call": "POST /iot/v1"}
    return {"status": "success", "message": f"IoT rule completed", "name":name,"rule_arn":f"arn:aws:iot:us-east-1:123456:rule/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch IoT status", "would_call": "GET /iot/v1"}
    return {"status": "success", "message": f"IoT completed", "things":random.randint(1,1000),"rules":random.randint(1,50),"connected":random.randint(1,500), "at": datetime.utcnow().isoformat() + "Z"}
