package policies.net.guardrails

import rego.v1

BLOCKED_PORTS := {22, 3389}
ALLOWED_LB_TYPES := {"application", "network"}

default allow := true

allow := false if {
    count(violations) > 0
}

violations contains msg if {
    input.intent == "net.firewall"
    port := to_number(input.params.port)
    port in BLOCKED_PORTS
    input.params.source == "0.0.0.0/0"
    msg := sprintf("Opening port %d to 0.0.0.0/0 is not allowed (SSH/RDP must be restricted)", [port])
}

violations contains msg if {
    input.intent == "net.lb_provision"
    lb_type := input.params.type
    not lb_type in ALLOWED_LB_TYPES
    msg := sprintf("Load balancer type '%s' is not allowed. Allowed: %v", [lb_type, ALLOWED_LB_TYPES])
}

violations contains msg if {
    input.intent == "net.lb_provision"
    input.params.scheme == "internet-facing"
    input.params.waf != "enabled"
    msg := "Internet-facing load balancers must have WAF enabled"
}

warnings contains msg if {
    input.intent == "net.firewall"
    input.params.source == "0.0.0.0/0"
    msg := "Rule allows traffic from all sources — consider restricting the source CIDR"
}

warnings contains msg if {
    input.intent == "net.lb_provision"
    input.params.access_logs != "enabled"
    msg := "Access logging is recommended for load balancers"
}
