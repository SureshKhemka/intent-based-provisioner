import random
import string
from datetime import datetime


def _fake_id(prefix="lg"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "log.create_group": _create_group,
        "log.delete_group": _delete_group,
        "log.query": _query,
        "log.export": _export,
        "log.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No log handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_group(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create log group '{name}'", "would_call": "POST /logs/v1"}
    return {"status": "success", "message": f"log group completed", "name":name,"log_group_arn":f"arn:aws:logs:us-east-1:123456:log-group:{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_group(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete log group '{name}'", "would_call": "DELETE /logs/v1"}
    return {"status": "success", "message": f"log group completed", "at": datetime.utcnow().isoformat() + "Z"}

def _query(params, dry_run):
    group=params.get("group",params.get("name","unknown"))
    query_str=params.get("query","*")
    if dry_run:
        return {"status": "dry_run", "message": f"Would query logs in '{group}'", "would_call": "GET /logs/v1"}
    return {"status": "success", "message": f"logs completed", "results_count":random.randint(0,1000),"scanned_bytes":random.randint(10000,99999999), "at": datetime.utcnow().isoformat() + "Z"}

def _export(params, dry_run):
    group=params.get("group",params.get("name","unknown"))
    destination=params.get("destination","s3")
    if dry_run:
        return {"status": "dry_run", "message": f"Would export logs from '{group}' to {destination}", "would_call": "GET /logs/v1"}
    return {"status": "success", "message": f"logs completed", "export_task_id":_fake_id("task"), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for log group '{name}'", "would_call": "GET /logs/v1"}
    return {"status": "success", "message": f"log group completed", "stored_bytes":random.randint(1000000,9999999999),"retention_days":random.randint(7,365), "at": datetime.utcnow().isoformat() + "Z"}
