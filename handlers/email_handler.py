import random
import string
from datetime import datetime


def _fake_id(prefix="ses"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "email.configure": _configure,
        "email.send": _send,
        "email.verify_domain": _verify_domain,
        "email.status": _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No email handler for intent: {intent}"}
    return handler(params, dry_run)


def _configure(params, dry_run):
    domain=params.get("domain",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would configure email service for '{domain}'", "would_call": "POST /ses/v1"}
    return {"status": "success", "message": f"email service completed", "domain":domain, "at": datetime.utcnow().isoformat() + "Z"}

def _send(params, dry_run):
    to=params.get("to","unknown")
    sender=params.get("from",params.get("sender","noreply@example.com"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would send email from '{sender}' to '{to}'", "would_call": "POST /ses/v1"}
    return {"status": "success", "message": f"email completed", "message_id":_fake_id("msg"), "at": datetime.utcnow().isoformat() + "Z"}

def _verify_domain(params, dry_run):
    domain=params.get("domain",params.get("name","unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would verify domain '{domain}' for email sending", "would_call": "POST /ses/v1"}
    return {"status": "success", "message": f"domain completed", "domain":domain,"verification_token":_fake_id("tok"), "at": datetime.utcnow().isoformat() + "Z"}

def _status(params, dry_run):
    domain=params.get("domain",params.get("name",""))
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch email service status", "would_call": "GET /ses/v1"}
    return {"status": "success", "message": f"email service completed", "send_quota_24h":50000,"sent_24h":random.randint(100,10000),"bounce_rate":f"{round(random.uniform(0,5),1)}%", "at": datetime.utcnow().isoformat() + "Z"}
