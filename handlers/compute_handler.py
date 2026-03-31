import random
import string
from datetime import datetime


def _fake_id(prefix: str) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def _fake_ip() -> str:
    return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def handle(intent: str, params: dict, dry_run: bool) -> dict:
    handler = {
        "compute.provision":   _provision,
        "compute.terminate":   _terminate,
        "compute.resize":      _resize,
        "compute.start_stop":  _start_stop,
        "compute.status":      _status,
        "compute.list":        _list,
    }.get(intent)

    if not handler:
        return {"status": "error", "message": f"No compute handler for intent: {intent}"}

    return handler(params, dry_run)


def _provision(params: dict, dry_run: bool) -> dict:
    name    = params.get("name", _fake_id("vm"))
    cpu     = params.get("cpu", "2")
    ram     = params.get("ram_gb", "8")
    disk    = params.get("storage_gb", "50")
    os_img  = params.get("os", "ubuntu-22.04")
    region  = params.get("region", "ap-south-1")
    env     = params.get("environment", "staging")

    if dry_run:
        return {
            "status":  "dry_run",
            "message": f"Would provision VM '{name}' ({cpu} vCPU / {ram}GB RAM / {disk}GB disk) "
                       f"running {os_img} in {region} [{env}]",
            "would_call": "POST /compute/v1/instances",
            "payload": params
        }

    return {
        "status":      "success",
        "message":     f"VM '{name}' provisioned successfully",
        "resource_id": _fake_id("i"),
        "name":        name,
        "private_ip":  _fake_ip(),
        "cpu":         cpu,
        "ram_gb":      ram,
        "storage_gb":  disk,
        "os":          os_img,
        "region":      region,
        "environment": env,
        "state":       "running",
        "created_at":  datetime.utcnow().isoformat() + "Z"
    }


def _terminate(params: dict, dry_run: bool) -> dict:
    name = params.get("name", params.get("resource_id", "unknown"))

    if dry_run:
        return {
            "status":  "dry_run",
            "message": f"Would terminate VM '{name}' — this is irreversible",
            "would_call": "DELETE /compute/v1/instances/{id}"
        }

    return {
        "status":       "success",
        "message":      f"VM '{name}' terminated",
        "resource_id":  params.get("resource_id", _fake_id("i")),
        "name":         name,
        "state":        "terminated",
        "terminated_at": datetime.utcnow().isoformat() + "Z"
    }


def _resize(params: dict, dry_run: bool) -> dict:
    name = params.get("name", "unknown")
    cpu  = params.get("cpu", "")
    ram  = params.get("ram_gb", "")

    changes = []
    if cpu:
        changes.append(f"cpu → {cpu}")
    if ram:
        changes.append(f"ram → {ram}GB")

    if dry_run:
        return {
            "status":  "dry_run",
            "message": f"Would resize VM '{name}': {', '.join(changes) or 'no changes specified'}",
            "would_call": "PATCH /compute/v1/instances/{id}"
        }

    return {
        "status":     "success",
        "message":    f"VM '{name}' resized — restart required for CPU/RAM changes",
        "name":       name,
        "new_config": {k: params[k] for k in ("cpu", "ram_gb", "storage_gb") if k in params},
        "resized_at": datetime.utcnow().isoformat() + "Z"
    }


def _start_stop(params: dict, dry_run: bool) -> dict:
    name   = params.get("name", "unknown")
    action = params.get("action", "start").lower()

    if dry_run:
        return {
            "status":  "dry_run",
            "message": f"Would {action} VM '{name}'",
            "would_call": f"POST /compute/v1/instances/{{id}}/{action}"
        }

    return {
        "status":  "success",
        "message": f"VM '{name}' {action}ed successfully",
        "name":    name,
        "state":   "running" if action == "start" else "stopped",
        "at":      datetime.utcnow().isoformat() + "Z"
    }


def _status(params: dict, dry_run: bool) -> dict:
    name = params.get("name", "unknown")

    if dry_run:
        return {
            "status":  "dry_run",
            "message": f"Would fetch status for VM '{name}'",
            "would_call": "GET /compute/v1/instances/{id}"
        }

    return {
        "status":      "success",
        "name":        name,
        "state":       "running",
        "private_ip":  _fake_ip(),
        "cpu_usage":   f"{random.randint(5, 80)}%",
        "ram_usage":   f"{random.randint(10, 90)}%",
        "uptime_hrs":  random.randint(1, 720),
        "checked_at":  datetime.utcnow().isoformat() + "Z"
    }


def _list(params: dict, dry_run: bool) -> dict:
    env = params.get("environment", "all")

    if dry_run:
        return {
            "status":  "dry_run",
            "message": f"Would list VMs in environment: {env}",
            "would_call": "GET /compute/v1/instances"
        }

    fake_vms = [
        {"name": _fake_id("vm"), "state": "running",  "ip": _fake_ip(), "env": env},
        {"name": _fake_id("vm"), "state": "running",  "ip": _fake_ip(), "env": env},
        {"name": _fake_id("vm"), "state": "stopped",  "ip": _fake_ip(), "env": env},
    ]

    return {
        "status": "success",
        "count":  len(fake_vms),
        "vms":    fake_vms
    }
