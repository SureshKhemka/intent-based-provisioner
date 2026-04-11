package policies.compute.defaults

import rego.v1

default enrichments := {}
default source := "org_standard"

enrichments := result if {
    input.intent == "compute.provision"
    result := _compute_provision_defaults
}

_compute_provision_defaults := defaults if {
    defaults := object.union(
        _base_compute_defaults,
        _env_specific_defaults
    )
}

_base_compute_defaults := {
    "encryption": "aes-256",
    "backup_policy": "daily",
    "monitoring": "enabled",
    "tags": "managed-by:intent-provisioner"
}

_env_specific_defaults := {"instance_type": "c5.xlarge"} if {
    input.params.environment == "prod"
} else := {"instance_type": "c5.xlarge"} if {
    input.params.environment == "production"
} else := {"instance_type": "t3.medium"}

source := "org_standard"
