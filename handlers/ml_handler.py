import random
import string
from datetime import datetime


def _fake_id(prefix="ml"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "ml.create_endpoint": _create_endpoint,
        "ml.delete_endpoint": _delete_endpoint,
        "ml.deploy_model": _deploy_model,
        "ml.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No ml handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_endpoint(params, dry_run):
    name=params.get("name",_fake_id())
    instance_type=params.get("instance_type","ml.m5.xlarge")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create ML endpoint '{name}' ({instance_type})", "would_call": "POST /sagemaker/v1/endpoints"}
    return {"status": "success", "message": f"ML endpoint completed", "name":name,"endpoint_arn":f"arn:aws:sagemaker:us-east-1:123456:endpoint/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_endpoint(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete ML endpoint '{name}'", "would_call": "DELETE /sagemaker/v1/endpoints"}
    return {"status": "success", "message": f"ML endpoint completed", "at": datetime.utcnow().isoformat() + "Z"}

def _deploy_model(params, dry_run):
    name=params.get("name","unknown")
    model=params.get("model","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would deploy model '{model}' to endpoint '{name}'", "would_call": "POST /sagemaker/v1/endpoints"}
    return {"status": "success", "message": f"model to endpoint completed", "name":name,"model":model, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for ML endpoint '{name}'", "would_call": "GET /sagemaker/v1/endpoints"}
    return {"status": "success", "message": f"ML endpoint completed", "state":"InService","invocations_5m":random.randint(10,5000),"latency_p99_ms":random.randint(10,500), "at": datetime.utcnow().isoformat() + "Z"}
