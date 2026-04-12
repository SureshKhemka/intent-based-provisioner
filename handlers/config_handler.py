import random
import string
from datetime import datetime


def _fake_id(prefix="cfg"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "config.create_rule": _create_rule,
        "config.delete_rule": _delete_rule,
        "config.evaluate": _evaluate,
        "config.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No config handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_rule(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create config rule '{name}'", "would_call": "POST /config/v1/rules"}
    return {"status": "success", "message": f"config rule completed", "name":name,"rule_arn":f"arn:aws:config:us-east-1:123456:config-rule/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_rule(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete config rule '{name}'", "would_call": "DELETE /config/v1/rules"}
    return {"status": "success", "message": f"config rule completed", "at": datetime.utcnow().isoformat() + "Z"}

def _evaluate(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would evaluate compliance for rule '{name}'", "would_call": "PUT /config/v1/rules"}
    return {"status": "success", "message": f"compliance completed", "compliant":random.randint(50,200),"non_compliant":random.randint(0,20), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch config compliance status", "would_call": "GET /config/v1/rules"}
    return {"status": "success", "message": f"config rules completed", "rules":random.randint(5,50),"compliant_resources":random.randint(50,500),"non_compliant":random.randint(0,30), "at": datetime.utcnow().isoformat() + "Z"}
