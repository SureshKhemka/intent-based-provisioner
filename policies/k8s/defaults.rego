package policies.k8s.defaults

import rego.v1

default enrichments := {}
default source := "org_standard"

enrichments := result if {
    input.intent == "k8s.deploy"
    result := _k8s_deploy_defaults
}

_k8s_deploy_defaults := defaults if {
    defaults := object.union(
        _base_k8s_defaults,
        _env_specific_defaults
    )
}

_base_k8s_defaults := {
    "resource_limits": "cpu:500m,memory:512Mi",
    "health_check": "enabled",
    "rolling_update": "true",
    "labels": "managed-by:intent-provisioner"
}

_env_specific_defaults := {
    "min_replicas": "3",
    "max_replicas": "10",
    "pod_disruption_budget": "1"
} if {
    input.params.environment in {"prod", "production"}
} else := {
    "min_replicas": "1",
    "max_replicas": "5",
    "pod_disruption_budget": "0"
}

source := "org_standard"
