"""
End-to-end multi-turn session test.

Runs a realistic 5-turn developer session through the full pipeline:
  classify -> apply_defaults -> policy_enrich -> policy_validate -> enforce_confirmation -> execute

Shows verbose output at every stage.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from classify import load_config, build_system_prompt, classify_intent
from policy_enricher import enrich as policy_enrich
from policy_validator import validate as policy_validate
from execution_router import ExecutionRouter

# ── Session: New Microservice Launch ──────────────────────────────────────────

SESSION = [
    {
        "turn": 1,
        "input": "Spin up a 4 core 16GB VM called payments-api in us-east-1 prod",
        "expected_intents": ["compute.provision"],
    },
    {
        "turn": 2,
        "input": "Create a postgres 15 database called payments-db in prod with 200GB storage",
        "expected_intents": ["db.provision"],
    },
    {
        "turn": 3,
        "input": "Set up a Redis cache with 8GB memory for session store",
        "expected_intents": ["cache.provision"],
    },
    {
        "turn": 4,
        "input": "Create an application load balancer for payments-api and add a DNS record payments.myapp.com pointing to it",
        "expected_intents": ["net.lb_provision", "net.dns_create"],
    },
    {
        "turn": 5,
        "input": "Add a CPU alert when it goes above 85% and create a monitoring dashboard for the payments service",
        "expected_intents": ["monitor.create_alert", "monitor.create_dashboard"],
    },
]

DIVIDER = "─" * 80
SECTION = "═" * 80


def print_banner():
    print(f"\n{SECTION}")
    print("  END-TO-END SESSION TEST: New Microservice Launch")
    print(f"{SECTION}")


def print_stage(name):
    print(f"\n  ┌{'─' * 60}┐")
    print(f"  │  {name:<58}│")
    print(f"  └{'─' * 60}┘")


def print_intents_raw(intents):
    """Print raw classification output."""
    for i, item in enumerate(intents, 1):
        intent = item.get("intent", "?")
        conf   = item.get("confidence", 0)
        params = item.get("params", {})
        bar    = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))

        print(f"    [{i}] {intent}  [{bar}] {conf:.2f}")
        if params:
            for k, v in params.items():
                print(f"        {k} = {v}")


def print_defaults(intents):
    """Show which fields came from config/defaults.json."""
    for item in intents:
        defaults = item.get("defaults_applied", [])
        if defaults:
            intent = item.get("intent", "?")
            print(f"    {intent}:")
            for d in defaults:
                print(f"      + {d} = {item['params'].get(d, '?')}  (from defaults.json)")


def print_enrichment(intents):
    """Show which fields were added by OPA policy enrichment."""
    any_enriched = False
    for item in intents:
        policy_applied = item.get("policy_applied", [])
        if policy_applied:
            any_enriched = True
            intent = item.get("intent", "?")
            print(f"    {intent}:")
            for p in policy_applied:
                print(f"      + {p['field']} = {p['value']}  (source: {p['source']})")
    if not any_enriched:
        print("    (no enrichments — domain may not have OPA defaults policy)")


def print_validation(intents):
    """Show OPA guardrails validation results."""
    for item in intents:
        validation = item.get("policy_validation", {})
        intent = item.get("intent", "?")
        allow  = validation.get("allow", True)
        note   = validation.get("note", "")

        if note:
            print(f"    {intent}: {note}")
        elif allow:
            print(f"    {intent}: ✓ ALLOWED")
        else:
            print(f"    {intent}: ✗ BLOCKED")

        for v in validation.get("violations", []):
            print(f"      ✗ {v}")
        for w in validation.get("warnings", []):
            print(f"      ⚠ {w}")


def print_confirmation(intents):
    """Show confirmation requirements."""
    for item in intents:
        intent  = item.get("intent", "?")
        confirm = item.get("requires_confirmation", False)
        if confirm:
            print(f"    {intent}: ⚠ REQUIRES CONFIRMATION")
        else:
            print(f"    {intent}: no confirmation needed")


def print_final_params(intents):
    """Show the fully assembled params with provenance tags."""
    for item in intents:
        intent = item.get("intent", "?")
        params = item.get("params", {})
        defaults_used = set(item.get("defaults_applied", []))
        policy_fields = {p["field"] for p in item.get("policy_applied", [])}

        print(f"    {intent}:")
        for k, v in params.items():
            if k in policy_fields:
                tag = "  ← POLICY"
            elif k in defaults_used:
                tag = "  ← DEFAULT"
            else:
                tag = "  ← USER"
            print(f"      {k:<24} = {str(v):<20} {tag}")


def run_session():
    print_banner()

    # Load config
    taxonomy, defaults, confirmation, model_config = load_config()
    model_name = model_config.get("model", "qwen3:4b")
    system_prompt = build_system_prompt(taxonomy)
    router = ExecutionRouter(dry_run=True)

    print(f"\n  Config loaded:")
    print(f"    Model           : {model_name}")
    print(f"    Intents loaded  : {len(taxonomy['intents'])}")
    print(f"    Defaults for    : {list(defaults.keys())}")
    print(f"    Execution mode  : DRY-RUN")

    # Check OPA
    from policy_engine import health_check, load_policy_config
    policy_config = load_policy_config()
    opa_ok = health_check(policy_config)
    print(f"    OPA status      : {'CONNECTED ✓' if opa_ok else 'UNAVAILABLE'}")

    total_latency = 0

    for step in SESSION:
        turn_num = step["turn"]
        user_input = step["input"]
        expected = step["expected_intents"]

        print(f"\n{SECTION}")
        print(f"  TURN {turn_num}")
        print(f"{SECTION}")
        print(f"\n  User: \"{user_input}\"")
        print(f"  Expected: {expected}")

        # ── STAGE 1: Classification ──────────────────────────────────────────
        print_stage("STAGE 1: LLM Intent Classification")
        start = time.time()
        result = classify_intent(user_input, system_prompt, defaults, confirmation, model_config)
        latency = result.get("latency_s", round(time.time() - start, 2))
        total_latency += latency

        intents = result.get("intents", [])
        compound = result.get("compound", False)

        print(f"    Latency  : {latency}s")
        print(f"    Compound : {compound}")
        print(f"    Intents  : {[i['intent'] for i in intents]}")
        print()
        print_intents_raw(intents)

        # Check accuracy
        actual_names = [i["intent"] for i in intents]
        match = set(actual_names) == set(expected)
        print(f"\n    Intent match: {'✓ CORRECT' if match else '✗ MISMATCH'}")
        if not match:
            missing = set(expected) - set(actual_names)
            extra = set(actual_names) - set(expected)
            if missing:
                print(f"    Missing: {list(missing)}")
            if extra:
                print(f"    Extra  : {list(extra)}")

        # ── STAGE 2: Defaults Applied ────────────────────────────────────────
        print_stage("STAGE 2: Config Defaults Applied")
        print_defaults(intents)

        # ── STAGE 3: Policy Enrichment ───────────────────────────────────────
        print_stage("STAGE 3: OPA Policy Enrichment")
        intents = policy_enrich(intents)
        result["intents"] = intents
        print_enrichment(intents)

        # ── STAGE 4: Policy Validation ───────────────────────────────────────
        print_stage("STAGE 4: OPA Policy Validation (Guardrails)")
        intents = policy_validate(intents)
        result["intents"] = intents
        print_validation(intents)

        # ── STAGE 5: Confirmation Check ──────────────────────────────────────
        print_stage("STAGE 5: Confirmation Rules")
        print_confirmation(intents)

        # ── Final assembled params ───────────────────────────────────────────
        print_stage("FINAL: Assembled Params with Provenance")
        print_final_params(intents)

        # ── STAGE 6: Execution ───────────────────────────────────────────────
        print_stage("STAGE 6: Execution (DRY-RUN)")

        blocked = any(
            not item.get("policy_validation", {}).get("allow", True)
            for item in intents
        )
        if blocked:
            print("    ✗ BLOCKED BY POLICY — execution skipped")
        else:
            exec_results = router.execute(result)
            for er in exec_results:
                intent = er["intent"]
                res = er["result"]
                print(f"\n    {intent}:")
                print(f"      status     : {res.get('status')}")
                print(f"      message    : {res.get('message')}")
                if res.get("would_call"):
                    print(f"      would_call : {res['would_call']}")

    # ── Session Summary ──────────────────────────────────────────────────────
    print(f"\n{SECTION}")
    print("  SESSION SUMMARY")
    print(f"{SECTION}")
    print(f"    Turns completed  : {len(SESSION)}")
    print(f"    Total LLM time   : {round(total_latency, 2)}s")
    print(f"    Avg per turn     : {round(total_latency / len(SESSION), 2)}s")
    print(f"    OPA enrichment   : {'active' if opa_ok else 'skipped'}")
    print(f"    OPA validation   : {'active' if opa_ok else 'skipped'}")
    print(f"    Execution mode   : DRY-RUN")
    print(f"{SECTION}\n")


if __name__ == "__main__":
    run_session()
