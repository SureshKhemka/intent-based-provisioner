import random
import string
from datetime import datetime


def _fake_id(prefix="wh"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "warehouse.provision": _provision,
        "warehouse.delete": _delete,
        "warehouse.resize": _resize,
        "warehouse.query": _query,
        "warehouse.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No warehouse handler for intent: {intent}"}
    return handler(params, dry_run)


def _provision(params, dry_run):
    name=params.get("name",_fake_id())
    nodes=params.get("nodes","2")
    node_type=params.get("node_type","dc2.large")
    if dry_run:
        return {"status": "dry_run", "message": f"Would provision warehouse '{name}' ({nodes}x {node_type})", "would_call": "POST /redshift/v1/clusters"}
    return {"status": "success", "message": f"data warehouse completed", "name":name,"cluster_id":_fake_id("wh"),"endpoint":f"{name}.{_fake_id("c")}.us-east-1.redshift.amazonaws.com:5439", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete data warehouse '{name}'", "would_call": "DELETE /redshift/v1/clusters"}
    return {"status": "success", "message": f"data warehouse completed", "at": datetime.utcnow().isoformat() + "Z"}

def _resize(params, dry_run):
    name=params.get("name","unknown")
    nodes=params.get("nodes","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would resize warehouse '{name}' to {nodes} nodes", "would_call": "PUT /redshift/v1/clusters"}
    return {"status": "success", "message": f"data warehouse completed", "at": datetime.utcnow().isoformat() + "Z"}

def _query(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would execute query against warehouse '{name}'", "would_call": "GET /redshift/v1/clusters"}
    return {"status": "success", "message": f"data warehouse completed", "query_id":_fake_id("q"),"rows_returned":random.randint(0,100000),"duration_ms":random.randint(100,30000), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for warehouse '{name}'", "would_call": "GET /redshift/v1/clusters"}
    return {"status": "success", "message": f"data warehouse completed", "state":"available","nodes":random.randint(1,8),"cpu_usage":f"{random.randint(5,80)}%","storage_used":f"{random.randint(10,90)}%", "at": datetime.utcnow().isoformat() + "Z"}
