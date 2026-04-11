package policies.net.defaults

import rego.v1

default enrichments := {}
default source := "org_standard"

enrichments := result if {
    input.intent == "net.lb_provision"
    result := _lb_provision_defaults
}

enrichments := result if {
    input.intent == "net.firewall"
    result := _firewall_defaults
}

_lb_provision_defaults := {
    "ssl_policy": "TLS-1-2-2017-01",
    "access_logs": "enabled",
    "idle_timeout": "60",
    "waf": "enabled",
    "tags": "managed-by:intent-provisioner"
}

_firewall_defaults := {
    "logging": "enabled",
    "default_action": "deny",
    "tags": "managed-by:intent-provisioner"
}

source := "org_standard"
