import random
import string
from datetime import datetime


def _fake_id(prefix="role"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "iam.create_role": _create_role,
        "iam.delete_role": _delete_role,
        "iam.attach_policy": _attach_policy,
        "iam.create_user": _create_user,
        "iam.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No iam handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_role(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create IAM role '{name}'", "would_call": "POST /iam/v1"}
    return {"status": "success", "message": f"IAM role completed", "name":name,"role_arn":f"arn:aws:iam::123456:role/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_role(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete IAM role '{name}'", "would_call": "DELETE /iam/v1"}
    return {"status": "success", "message": f"IAM role completed", "at": datetime.utcnow().isoformat() + "Z"}

def _attach_policy(params, dry_run):
    role=params.get("role",params.get("name","unknown"))
    policy=params.get("policy","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would attach policy '{policy}' to role '{role}'", "would_call": "POST /iam/v1"}
    return {"status": "success", "message": f"policy completed", "role":role,"policy":policy, "at": datetime.utcnow().isoformat() + "Z"}

def _create_user(params, dry_run):
    name=params.get("name",_fake_id("user"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would create IAM user '{name}'", "would_call": "POST /iam/v1"}
    return {"status": "success", "message": f"IAM user completed", "name":name,"user_arn":f"arn:aws:iam::123456:user/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch IAM status", "would_call": "GET /iam/v1"}
    return {"status": "success", "message": f"IAM completed", "roles":random.randint(5,50),"users":random.randint(3,30),"policies":random.randint(10,100), "at": datetime.utcnow().isoformat() + "Z"}
