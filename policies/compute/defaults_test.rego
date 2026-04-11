package policies.compute.defaults_test

import rego.v1

import data.policies.compute.defaults

test_provision_staging_defaults if {
    result := defaults.enrichments with input as {
        "intent": "compute.provision",
        "params": {"environment": "staging"}
    }
    result.encryption == "aes-256"
    result.backup_policy == "daily"
    result.monitoring == "enabled"
    result.instance_type == "t3.medium"
}

test_provision_prod_defaults if {
    result := defaults.enrichments with input as {
        "intent": "compute.provision",
        "params": {"environment": "prod"}
    }
    result.instance_type == "c5.xlarge"
    result.encryption == "aes-256"
}

test_non_provision_no_enrichments if {
    result := defaults.enrichments with input as {
        "intent": "compute.terminate",
        "params": {}
    }
    count(result) == 0
}

test_source_is_org_standard if {
    result := defaults.source with input as {
        "intent": "compute.provision",
        "params": {"environment": "staging"}
    }
    result == "org_standard"
}
