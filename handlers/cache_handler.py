import random
import string
from datetime import datetime


def _fake_id(prefix="cache"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "cache.provision": _provision,
        "cache.delete":    _delete,
        "cache.resize":    _resize,
        "cache.flush":     _flush,
        "cache.status":    _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No cache handler for intent: {intent}"}
    return handler(params, dry_run)


def _provision(params, dry_run):
    name   = params.get("name", _fake_id())
    engine = params.get("engine", "redis")
    memory = params.get("memory", "4GB")
    nodes  = params.get("nodes", "1")
    if dry_run:
        return {"status": "dry_run", "message": f"Would provision {engine} cache '{name}' ({nodes} node(s), {memory})", "would_call": "POST /cache/v1/clusters"}
    return {"status": "success", "message": f"Cache cluster '{name}' provisioned", "name": name, "engine": engine, "memory": memory, "nodes": nodes, "endpoint": f"{name}.cache.{_fake_id('r')}.amazonaws.com:6379", "state": "available", "created_at": datetime.utcnow().isoformat() + "Z"}


def _delete(params, dry_run):
    name = params.get("name", "unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete cache cluster '{name}'", "would_call": "DELETE /cache/v1/clusters/{id}"}
    return {"status": "success", "message": f"Cache cluster '{name}' deleted", "deleted_at": datetime.utcnow().isoformat() + "Z"}


def _resize(params, dry_run):
    name   = params.get("name", "unknown")
    memory = params.get("memory", "")
    nodes  = params.get("nodes", "")
    if dry_run:
        return {"status": "dry_run", "message": f"Would resize cache '{name}' (memory={memory}, nodes={nodes})", "would_call": "PATCH /cache/v1/clusters/{id}"}
    return {"status": "success", "message": f"Cache cluster '{name}' resized", "resized_at": datetime.utcnow().isoformat() + "Z"}


def _flush(params, dry_run):
    name = params.get("name", "unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would flush all data from cache '{name}'", "would_call": "POST /cache/v1/clusters/{id}/flush"}
    return {"status": "success", "message": f"Cache cluster '{name}' flushed", "flushed_at": datetime.utcnow().isoformat() + "Z"}


def _status(params, dry_run):
    name = params.get("name", "unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for cache '{name}'", "would_call": "GET /cache/v1/clusters/{id}"}
    return {"status": "success", "name": name, "state": "available", "memory_usage": f"{random.randint(10, 85)}%", "connections": random.randint(5, 200), "hit_rate": f"{random.randint(80, 99)}%", "checked_at": datetime.utcnow().isoformat() + "Z"}
