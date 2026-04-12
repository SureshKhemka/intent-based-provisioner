import random
import string
from datetime import datetime


def _fake_id(prefix="wf"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "workflow.create": _create,
        "workflow.delete": _delete,
        "workflow.execute": _execute,
        "workflow.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No workflow handler for intent: {intent}"}
    return handler(params, dry_run)


def _create(params, dry_run):
    name=params.get("name",_fake_id())
    if dry_run:
        return {"status": "dry_run", "message": f"Would create workflow '{name}'", "would_call": "POST /stepfunctions/v1"}
    return {"status": "success", "message": f"workflow completed", "name":name,"workflow_arn":f"arn:aws:states:us-east-1:123456:stateMachine:{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete workflow '{name}'", "would_call": "DELETE /stepfunctions/v1"}
    return {"status": "success", "message": f"workflow completed", "at": datetime.utcnow().isoformat() + "Z"}

def _execute(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would execute workflow '{name}'", "would_call": "POST /stepfunctions/v1"}
    return {"status": "success", "message": f"workflow completed", "execution_id":_fake_id("exec"),"status":"RUNNING", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for workflow '{name}'", "would_call": "GET /stepfunctions/v1"}
    return {"status": "success", "message": f"workflow completed", "state":"ACTIVE","executions_24h":random.randint(0,100),"last_status":"SUCCEEDED", "at": datetime.utcnow().isoformat() + "Z"}
