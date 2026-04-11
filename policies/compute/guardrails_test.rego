package policies.compute.guardrails_test

import rego.v1

import data.policies.compute.guardrails

test_valid_provision_allowed if {
    guardrails.allow with input as {
        "intent": "compute.provision",
        "params": {
            "region": "ap-south-1",
            "cpu": "4",
            "ram_gb": "16",
            "storage_gb": "100",
            "encryption": "aes-256",
            "environment": "staging"
        }
    }
}

test_invalid_region_blocked if {
    not guardrails.allow with input as {
        "intent": "compute.provision",
        "params": {"region": "cn-north-1", "cpu": "2", "ram_gb": "8", "storage_gb": "50"}
    }
}

test_excessive_cpu_blocked if {
    not guardrails.allow with input as {
        "intent": "compute.provision",
        "params": {"region": "us-east-1", "cpu": "64", "ram_gb": "8", "storage_gb": "50"}
    }
}

test_excessive_ram_blocked if {
    not guardrails.allow with input as {
        "intent": "compute.provision",
        "params": {"region": "us-east-1", "cpu": "4", "ram_gb": "256", "storage_gb": "50"}
    }
}

test_prod_without_encryption_blocked if {
    not guardrails.allow with input as {
        "intent": "compute.provision",
        "params": {
            "region": "us-east-1",
            "cpu": "4",
            "ram_gb": "16",
            "storage_gb": "100",
            "encryption": "none",
            "environment": "prod"
        }
    }
}

test_large_cpu_warning if {
    warnings := guardrails.warnings with input as {
        "intent": "compute.provision",
        "params": {"region": "us-east-1", "cpu": "24", "ram_gb": "64", "storage_gb": "100"}
    }
    count(warnings) > 0
}

test_no_violations_empty if {
    violations := guardrails.violations with input as {
        "intent": "compute.provision",
        "params": {
            "region": "ap-south-1",
            "cpu": "2",
            "ram_gb": "8",
            "storage_gb": "50",
            "encryption": "aes-256",
            "environment": "staging"
        }
    }
    count(violations) == 0
}
