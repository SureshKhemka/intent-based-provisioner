import random
import string
from datetime import datetime


def _fake_id(prefix="api"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "apigw.create": _create,
        "apigw.delete": _delete,
        "apigw.deploy_stage": _deploy_stage,
        "apigw.update_route": _update_route,
        "apigw.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No apigw handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create API gateway '{name}'", "would_call": "POST /apigateway/v1"}
    return {"status": "success", "message": f"API gateway completed", "name":name,"api_id":_fake_id("api"),"endpoint":f"https://{_fake_id("a")}.execute-api.us-east-1.amazonaws.com", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete API gateway '{name}'", "would_call": "DELETE /apigateway/v1"}
    return {"status": "success", "message": f"API gateway completed", "at": datetime.utcnow().isoformat() + "Z"}

def _deploy_stage(params, dry_run):
    name=params.get("name","unknown")
    stage=params.get("stage","prod")
    if dry_run:
        return {"status": "dry_run", "message": f"Would deploy API '{name}' to stage '{stage}'", "would_call": "POST /apigateway/v1"}
    return {"status": "success", "message": f"API to stage completed", "name":name,"stage":stage, "at": datetime.utcnow().isoformat() + "Z"}

def _update_route(params, dry_run):
    name=params.get("name","unknown")
    path=params.get("path","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would update route '{path}' on API '{name}'", "would_call": "POST /apigateway/v1"}
    return {"status": "success", "message": f"API route completed", "name":name,"path":path, "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for API '{name}'", "would_call": "GET /apigateway/v1"}
    return {"status": "success", "message": f"API gateway completed", "stages":["dev","staging","prod"],"routes":random.randint(3,20),"requests_24h":random.randint(1000,500000), "at": datetime.utcnow().isoformat() + "Z"}
