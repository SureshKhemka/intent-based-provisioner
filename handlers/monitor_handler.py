import random
import string
from datetime import datetime


def _fake_id(prefix="alarm"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "monitor.create_alert": _create_alert,
        "monitor.delete_alert": _delete_alert,
        "monitor.create_dashboard": _create_dashboard,
        "monitor.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No monitor handler for intent: {intent}"}
    return handler(params, dry_run)


def _create_alert(params, dry_run):
    name=params.get("name",_fake_id("alarm"))
    metric=params.get("metric","CPUUtilization")
    threshold=params.get("threshold","80%")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create alert '{name}' on {metric} > {threshold}", "would_call": "POST /cloudwatch/v1"}
    return {"status": "success", "message": f"alert completed", "name":name,"alarm_arn":f"arn:aws:cloudwatch:us-east-1:123456:alarm:{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _delete_alert(params, dry_run):
    name=params.get("name","unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete alert '{name}'", "would_call": "DELETE /cloudwatch/v1"}
    return {"status": "success", "message": f"alert completed", "at": datetime.utcnow().isoformat() + "Z"}

def _create_dashboard(params, dry_run):
    name=params.get("name",_fake_id("dash"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would create dashboard '{name}'", "would_call": "POST /cloudwatch/v1"}
    return {"status": "success", "message": f"dashboard completed", "name":name,"dashboard_arn":f"arn:aws:cloudwatch::123456:dashboard/{name}", "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    name=params.get("name","")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch monitoring status", "would_call": "GET /cloudwatch/v1"}
    return {"status": "success", "message": f"monitoring completed", "alarms_ok":random.randint(5,30),"alarms_alarm":random.randint(0,3),"dashboards":random.randint(1,10), "at": datetime.utcnow().isoformat() + "Z"}
