package policies.k8s.guardrails_test

import rego.v1

import data.policies.k8s.guardrails

test_valid_deploy_allowed if {
    guardrails.allow with input as {
        "intent": "k8s.deploy",
        "params": {"replicas": "3", "environment": "staging"}
    }
}

test_excessive_replicas_blocked if {
    not guardrails.allow with input as {
        "intent": "k8s.deploy",
        "params": {"replicas": "100", "environment": "staging"}
    }
}

test_prod_single_replica_blocked if {
    not guardrails.allow with input as {
        "intent": "k8s.deploy",
        "params": {"replicas": "1", "environment": "prod"}
    }
}

test_delete_prod_default_ns_blocked if {
    not guardrails.allow with input as {
        "intent": "k8s.delete",
        "params": {"environment": "prod", "namespace": "default"}
    }
}

test_high_replicas_warning if {
    warnings := guardrails.warnings with input as {
        "intent": "k8s.deploy",
        "params": {"replicas": "30", "environment": "staging"}
    }
    count(warnings) > 0
}
