import random
import string
from datetime import datetime


def _fake_id(prefix="mesh"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "servicemesh.install": _install,
        "servicemesh.uninstall": _uninstall,
        "servicemesh.configure": _configure,
        "servicemesh.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No servicemesh handler for intent: {intent}"}
    return handler(params, dry_run)


def _install(params, dry_run):
    name=params.get("name","istio")
    cluster=params.get("cluster","default")
    if dry_run:
        return {"status": "dry_run", "message": f"Would install service mesh '{name}' on cluster '{cluster}'", "would_call": "POST /servicemesh/v1"}
    return {"status": "success", "message": f"service mesh completed", "name":name,"cluster":cluster, "at": datetime.utcnow().isoformat() + "Z"}

def _uninstall(params, dry_run):
    name=params.get("name","istio")
    if dry_run:
        return {"status": "dry_run", "message": f"Would uninstall service mesh '{name}'", "would_call": "DELETE /servicemesh/v1"}
    return {"status": "success", "message": f"service mesh completed", "at": datetime.utcnow().isoformat() + "Z"}

def _configure(params, dry_run):
    name=params.get("name","istio")
    if dry_run:
        return {"status": "dry_run", "message": f"Would configure service mesh '{name}'", "would_call": "POST /servicemesh/v1"}
    return {"status": "success", "message": f"service mesh completed", "name":name, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","istio")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for service mesh '{name}'", "would_call": "GET /servicemesh/v1"}
    return {"status": "success", "message": f"service mesh completed", "name":name,"state":"active","proxies":random.randint(5,50), "at": datetime.utcnow().isoformat() + "Z"}
