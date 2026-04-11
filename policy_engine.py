import json
import os
import requests

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
POLICY_CONFIG_PATH = os.path.join(CONFIG_DIR, "policy_config.json")


def load_policy_config() -> dict:
    with open(POLICY_CONFIG_PATH) as f:
        return json.load(f)


def health_check(config: dict) -> bool:
    """Check if OPA server is reachable."""
    endpoint = config.get("opa_endpoint", "http://localhost:8181")
    health   = config.get("health_path", "/health")
    timeout  = config.get("timeout_seconds", 3)
    try:
        resp = requests.get(f"{endpoint}{health}", timeout=timeout)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def query_policy(policy_path: str, input_data: dict, config: dict) -> dict:
    """
    Query OPA at the given policy path with input_data.

    Returns the OPA result dict on success, or a fallback error dict
    if OPA is unreachable and fallback_on_error is true.
    """
    endpoint = config.get("opa_endpoint", "http://localhost:8181")
    timeout  = config.get("timeout_seconds", 3)
    fallback = config.get("fallback_on_error", True)
    url      = f"{endpoint}/v1/data/{policy_path}"

    try:
        resp = requests.post(
            url,
            json={"input": input_data},
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        if resp.status_code != 200:
            if fallback:
                print(f"  [policy] OPA returned {resp.status_code} for {policy_path} — skipping")
                return {"status": "skipped", "reason": f"OPA returned {resp.status_code}"}
            return {"status": "error", "reason": f"OPA returned {resp.status_code}"}

        body = resp.json()
        return body.get("result", {})

    except requests.RequestException as e:
        if fallback:
            print(f"  [policy] OPA unreachable for {policy_path} — skipping ({e})")
            return {"status": "skipped", "reason": str(e)}
        return {"status": "error", "reason": str(e)}


def get_policy_path(domain: str, policy_type: str, config: dict) -> str:
    """
    Look up the OPA policy path for a domain + type (defaults or guardrails).
    Returns empty string if no mapping exists.
    """
    paths = config.get("policy_paths", {})
    domain_paths = paths.get(domain, {})
    return domain_paths.get(policy_type, "")
