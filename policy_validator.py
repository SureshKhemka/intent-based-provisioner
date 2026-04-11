from policy_engine import load_policy_config, query_policy, get_policy_path


def validate(intents: list) -> list:
    """
    Query OPA guardrails policies to validate fully-enriched params.

    Sets 'policy_validation' on each intent with:
      - allow: bool
      - violations: list of blocking issues
      - warnings: list of non-blocking advisories
    """
    config = load_policy_config()

    for item in intents:
        intent_name = item.get("intent", "")
        domain      = intent_name.split(".")[0]
        params      = item.get("params", {})

        policy_path = get_policy_path(domain, "guardrails", config)
        if not policy_path:
            item["policy_validation"] = {
                "allow": True, "violations": [], "warnings": []
            }
            continue

        input_data = {
            "intent": intent_name,
            "params": params
        }

        result = query_policy(policy_path, input_data, config)

        if result.get("status") == "skipped":
            item["policy_validation"] = {
                "allow": True, "violations": [], "warnings": [],
                "note": "OPA unavailable — policy check skipped"
            }
            continue

        item["policy_validation"] = {
            "allow":      result.get("allow", True),
            "violations": result.get("violations", []),
            "warnings":   result.get("warnings", [])
        }

    return intents


def print_policy_result(item: dict):
    """Print policy validation outcome for a single intent."""
    validation = item.get("policy_validation", {})
    intent     = item.get("intent", "unknown")

    if not validation:
        return

    if validation.get("note"):
        print(f"  [policy] {intent}: {validation['note']}")

    for warning in validation.get("warnings", []):
        print(f"  [policy] {intent}: WARNING — {warning}")

    if not validation.get("allow", True):
        print(f"  [policy] {intent}: BLOCKED by policy")
        for v in validation.get("violations", []):
            print(f"           ✗ {v}")
