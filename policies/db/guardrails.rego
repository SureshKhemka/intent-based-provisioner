package policies.db.guardrails

import rego.v1

ALLOWED_ENGINES := {"postgres", "mysql", "mariadb"}

MAX_STORAGE_GB := 5000

default allow := true

allow := false if {
    count(violations) > 0
}

violations contains msg if {
    engine := input.params.engine
    not engine in ALLOWED_ENGINES
    msg := sprintf("Database engine '%s' is not allowed. Allowed: %v", [engine, ALLOWED_ENGINES])
}

violations contains msg if {
    storage := to_number(input.params.storage_gb)
    storage > MAX_STORAGE_GB
    msg := sprintf("Storage %dGB exceeds maximum of %dGB", [storage, MAX_STORAGE_GB])
}

violations contains msg if {
    input.params.environment in {"prod", "production"}
    input.params.encryption != "aes-256"
    msg := "Production databases must use AES-256 encryption"
}

violations contains msg if {
    input.params.environment in {"prod", "production"}
    input.params.multi_az != "true"
    msg := "Production databases must be multi-AZ"
}

violations contains msg if {
    input.params.environment in {"prod", "production"}
    input.params.deletion_protection != "true"
    msg := "Production databases must have deletion protection enabled"
}

warnings contains msg if {
    input.params.environment in {"prod", "production"}
    retention := to_number(input.params.backup_retention_days)
    retention < 14
    msg := sprintf("Backup retention of %d days is below recommended 14 for production", [retention])
}
