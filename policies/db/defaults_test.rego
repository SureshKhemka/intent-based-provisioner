package policies.db.defaults_test

import rego.v1

import data.policies.db.defaults

test_provision_staging_defaults if {
    result := defaults.enrichments with input as {
        "intent": "db.provision",
        "params": {"environment": "staging"}
    }
    result.encryption == "aes-256"
    result.multi_az == "false"
    result.deletion_protection == "false"
    result.monitoring == "enabled"
}

test_provision_prod_defaults if {
    result := defaults.enrichments with input as {
        "intent": "db.provision",
        "params": {"environment": "prod"}
    }
    result.multi_az == "true"
    result.backup_retention_days == "30"
    result.deletion_protection == "true"
    result.instance == "db.r5.large"
}

test_non_provision_no_enrichments if {
    result := defaults.enrichments with input as {
        "intent": "db.backup",
        "params": {}
    }
    count(result) == 0
}
