import random
import string
from datetime import datetime


def _fake_id(prefix="topic"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "notification.create_topic": _create_topic,
        "notification.delete_topic": _delete_topic,
        "notification.publish": _publish,
        "notification.subscribe": _subscribe,
        "notification.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No notification handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_topic(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create notification topic '{name}'", "would_call": "POST /sns/v1/topics"}
    return {"status": "success", "message": f"topic completed", "name":name,"topic_arn":f"arn:aws:sns:us-east-1:123456:{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_topic(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete notification topic '{name}'", "would_call": "DELETE /sns/v1/topics"}
    return {"status": "success", "message": f"topic completed", "at": datetime.utcnow().isoformat() + "Z"}

def _publish(params, dry_run):
    name=params.get("name",params.get("topic","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would publish notification to topic '{name}'", "would_call": "POST /sns/v1/topics"}
    return {"status": "success", "message": f"notification completed", "message_id":_fake_id("msg"), "at": datetime.utcnow().isoformat() + "Z"}

def _subscribe(params, dry_run):
    name=params.get("name",params.get("topic","unknown"))
    endpoint=params.get("endpoint","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would subscribe '{endpoint}' to topic '{name}'", "would_call": "POST /sns/v1/topics"}
    return {"status": "success", "message": f"to topic completed", "subscription_arn":f"arn:aws:sns:us-east-1:123456:{name}:{_fake_id("s")}", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for topic '{name}'", "would_call": "GET /sns/v1/topics"}
    return {"status": "success", "message": f"notification topic completed", "subscriptions":random.randint(1,20),"messages_published_24h":random.randint(0,10000), "at": datetime.utcnow().isoformat() + "Z"}
