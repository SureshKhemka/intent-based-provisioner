import json
import os

from classify import load_config, build_system_prompt, classify_intent
from context_manager import ContextManager
from execution_router import ExecutionRouter
from policy_enricher import enrich as policy_enrich
from policy_validator import validate as policy_validate, print_policy_result
from policy_engine import health_check, load_policy_config
from judge import (
    load_judge_config, evaluate as judge_evaluate,
    log_evaluation as judge_log, print_evaluation as judge_print,
)

CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "context")


def select_team() -> str:
    os.makedirs(CONTEXT_DIR, exist_ok=True)
    existing = [
        f.replace(".json", "")
        for f in os.listdir(CONTEXT_DIR)
        if f.endswith(".json")
    ]
    print("\n  Available team contexts:")
    if existing:
        for name in existing:
            print(f"    {name}")
    else:
        print("    (none yet)")
    team = input("\n  Enter team name (or press Enter for 'default'): ").strip()
    return team if team else "default"


def print_classification(result: dict):
    intents  = result.get("intents", [])
    compound = result.get("compound", False)
    latency  = result.get("latency_s", 0)

    if compound:
        print(f"\n  ⚡ Compound request — {len(intents)} intents detected")

    for i, item in enumerate(intents, 1):
        intent        = item.get("intent", "meta.unknown")
        confidence    = item.get("confidence", 0.0)
        params        = item.get("params", {})
        needs_confirm = item.get("requires_confirmation", False)
        defaults_used = set(item.get("defaults_applied", []))

        bar    = "█" * int(confidence * 20) + "░" * (20 - int(confidence * 20))
        prefix = f"  [{i}]" if compound else "  "

        print(f"\n{prefix} Intent     : {intent}", end="")
        if needs_confirm:
            print("  ⚠️  REQUIRES CONFIRMATION", end="")
        print()
        print(f"{prefix} Confidence : [{bar}] {confidence:.2f}")

        if params:
            print(f"{prefix} Params     :")
            policy_fields = {
                p["field"] for p in item.get("policy_applied", [])
            }
            for k, v in params.items():
                if k in policy_fields:
                    tag = " (policy)"
                elif k in defaults_used:
                    tag = " (default)"
                else:
                    tag = ""
                print(f"{prefix}               {k} = {v}{tag}")
        else:
            print(f"{prefix} Params     : (none extracted)")

    print(f"\n  ⏱  {latency}s")


def print_history(history: list):
    if not history:
        print("\n  No history yet.")
        return
    print(f"\n  ── Last {min(len(history), 10)} turns ──────────────────────────")
    for turn in history[-10:]:
        print(f"  {turn['timestamp'][:19]}  {turn['user_input'][:50]}")
        print(f"    → {', '.join(turn['intents'])}")


def print_help(intent_names: list, dry_run: bool):
    mode = "DRY-RUN 🔵" if dry_run else "SIMULATE 🟢"
    print(f"\n  Execution mode : {mode}")
    print(f"\n  Available intents:")
    for name in intent_names:
        print(f"    {name}")
    print(f"\n  Commands:")
    print(f"    help      — show this screen")
    print(f"    history   — show last 10 turns")
    print(f"    clear     — clear context for current team")
    print(f"    switch    — switch to a different team")
    print(f"    mode      — toggle dry-run / simulate mode")
    print(f"    classify  — toggle classify-only (no execution)")
    print(f"    judge     — toggle judge LLM evaluation")
    print(f"    quit      — exit")


def main():
    taxonomy, defaults, confirmation, model_config = load_config()
    intent_names  = [i["name"] for i in taxonomy["intents"]]
    router        = ExecutionRouter(dry_run=True)
    classify_only = False
    model_name    = model_config.get("model", "qwen3:4b")

    policy_config  = load_policy_config()
    opa_available  = health_check(policy_config)

    judge_config   = load_judge_config()
    judge_enabled  = judge_config.get("enabled", False)
    judge_model    = judge_config.get("model", "n/a")

    print("=" * 60)
    print("  Infrastructure Intent-Based Provisioner")
    print(f"  Model      : {model_name} via Ollama")
    print(f"  Intents    : {len(intent_names)} loaded from config")
    print(f"  Exec mode  : DRY-RUN 🔵  (type 'mode' to toggle)")
    if opa_available:
        print(f"  OPA Policy : CONNECTED ✓")
    else:
        print(f"  OPA Policy : UNAVAILABLE (enrichment/validation will be skipped)")
    if judge_enabled:
        print(f"  Judge LLM  : {judge_model} ✓  (type 'judge' to toggle)")
    else:
        print(f"  Judge LLM  : DISABLED  (type 'judge' to toggle)")
    print(f"  Type 'help' for all commands")
    print("=" * 60)

    team    = select_team()
    context = ContextManager(team)
    print(f"\n  Team context loaded:")
    print(context.summary())

    while True:
        try:
            prompt     = "classify> " if classify_only else "> "
            user_input = input(f"\n{prompt}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\nExiting. Goodbye!")
            break

        if user_input.lower() == "help":
            print_help(intent_names, router.dry_run)
            continue

        if user_input.lower() == "history":
            print_history(context.get_history())
            continue

        if user_input.lower() == "clear":
            confirm = input("  Clear context? (yes/no): ").strip()
            if confirm.lower() == "yes":
                context.clear()
            continue

        if user_input.lower() == "switch":
            team    = select_team()
            context = ContextManager(team)
            print(f"\n  Switched to team: {team}")
            print(context.summary())
            continue

        if user_input.lower() == "mode":
            router.set_mode(not router.dry_run)
            continue

        if user_input.lower() == "classify":
            classify_only = not classify_only
            state = "ON (no execution)" if classify_only else "OFF (execution enabled)"
            print(f"\n  Classify-only mode: {state}")
            continue

        if user_input.lower() == "judge":
            judge_enabled = not judge_enabled
            judge_config["enabled"] = judge_enabled
            state = f"ON ({judge_model})" if judge_enabled else "OFF"
            print(f"\n  ⚖️  Judge LLM: {state}")
            continue

        try:
            # Step 1 — resolve references
            resolved = context.resolve_references(user_input)
            if resolved != user_input:
                print(f"\n  🔗 Resolved: \"{resolved}\"")

            # Step 2 — build prompt with context
            context_block = context.build_context_block()
            system_prompt = build_system_prompt(taxonomy, context_block)

            # Step 3 — classify
            result = classify_intent(resolved, system_prompt, defaults, confirmation, model_config)

            # Step 4 — policy enrichment (fill org-standard defaults)
            result["intents"] = policy_enrich(result.get("intents", []))

            # Step 5 — policy validation (check guardrails)
            result["intents"] = policy_validate(result.get("intents", []))

            # Step 6 — show classification + policy results
            print_classification(result)

            # Show policy validation output
            blocked = False
            for item in result.get("intents", []):
                print_policy_result(item)
                validation = item.get("policy_validation", {})
                if not validation.get("allow", True):
                    blocked = True

            # Step 6b — judge LLM evaluation
            if judge_enabled:
                evaluation = judge_evaluate(
                    user_input, result, intent_names,
                    confirmation, judge_config,
                )
                judge_print(evaluation)
                judge_log(user_input, result, evaluation, judge_config)

            # Step 7 — execute (skip if policy blocked)
            if blocked:
                print(f"\n  ── Execution BLOCKED by policy ──────────────────────")
                print(f"     Resolve the violations above before retrying.")
            elif not classify_only:
                print(f"\n  ── Execution ────────────────────────────────────────")
                router.execute(result)

            # Step 8 — save to context
            context.add_turn(user_input, result)

        except Exception as e:
            print(f"\n  Error: {e}")
            print("  Make sure Ollama is running: ollama serve")


if __name__ == "__main__":
    main()
