import random
import string
from datetime import datetime


def _fake_id(prefix: str = "pod") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{prefix}-{suffix}"


def handle(intent: str, params: dict, dry_run: bool) -> dict:
    handler = {
        "k8s.deploy":    _deploy,
        "k8s.scale":     _scale,
        "k8s.rollback":  _rollback,
        "k8s.status":    _status,
        "k8s.logs":      _logs,
        "k8s.exec":      _exec,
        "k8s.delete":    _delete,
    }.get(intent)

    if not handler:
        return {"status": "error", "message": f"No k8s handler for intent: {intent}"}

    return handler(params, dry_run)


def _deploy(params: dict, dry_run: bool) -> dict:
    service  = params.get("service", "unknown-service")
    image    = params.get("image", f"{service}:latest")
    replicas = params.get("replicas", "2")
    env      = params.get("environment", "staging")
    ns       = params.get("namespace", env)

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would deploy '{service}' image={image} replicas={replicas} "
                          f"to namespace '{ns}'",
            "would_call": "kubectl apply -f deployment.yaml"
        }

    return {
        "status":      "success",
        "message":     f"Deployment '{service}' rolled out successfully",
        "service":     service,
        "image":       image,
        "replicas":    replicas,
        "namespace":   ns,
        "pods":        [_fake_id(service) for _ in range(int(replicas))],
        "deployed_at": datetime.utcnow().isoformat() + "Z"
    }


def _scale(params: dict, dry_run: bool) -> dict:
    service  = params.get("service", "unknown-service")
    replicas = params.get("replicas", "3")
    ns       = params.get("namespace", params.get("environment", "staging"))

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would scale '{service}' to {replicas} replicas in namespace '{ns}'",
            "would_call": f"kubectl scale deployment/{service} --replicas={replicas} -n {ns}"
        }

    return {
        "status":    "success",
        "message":   f"'{service}' scaled to {replicas} replicas",
        "service":   service,
        "replicas":  replicas,
        "namespace": ns,
        "pods":      [_fake_id(service) for _ in range(int(replicas))],
        "scaled_at": datetime.utcnow().isoformat() + "Z"
    }


def _rollback(params: dict, dry_run: bool) -> dict:
    service  = params.get("service", "unknown-service")
    version  = params.get("version", "previous")
    ns       = params.get("namespace", params.get("environment", "staging"))

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would rollback '{service}' to version '{version}' in namespace '{ns}'",
            "would_call": f"kubectl rollout undo deployment/{service} -n {ns}"
        }

    return {
        "status":       "success",
        "message":      f"'{service}' rolled back to {version}",
        "service":      service,
        "rolled_back_to": version,
        "namespace":    ns,
        "rolled_back_at": datetime.utcnow().isoformat() + "Z"
    }


def _status(params: dict, dry_run: bool) -> dict:
    service = params.get("service", "unknown-service")
    ns      = params.get("namespace", params.get("environment", "staging"))

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would fetch status for '{service}' in namespace '{ns}'",
            "would_call": f"kubectl get deployment/{service} -n {ns}"
        }

    replicas = random.randint(2, 5)
    return {
        "status":            "success",
        "service":           service,
        "namespace":         ns,
        "desired_replicas":  replicas,
        "ready_replicas":    replicas,
        "available_replicas": replicas,
        "image":             f"{service}:v{random.randint(1,10)}.{random.randint(0,9)}",
        "age_hrs":           random.randint(1, 240),
        "checked_at":        datetime.utcnow().isoformat() + "Z"
    }


def _logs(params: dict, dry_run: bool) -> dict:
    service = params.get("service", "unknown-service")
    ns      = params.get("namespace", params.get("environment", "staging"))
    tail    = params.get("lines", "50")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would tail {tail} lines of logs for '{service}' in namespace '{ns}'",
            "would_call": f"kubectl logs deployment/{service} --tail={tail} -n {ns}"
        }

    fake_logs = [
        f"[{datetime.utcnow().isoformat()}] INFO  Starting {service}",
        f"[{datetime.utcnow().isoformat()}] INFO  Connected to database",
        f"[{datetime.utcnow().isoformat()}] INFO  Listening on :8080",
        f"[{datetime.utcnow().isoformat()}] INFO  Health check passed",
        f"[{datetime.utcnow().isoformat()}] DEBUG Processing request GET /health",
    ]

    return {
        "status":  "success",
        "service": service,
        "lines":   fake_logs
    }


def _exec(params: dict, dry_run: bool) -> dict:
    service = params.get("service", "unknown-service")
    ns      = params.get("namespace", params.get("environment", "staging"))

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would open shell in a pod of '{service}' in namespace '{ns}'",
            "would_call": f"kubectl exec -it {_fake_id(service)} -n {ns} -- /bin/sh"
        }

    return {
        "status":   "success",
        "message":  f"Shell session opened in pod '{_fake_id(service)}'",
        "note":     "In production this would open an interactive shell session"
    }


def _delete(params: dict, dry_run: bool) -> dict:
    service = params.get("service", params.get("namespace", "unknown"))
    ns      = params.get("namespace", params.get("environment", "staging"))

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would delete deployment '{service}' from namespace '{ns}' — irreversible",
            "would_call": f"kubectl delete deployment/{service} -n {ns}"
        }

    return {
        "status":     "success",
        "message":    f"Deployment '{service}' deleted from namespace '{ns}'",
        "service":    service,
        "namespace":  ns,
        "deleted_at": datetime.utcnow().isoformat() + "Z"
    }
