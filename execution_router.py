import json
from datetime import datetime

from handlers import compute_handler, k8s_handler, db_handler, net_handler

# ── Mode toggle ───────────────────────────────────────────────────────────────
# True  → dry-run: describe what would happen, no side effects
# False → simulate: return realistic fake responses
DRY_RUN = True


# ── Domain → handler mapping ──────────────────────────────────────────────────
HANDLER_MAP = {
    "compute": compute_handler,
    "k8s":     k8s_handler,
    "db":      db_handler,
    "net":     net_handler,
}


def _get_handler(intent: str):
    domain = intent.split(".")[0]
    return HANDLER_MAP.get(domain)


def _audit(event: str, intent: str, params: dict, result: dict, user: str = "developer"):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user":      user,
        "intent":    intent,
        "params":    params,
        "mode":      "dry_run" if DRY_RUN else "simulate",
        "event":     event,
        "outcome":   result.get("status", "unknown"),
        "message":   result.get("message", "")
    }
    _print_audit(entry)


def _print_audit(entry: dict):
    mode_tag = "DRY-RUN" if entry["mode"] == "dry_run" else "SIMULATE"
    print(
        f"\n  📋 AUDIT  [{mode_tag}]  {entry['timestamp']}"
        f"\n           intent  : {entry['intent']}"
        f"\n           event   : {entry['event']}"
        f"\n           outcome : {entry['outcome']}"
        f"\n           message : {entry['message']}"
    )


def _confirm(intent: str, params: dict) -> bool:
    """Ask user to confirm a sensitive action. Returns True if confirmed."""
    print(f"\n  ⚠️  CONFIRMATION REQUIRED")
    print(f"     Intent : {intent}")
    if params:
        for k, v in params.items():
            print(f"     {k:<12}: {v}")
    answer = input("\n  Proceed? (yes/no): ").strip().lower()
    return answer == "yes"


def _print_result(intent: str, result: dict, dry_run: bool):
    mode  = "DRY-RUN" if dry_run else "SIMULATED"
    color = "🔵" if dry_run else "🟢"
    status = result.get("status", "unknown")

    print(f"\n  {color} [{mode}] {intent}")

    if status == "error":
        print(f"  ❌ Error: {result.get('message')}")
        return

    print(f"  ✓ {result.get('message', '')}")

    if dry_run and result.get("would_call"):
        print(f"  → API: {result['would_call']}")

    # Print key result fields (skip status/message/would_call)
    skip = {"status", "message", "would_call", "payload"}
    extras = {k: v for k, v in result.items() if k not in skip}
    if extras:
        print(f"  ─────────────────────────────────────")
        for k, v in extras.items():
            if isinstance(v, list):
                print(f"  {k:<16}: {', '.join(str(i) for i in v)}")
            else:
                print(f"  {k:<16}: {v}")


class ExecutionRouter:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def set_mode(self, dry_run: bool):
        self.dry_run = dry_run
        mode = "DRY-RUN" if dry_run else "SIMULATE"
        print(f"\n  ⚙️  Execution mode set to: {mode}")

    def execute(self, classification: dict) -> list:
        """
        Takes the full classification result from classify_intent()
        and executes each intent through the appropriate handler.

        Returns a list of execution results.
        """
        intents  = classification.get("intents", [])
        compound = classification.get("compound", False)
        results  = []

        if compound:
            print(f"\n  ⚡ Compound request — executing {len(intents)} intents sequentially")

        for item in intents:
            intent           = item.get("intent", "meta.unknown")
            params           = item.get("params", {})
            needs_confirm    = item.get("requires_confirmation", False)

            # Skip meta intents — nothing to execute
            if intent.startswith("meta."):
                result = {
                    "status":  "skipped",
                    "message": f"'{intent}' is informational — no execution needed"
                }
                _print_result(intent, result, self.dry_run)
                results.append({"intent": intent, "result": result})
                continue

            # Confirmation gate
            if needs_confirm and not self.dry_run:
                confirmed = _confirm(intent, params)
                if not confirmed:
                    result = {
                        "status":  "cancelled",
                        "message": f"Execution of '{intent}' cancelled by user"
                    }
                    _audit("cancelled", intent, params, result)
                    _print_result(intent, result, self.dry_run)
                    results.append({"intent": intent, "result": result})
                    continue
            elif needs_confirm and self.dry_run:
                print(f"\n  ⚠️  Note: '{intent}' would require confirmation in simulate mode")

            # Dispatch to handler
            handler = _get_handler(intent)
            if not handler:
                result = {
                    "status":  "error",
                    "message": f"No handler registered for intent: {intent}"
                }
            else:
                try:
                    result = handler.handle(intent, params, self.dry_run)
                except Exception as e:
                    result = {
                        "status":  "error",
                        "message": f"Handler exception: {str(e)}"
                    }

            _audit("executed", intent, params, result)
            _print_result(intent, result, self.dry_run)
            results.append({"intent": intent, "result": result})

        return results
