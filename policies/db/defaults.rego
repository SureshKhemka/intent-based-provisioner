package policies.db.defaults

import rego.v1

default enrichments := {}
default source := "org_standard"

enrichments := result if {
    input.intent == "db.provision"
    result := _db_provision_defaults
}

_db_provision_defaults := defaults if {
    defaults := object.union(
        _base_db_defaults,
        _env_specific_defaults
    )
}

_base_db_defaults := {
    "encryption": "aes-256",
    "backup_retention_days": "7",
    "monitoring": "enabled",
    "auto_minor_upgrade": "true",
    "tags": "managed-by:intent-provisioner"
}

_env_specific_defaults := {
    "multi_az": "true",
    "backup_retention_days": "30",
    "deletion_protection": "true",
    "instance": "db.r5.large"
} if {
    input.params.environment in {"prod", "production"}
} else := {
    "multi_az": "false",
    "deletion_protection": "false"
}

source := "org_standard"
