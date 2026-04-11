package policies.k8s.guardrails

import rego.v1

MAX_REPLICAS := 50

default allow := true

allow := false if {
    count(violations) > 0
}

violations contains msg if {
    replicas := to_number(input.params.replicas)
    replicas > MAX_REPLICAS
    msg := sprintf("Replica count %d exceeds maximum of %d", [replicas, MAX_REPLICAS])
}

violations contains msg if {
    input.params.environment in {"prod", "production"}
    replicas := to_number(input.params.replicas)
    replicas < 2
    msg := "Production deployments must have at least 2 replicas"
}

violations contains msg if {
    input.intent == "k8s.delete"
    input.params.environment in {"prod", "production"}
    input.params.namespace == "default"
    msg := "Cannot delete resources in the default namespace in production"
}

warnings contains msg if {
    replicas := to_number(input.params.replicas)
    replicas > 20
    msg := sprintf("High replica count (%d) — ensure cluster has capacity", [replicas])
}

warnings contains msg if {
    input.intent == "k8s.deploy"
    not input.params.health_check
    msg := "Deployment without health check is not recommended"
}
