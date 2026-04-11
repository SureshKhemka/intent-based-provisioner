package policies.net.defaults_test

import rego.v1

import data.policies.net.defaults

test_lb_provision_defaults if {
    result := defaults.enrichments with input as {
        "intent": "net.lb_provision",
        "params": {}
    }
    result.ssl_policy == "TLS-1-2-2017-01"
    result.access_logs == "enabled"
    result.waf == "enabled"
}

test_firewall_defaults if {
    result := defaults.enrichments with input as {
        "intent": "net.firewall",
        "params": {}
    }
    result.logging == "enabled"
    result.default_action == "deny"
}

test_dns_no_enrichments if {
    result := defaults.enrichments with input as {
        "intent": "net.dns_create",
        "params": {}
    }
    count(result) == 0
}
