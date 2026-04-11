package policies.k8s.defaults_test

import rego.v1

import data.policies.k8s.defaults

test_deploy_staging_defaults if {
    result := defaults.enrichments with input as {
        "intent": "k8s.deploy",
        "params": {"environment": "staging"}
    }
    result.health_check == "enabled"
    result.rolling_update == "true"
    result.min_replicas == "1"
    result.max_replicas == "5"
}

test_deploy_prod_defaults if {
    result := defaults.enrichments with input as {
        "intent": "k8s.deploy",
        "params": {"environment": "prod"}
    }
    result.min_replicas == "3"
    result.max_replicas == "10"
    result.pod_disruption_budget == "1"
}

test_non_deploy_no_enrichments if {
    result := defaults.enrichments with input as {
        "intent": "k8s.scale",
        "params": {}
    }
    count(result) == 0
}
