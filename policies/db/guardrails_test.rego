package policies.db.guardrails_test

import rego.v1

import data.policies.db.guardrails

test_valid_provision_allowed if {
    guardrails.allow with input as {
        "intent": "db.provision",
        "params": {
            "engine": "postgres",
            "storage_gb": "100",
            "encryption": "aes-256",
            "multi_az": "true",
            "deletion_protection": "true",
            "environment": "prod"
        }
    }
}

test_invalid_engine_blocked if {
    not guardrails.allow with input as {
        "intent": "db.provision",
        "params": {"engine": "oracle", "storage_gb": "100"}
    }
}

test_excessive_storage_blocked if {
    not guardrails.allow with input as {
        "intent": "db.provision",
        "params": {"engine": "postgres", "storage_gb": "10000"}
    }
}

test_prod_no_encryption_blocked if {
    not guardrails.allow with input as {
        "intent": "db.provision",
        "params": {
            "engine": "postgres",
            "storage_gb": "100",
            "encryption": "none",
            "multi_az": "true",
            "deletion_protection": "true",
            "environment": "prod"
        }
    }
}

test_prod_no_multi_az_blocked if {
    not guardrails.allow with input as {
        "intent": "db.provision",
        "params": {
            "engine": "postgres",
            "storage_gb": "100",
            "encryption": "aes-256",
            "multi_az": "false",
            "deletion_protection": "true",
            "environment": "prod"
        }
    }
}

test_staging_no_multi_az_allowed if {
    guardrails.allow with input as {
        "intent": "db.provision",
        "params": {
            "engine": "postgres",
            "storage_gb": "100",
            "multi_az": "false",
            "environment": "staging"
        }
    }
}
