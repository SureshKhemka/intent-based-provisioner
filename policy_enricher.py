from policy_engine import load_policy_config, query_policy, get_policy_path


def enrich(intents: list) -> list:
    """
    Query OPA defaults policies to fill org-standard values into params
    the user didn't specify. User-specified params always take precedence.

    Adds 'policy_applied' list to each intent's params tracking provenance.
    """
    config = load_policy_config()

    for item in intents:
        intent_name = item.get("intent", "")
        domain      = intent_name.split(".")[0]
        params      = item.get("params", {})

        policy_path = get_policy_path(domain, "defaults", config)
        if not policy_path:
            continue

        input_data = {
            "intent": intent_name,
            "params": params
        }

        result = query_policy(policy_path, input_data, config)

        if result.get("status") == "skipped":
            continue

        enrichments = result.get("enrichments", {})
        source      = result.get("source", "org_standard")

        policy_applied = item.get("policy_applied", [])

        for key, value in enrichments.items():
            if key not in params:
                params[key] = value
                policy_applied.append({
                    "field":  key,
                    "value":  value,
                    "source": source
                })

        item["params"]          = params
        item["policy_applied"]  = policy_applied

    return intents
