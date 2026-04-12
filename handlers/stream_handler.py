import random
import string
from datetime import datetime


def _fake_id(prefix="str"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "stream.create": _create,
        "stream.delete": _delete,
        "stream.scale": _scale,
        "stream.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No stream handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    shards=params.get("shards","4")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create stream '{name}' with {shards} shards", "would_call": "POST /kinesis/v1/streams"}
    return {"status": "success", "message": f"data stream completed", "name":name,"shards":shards,"stream_arn":f"arn:aws:kinesis:us-east-1:123456:stream/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete stream '{name}'", "would_call": "DELETE /kinesis/v1/streams"}
    return {"status": "success", "message": f"data stream completed", "at": datetime.utcnow().isoformat() + "Z"}

def _scale(params, dry_run):
    name=params.get("name","unknown")
    shards=params.get("shards","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would scale stream '{name}' to {shards} shards", "would_call": "POST /kinesis/v1/streams"}
    return {"status": "success", "message": f"stream shards completed", "shards":shards, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for stream '{name}'", "would_call": "GET /kinesis/v1/streams"}
    return {"status": "success", "message": f"data stream completed", "state":"ACTIVE","open_shards":random.randint(1,16),"incoming_records":f"{random.randint(100,10000)}/s", "at": datetime.utcnow().isoformat() + "Z"}
