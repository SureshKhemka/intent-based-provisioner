package policies.compute.guardrails

import rego.v1

ALLOWED_REGIONS := {"ap-south-1", "us-east-1", "us-west-2", "eu-west-1"}

MAX_CPU := 32
MAX_RAM_GB := 128
MAX_STORAGE_GB := 2000

default allow := true

allow := false if {
    count(violations) > 0
}

violations contains msg if {
    region := input.params.region
    not region in ALLOWED_REGIONS
    msg := sprintf("Region '%s' is not allowed. Allowed: %v", [region, ALLOWED_REGIONS])
}

violations contains msg if {
    cpu := to_number(input.params.cpu)
    cpu > MAX_CPU
    msg := sprintf("CPU %d exceeds maximum of %d", [cpu, MAX_CPU])
}

violations contains msg if {
    ram := to_number(input.params.ram_gb)
    ram > MAX_RAM_GB
    msg := sprintf("RAM %dGB exceeds maximum of %dGB", [ram, MAX_RAM_GB])
}

violations contains msg if {
    storage := to_number(input.params.storage_gb)
    storage > MAX_STORAGE_GB
    msg := sprintf("Storage %dGB exceeds maximum of %dGB", [storage, MAX_STORAGE_GB])
}

violations contains msg if {
    input.params.environment in {"prod", "production"}
    input.params.encryption != "aes-256"
    msg := "Production instances must use AES-256 encryption"
}

warnings contains msg if {
    input.params.environment in {"prod", "production"}
    input.params.backup_policy != "daily"
    msg := "Production instances should have daily backups"
}

warnings contains msg if {
    cpu := to_number(input.params.cpu)
    cpu > 16
    msg := sprintf("Large instance requested (%d vCPU) — ensure this is justified", [cpu])
}
