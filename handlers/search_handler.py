import random
import string
from datetime import datetime


def _fake_id(prefix="es"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "search.create": _create,
        "search.delete": _delete,
        "search.resize": _resize,
        "search.reindex": _reindex,
        "search.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No search handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    nodes=params.get("nodes","3")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create search cluster '{name}' ({nodes} nodes)", "would_call": "POST /opensearch/v1/domains"}
    return {"status": "success", "message": f"search cluster completed", "name":name,"domain_id":_fake_id("es"),"endpoint":f"search-{name}-{_fake_id("x")}.us-east-1.es.amazonaws.com", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete search cluster '{name}'", "would_call": "DELETE /opensearch/v1/domains"}
    return {"status": "success", "message": f"search cluster completed", "at": datetime.utcnow().isoformat() + "Z"}

def _resize(params, dry_run):
    name=params.get("name","unknown")
    nodes=params.get("nodes","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would resize search cluster '{name}' to {nodes} nodes", "would_call": "PUT /opensearch/v1/domains"}
    return {"status": "success", "message": f"search cluster completed", "at": datetime.utcnow().isoformat() + "Z"}

def _reindex(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would reindex search cluster '{name}'", "would_call": "PUT /opensearch/v1/domains"}
    return {"status": "success", "message": f"search index completed", "task_id":_fake_id("task"), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for search cluster '{name}'", "would_call": "GET /opensearch/v1/domains"}
    return {"status": "success", "message": f"search cluster completed", "state":"active","indices":random.randint(5,100),"docs":random.randint(10000,10000000),"storage_gb":round(random.uniform(1,500),1), "at": datetime.utcnow().isoformat() + "Z"}
