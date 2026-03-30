import json
import os

from classify import load_config, build_system_prompt, classify_intent
from context_manager import ContextManager

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


def print_result(result: dict):
    intents  = result.get("intents", [])
    compound = result.get("compound", False)
    latency  = result.get("latency_s", 0)

    if compound:
        print(f"\n  ⚡ Compound request — {len(intents)} intents detected")

    for i, item in enumerate(intents, 1):
        intent      = item.get("intent", "meta.unknown")
        confidence  = item.get("confidence", 0.0)
        params      = item.get("params", {})
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


def main():
    taxonomy, defaults, confirmation = load_config()
    intent_names = [i["name"] for i in taxonomy["intents"]]

    print("=" * 55)
    print("  Infrastructure Intent Classifier")
    print(f"  Model   : qwen3:4b via Ollama")
    print(f"  Intents : {len(intent_names)} loaded from config")
    print("  Commands: quit, help, history, clear, switch")
    print("=" * 55)

    team    = select_team()
    context = ContextManager(team)
    print(f"\n  Team context loaded:")
    print(context.summary())

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\nExiting. Goodbye!")
            break

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
            # Rebuild system prompt is handled per-call
            continue

        if user_input.lower() == "help":
            print("\n  Available intents:")
            for name in intent_names:
                print(f"    {name}")
            continue

        try:
            # Step 1 — resolve references using context
            resolved = context.resolve_references(user_input)
            if resolved != user_input:
                print(f"\n  🔗 Resolved: \"{resolved}\"")

            # Step 2 — build prompt with current context injected
            context_block = context.build_context_block()
            system_prompt = build_system_prompt(taxonomy, context_block)

            # Step 3 — classify
            result = classify_intent(resolved, system_prompt, defaults, confirmation)

            # Step 4 — display result
            print_result(result)

            # Step 5 — save turn to context
            context.add_turn(user_input, result)

        except Exception as e:
            print(f"\n  Error: {e}")
            print("  Make sure Ollama is running: ollama serve")


if __name__ == "__main__":
    main()
