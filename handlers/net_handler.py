import random
import string
from datetime import datetime


def _fake_id(prefix: str = "res") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent: str, params: dict, dry_run: bool) -> dict:
    handler = {
        "net.dns_create":   _dns_create,
        "net.dns_delete":   _dns_delete,
        "net.lb_provision": _lb_provision,
        "net.lb_update":    _lb_update,
        "net.firewall":     _firewall,
        "net.status":       _status,
    }.get(intent)

    if not handler:
        return {"status": "error", "message": f"No net handler for intent: {intent}"}

    return handler(params, dry_run)


def _dns_create(params: dict, dry_run: bool) -> dict:
    hostname = params.get("hostname", "unknown.example.com")
    target   = params.get("target", "")
    ttl      = params.get("ttl", "300")
    rtype    = params.get("type", "A")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would create {rtype} record: {hostname} → {target} (TTL {ttl}s)",
            "would_call": "POST /route53/v1/records"
        }

    return {
        "status":     "success",
        "message":    f"DNS record created: {hostname} → {target}",
        "record_id":  _fake_id("dns"),
        "hostname":   hostname,
        "target":     target,
        "type":       rtype,
        "ttl":        ttl,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }


def _dns_delete(params: dict, dry_run: bool) -> dict:
    hostname = params.get("hostname", "unknown.example.com")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would delete DNS record for '{hostname}'",
            "would_call": "DELETE /route53/v1/records/{id}"
        }

    return {
        "status":     "success",
        "message":    f"DNS record for '{hostname}' deleted",
        "hostname":   hostname,
        "deleted_at": datetime.utcnow().isoformat() + "Z"
    }


def _lb_provision(params: dict, dry_run: bool) -> dict:
    name   = params.get("name", _fake_id("lb"))
    lbtype = params.get("type", "application")
    scheme = params.get("scheme", "internal")
    env    = params.get("environment", "staging")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would provision {scheme} {lbtype} load balancer '{name}' in [{env}]",
            "would_call": "POST /elb/v1/load-balancers"
        }

    return {
        "status":      "success",
        "message":     f"Load balancer '{name}' provisioned",
        "name":        name,
        "lb_id":       _fake_id("lb"),
        "type":        lbtype,
        "scheme":      scheme,
        "dns_name":    f"{name}.{_fake_id('elb')}.ap-south-1.elb.amazonaws.com",
        "environment": env,
        "state":       "active",
        "created_at":  datetime.utcnow().isoformat() + "Z"
    }


def _lb_update(params: dict, dry_run: bool) -> dict:
    name = params.get("name", "unknown")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would update load balancer '{name}' with params: {params}",
            "would_call": "PATCH /elb/v1/load-balancers/{id}"
        }

    return {
        "status":     "success",
        "message":    f"Load balancer '{name}' updated",
        "name":       name,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }


def _firewall(params: dict, dry_run: bool) -> dict:
    port     = params.get("port", "unknown")
    action   = params.get("action", "open")
    protocol = params.get("protocol", "tcp")
    env      = params.get("environment", "staging")
    source   = params.get("source", "0.0.0.0/0")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would {action} port {port}/{protocol} from {source} in [{env}]",
            "would_call": "POST /firewall/v1/rules"
        }

    return {
        "status":     "success",
        "message":    f"Firewall rule applied: port {port}/{protocol} {action}ed",
        "rule_id":    _fake_id("sg"),
        "port":       port,
        "protocol":   protocol,
        "action":     action,
        "source":     source,
        "environment": env,
        "applied_at": datetime.utcnow().isoformat() + "Z"
    }


def _status(params: dict, dry_run: bool) -> dict:
    env = params.get("environment", "all")

    if dry_run:
        return {
            "status":     "dry_run",
            "message":    f"Would fetch network status for environment: {env}",
            "would_call": "GET /network/v1/status"
        }

    return {
        "status":      "success",
        "environment": env,
        "load_balancers": random.randint(1, 5),
        "dns_records":    random.randint(10, 50),
        "firewall_rules": random.randint(5, 30),
        "checked_at":     datetime.utcnow().isoformat() + "Z"
    }
