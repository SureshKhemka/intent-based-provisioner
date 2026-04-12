import random
import string
from datetime import datetime


def _fake_id(prefix="key"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "kms.create_key": _create_key,
        "kms.delete_key": _delete_key,
        "kms.rotate": _rotate,
        "kms.encrypt": _encrypt,
        "kms.decrypt": _decrypt,
        "kms.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No kms handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_key(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create KMS key '{name}'", "would_call": "POST /kms/v1/keys"}
    return {"status": "success", "message": f"KMS key completed", "name":name,"key_id":_fake_id("key"),"key_arn":f"arn:aws:kms:us-east-1:123456:key/{_fake_id("k")}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_key(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would schedule deletion of KMS key '{name}'", "would_call": "DELETE /kms/v1/keys"}
    return {"status": "success", "message": f"KMS key completed", "pending_deletion_days":30, "at": datetime.utcnow().isoformat() + "Z"}

def _rotate(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would rotate KMS key '{name}'", "would_call": "PUT /kms/v1/keys"}
    return {"status": "success", "message": f"KMS key completed", "name":name, "at": datetime.utcnow().isoformat() + "Z"}

def _encrypt(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would encrypt data with KMS key '{name}'", "would_call": "POST /kms/v1/keys"}
    return {"status": "success", "message": f"data completed", "key_id":name,"ciphertext_blob":"<encrypted>", "at": datetime.utcnow().isoformat() + "Z"}

def _decrypt(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would decrypt data with KMS key '{name}'", "would_call": "GET /kms/v1/keys"}
    return {"status": "success", "message": f"data completed", "key_id":name, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for KMS key '{name}'", "would_call": "GET /kms/v1/keys"}
    return {"status": "success", "message": f"KMS key completed", "state":"Enabled","key_rotation":"Enabled","creation_date":"2026-01-15", "at": datetime.utcnow().isoformat() + "Z"}
