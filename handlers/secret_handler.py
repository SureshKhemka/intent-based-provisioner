import random
import string
from datetime import datetime


def _fake_id(prefix="secret"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "secret.create": _create,
        "secret.delete": _delete,
        "secret.rotate": _rotate,
        "secret.get": _get,
        "secret.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No secret handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create secret '{name}'", "would_call": "POST /secretsmanager/v1/secrets"}
    return {"status": "success", "message": f"secret completed", "name":name,"secret_arn":f"arn:aws:secretsmanager:us-east-1:123456:secret:{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete secret '{name}'", "would_call": "DELETE /secretsmanager/v1/secrets"}
    return {"status": "success", "message": f"secret completed", "at": datetime.utcnow().isoformat() + "Z"}

def _rotate(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would rotate secret '{name}'", "would_call": "PUT /secretsmanager/v1/secrets"}
    return {"status": "success", "message": f"secret completed", "name":name,"version_id":_fake_id("v"), "at": datetime.utcnow().isoformat() + "Z"}

def _get(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would retrieve secret '{name}'", "would_call": "GET /secretsmanager/v1/secrets"}
    return {"status": "success", "message": f"secret completed", "name":name,"version_stage":"AWSCURRENT", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would list secrets status", "would_call": "GET /secretsmanager/v1/secrets"}
    return {"status": "success", "message": f"secrets completed", "total_secrets":random.randint(5,100),"rotation_enabled":random.randint(2,20), "at": datetime.utcnow().isoformat() + "Z"}
