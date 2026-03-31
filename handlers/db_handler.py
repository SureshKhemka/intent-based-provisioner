import random
import string
from datetime import datetime


def _fake_id(prefix: str = "db") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def _fake_endpoint(name: str) -> str:
    return f"{name}.cluster.{_fake_id('rds')}.ap-south-1.rds.amazonaws.com"


def handle(intent: str, params: dict, dry_run: bool) -> dict:
    handler = {
        "db.provision": _provision,
        "db.delete":    _delete,
        "db.resize":    _resize,
        "db.backup":    _backup,
        "db.restore":   _restore,
        "db.access":    _access,
        "db.status":    _status,
    }.get(intent)

    if not handler:
        return {"status": "error", "message": f"No db handler for intent: {intent}"}

    return handler(params, dry_run)


def _provision(params: dict, dry_run: bool) -> dict:
    name    = params.get("name", _fake_id("db"))
    engine  = params.get("engine", "postgres")
    version = params.get("version", "15")
    storage = params.get("storage_gb", "100")
    inst    = params.get("instance", "db.t3.medium")
    env     = params.get("environment", "staging")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would provision {engine} {version} instance '{name}' "
                          f"({inst}, {storage}GB) in [{env}]",
            "would_call": "POST /rds/v1/instances"
        }

    return {
        "status":       "success",
        "message":      f"Database '{name}' provisioned successfully",
        "name":         name,
        "engine":       engine,
        "version":      version,
        "instance":     inst,
        "storage_gb":   storage,
        "environment":  env,
        "endpoint":     _fake_endpoint(name),
        "port":         5432 if engine == "postgres" else 3306,
        "state":        "available",
        "created_at":   datetime.utcnow().isoformat() + "Z"
    }


def _delete(params: dict, dry_run: bool) -> dict:
    name = params.get("name", "unknown")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would delete database '{name}' — this is irreversible and deletes all data",
            "would_call": "DELETE /rds/v1/instances/{id}"
        }

    return {
        "status":     "success",
        "message":    f"Database '{name}' deleted",
        "name":       name,
        "deleted_at": datetime.utcnow().isoformat() + "Z"
    }


def _resize(params: dict, dry_run: bool) -> dict:
    name    = params.get("name", "unknown")
    inst    = params.get("instance", "")
    storage = params.get("storage_gb", "")

    changes = []
    if inst:    changes.append(f"instance → {inst}")
    if storage: changes.append(f"storage → {storage}GB")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would resize database '{name}': {', '.join(changes) or 'no changes specified'}",
            "would_call": "PATCH /rds/v1/instances/{id}"
        }

    return {
        "status":     "success",
        "message":    f"Database '{name}' resize initiated — brief downtime expected",
        "name":       name,
        "changes":    changes,
        "resized_at": datetime.utcnow().isoformat() + "Z"
    }


def _backup(params: dict, dry_run: bool) -> dict:
    name = params.get("name", "unknown")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would take a snapshot of database '{name}'",
            "would_call": "POST /rds/v1/instances/{id}/snapshots"
        }

    snapshot_id = _fake_id("snap")
    return {
        "status":      "success",
        "message":     f"Snapshot of '{name}' created",
        "snapshot_id": snapshot_id,
        "source_db":   name,
        "size_gb":     random.randint(10, 200),
        "created_at":  datetime.utcnow().isoformat() + "Z"
    }


def _restore(params: dict, dry_run: bool) -> dict:
    name        = params.get("name", "unknown")
    snapshot_id = params.get("snapshot_id", "latest")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would restore database '{name}' from snapshot '{snapshot_id}'",
            "would_call": "POST /rds/v1/instances/{id}/restore"
        }

    return {
        "status":       "success",
        "message":      f"Database '{name}' restored from snapshot '{snapshot_id}'",
        "name":         name,
        "snapshot_id":  snapshot_id,
        "restored_at":  datetime.utcnow().isoformat() + "Z",
        "note":         "Restore complete — verify data integrity before resuming traffic"
    }


def _access(params: dict, dry_run: bool) -> dict:
    name   = params.get("name", "unknown")
    user   = params.get("user", "unknown")
    action = params.get("action", "grant")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would {action} access for user '{user}' on database '{name}'",
            "would_call": "POST /rds/v1/instances/{id}/users"
        }

    return {
        "status":   "success",
        "message":  f"Access {action}ed for '{user}' on database '{name}'",
        "db":       name,
        "user":     user,
        "action":   action,
        "at":       datetime.utcnow().isoformat() + "Z"
    }


def _status(params: dict, dry_run: bool) -> dict:
    name = params.get("name", "unknown")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would fetch status for database '{name}'",
            "would_call": "GET /rds/v1/instances/{id}"
        }

    return {
        "status":       "success",
        "name":         name,
        "state":        "available",
        "connections":  random.randint(5, 120),
        "cpu_usage":    f"{random.randint(5, 60)}%",
        "storage_used": f"{random.randint(10, 90)}%",
        "endpoint":     _fake_endpoint(name),
        "checked_at":   datetime.utcnow().isoformat() + "Z"
    }
