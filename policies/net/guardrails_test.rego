package policies.net.guardrails_test

import rego.v1

import data.policies.net.guardrails

test_valid_firewall_allowed if {
    guardrails.allow with input as {
        "intent": "net.firewall",
        "params": {"port": "443", "source": "10.0.0.0/8"}
    }
}

test_ssh_open_to_world_blocked if {
    not guardrails.allow with input as {
        "intent": "net.firewall",
        "params": {"port": "22", "source": "0.0.0.0/0"}
    }
}

test_rdp_open_to_world_blocked if {
    not guardrails.allow with input as {
        "intent": "net.firewall",
        "params": {"port": "3389", "source": "0.0.0.0/0"}
    }
}

test_valid_lb_allowed if {
    guardrails.allow with input as {
        "intent": "net.lb_provision",
        "params": {"type": "application", "scheme": "internal"}
    }
}

test_invalid_lb_type_blocked if {
    not guardrails.allow with input as {
        "intent": "net.lb_provision",
        "params": {"type": "classic"}
    }
}

test_internet_facing_no_waf_blocked if {
    not guardrails.allow with input as {
        "intent": "net.lb_provision",
        "params": {
            "type": "application",
            "scheme": "internet-facing",
            "waf": "disabled"
        }
    }
}

test_open_source_warning if {
    warnings := guardrails.warnings with input as {
        "intent": "net.firewall",
        "params": {"port": "443", "source": "0.0.0.0/0"}
    }
    count(warnings) > 0
}
