import random
import string
from datetime import datetime


def _fake_id(prefix="q"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "queue.create": _create,
        "queue.delete": _delete,
        "queue.purge":  _purge,
        "queue.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No queue handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name = params.get("name", _fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create queue '{name}'", "would_call": "POST /sqs/v1/queues"}
    return {"status": "success", "message": f"Queue '{name}' created", "name": name, "queue_url": f"https://sqs.us-east-1.amazonaws.com/123456/{name}", "created_at": datetime.utcnow().isoformat() + "Z"}


def _delete(params, dry_run):
    name = params.get("name", "unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete queue '{name}'", "would_call": "DELETE /sqs/v1/queues/{name}"}
    return {"status": "success", "message": f"Queue '{name}' deleted", "deleted_at": datetime.utcnow().isoformat() + "Z"}


def _purge(params, dry_run):
    name = params.get("name", "unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would purge all messages from queue '{name}'", "would_call": f"POST /sqs/v1/queues/{name}/purge"}
    return {"status": "success", "message": f"Queue '{name}' purged — {random.randint(100, 50000)} messages removed", "purged_at": datetime.utcnow().isoformat() + "Z"}


def _status(params, dry_run):
    name = params.get("name", "unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for queue '{name}'", "would_call": f"GET /sqs/v1/queues/{name}/attributes"}
    return {"status": "success", "name": name, "messages_available": random.randint(0, 10000), "messages_in_flight": random.randint(0, 100), "checked_at": datetime.utcnow().isoformat() + "Z"}
