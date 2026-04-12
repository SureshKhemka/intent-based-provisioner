import random
import string
from datetime import datetime


def _fake_id(prefix="fn"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "serverless.deploy": _deploy,
        "serverless.delete": _delete,
        "serverless.invoke": _invoke,
        "serverless.update_config": _update_config,
        "serverless.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No serverless handler for intent: {intent}"}
    return handler(params, dry_run)


def _deploy(params, dry_run):
    name=params.get("name",_fake_id())
    runtime=params.get("runtime","python3.12")
    memory=params.get("memory","256")
    if dry_run:
        return {"status": "dry_run", "message": f"Would deploy function '{name}' (runtime={runtime}, memory={memory}MB)", "would_call": "POST /lambda/v1/functions"}
    return {"status": "success", "message": f"function completed", "name":name,"runtime":runtime,"memory":memory,"function_arn":f"arn:aws:lambda:us-east-1:123456:function:{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete function '{name}'", "would_call": "DELETE /lambda/v1/functions"}
    return {"status": "success", "message": f"function completed", "at": datetime.utcnow().isoformat() + "Z"}

def _invoke(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would invoke function '{name}'", "would_call": "POST /lambda/v1/functions"}
    return {"status": "success", "message": f"function completed", "request_id":_fake_id("req"),"duration_ms":random.randint(50,3000),"status_code":200, "at": datetime.utcnow().isoformat() + "Z"}

def _update_config(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would update config for function '{name}'", "would_call": "PUT /lambda/v1/functions"}
    return {"status": "success", "message": f"function config completed", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for function '{name}'", "would_call": "GET /lambda/v1/functions"}
    return {"status": "success", "message": f"function completed", "state":"Active","runtime":params.get("runtime","python3.12"),"invocations_24h":random.randint(100,100000), "at": datetime.utcnow().isoformat() + "Z"}
