import json
import os

from classify import load_config, build_system_prompt, classify_intent
from context_manager import ContextManager
from execution_router import ExecutionRouter

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
            for k, v in params.items():
                tag = " (default)" if k in defaults_used else ""
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
    print(f"    quit      — exit")


def main():
    taxonomy, defaults, confirmation = load_config()
    intent_names  = [i["name"] for i in taxonomy["intents"]]
    router        = ExecutionRouter(dry_run=True)
    classify_only = False

    print("=" * 60)
    print("  Infrastructure Intent-Based Provisioner")
    print(f"  Model      : qwen3:4b via Ollama")
    print(f"  Intents    : {len(intent_names)} loaded from config")
    print(f"  Exec mode  : DRY-RUN 🔵  (type 'mode' to toggle)")
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

        try:
            # Step 1 — resolve references
            resolved = context.resolve_references(user_input)
            if resolved != user_input:
                print(f"\n  🔗 Resolved: \"{resolved}\"")

            # Step 2 — build prompt with context
            context_block = context.build_context_block()
            system_prompt = build_system_prompt(taxonomy, context_block)

            # Step 3 — classify
            result = classify_intent(resolved, system_prompt, defaults, confirmation)

            # Step 4 — show classification
            print_classification(result)

            # Step 5 — execute
            if not classify_only:
                print(f"\n  ── Execution ────────────────────────────────────────")
                router.execute(result)

            # Step 6 — save to context
            context.add_turn(user_input, result)

        except Exception as e:
            print(f"\n  Error: {e}")
            print("  Make sure Ollama is running: ollama serve")


if __name__ == "__main__":
    main()
