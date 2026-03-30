import json
import os
from datetime import datetime

CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "context")


class ContextManager:
    def __init__(self, team: str = "default"):
        self.team = team
        self.path = os.path.join(CONTEXT_DIR, f"{team}.json")
        os.makedirs(CONTEXT_DIR, exist_ok=True)
        self.session = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path) as f:
                return json.load(f)
        return {"team": self.team, "history": [], "resources": {}}

    def save(self):
        self.session["last_active"] = datetime.utcnow().isoformat()
        with open(self.path, "w") as f:
            json.dump(self.session, f, indent=2)

    def add_turn(self, user_input: str, result: dict):
        intents   = [i["intent"] for i in result.get("intents", [])]
        resources = self.session.setdefault("resources", {})

        # Track the last resource per domain
        for item in result.get("intents", []):
            params = item.get("params", {})
            intent = item.get("intent", "")

            if intent.startswith("compute.") and params.get("name"):
                resources["last_vm"] = {
                    "name":        params["name"],
                    "environment": params.get("environment", ""),
                    "region":      params.get("region", "")
                }

            if intent.startswith("k8s.") and params.get("service"):
                resources["last_service"] = {
                    "name":        params["service"],
                    "environment": params.get("environment", ""),
                    "namespace":   params.get("namespace", "")
                }

            if intent.startswith("db.") and params.get("name"):
                resources["last_db"] = {
                    "name":        params["name"],
                    "environment": params.get("environment", "")
                }

        self.session["history"].append({
            "timestamp":  datetime.utcnow().isoformat(),
            "user_input": user_input,
            "intents":    intents,
            "params":     [i.get("params", {}) for i in result.get("intents", [])]
        })

        # Keep history to last 20 turns
        self.session["history"] = self.session["history"][-20:]
        self.save()

    def build_context_block(self) -> str:
        resources = self.session.get("resources", {})
        history   = self.session.get("history", [])
        lines     = []

        if resources.get("last_vm"):
            vm = resources["last_vm"]
            lines.append(f"Last VM: name={vm['name']}, environment={vm.get('environment','')}, region={vm.get('region','')}")

        if resources.get("last_service"):
            svc = resources["last_service"]
            lines.append(f"Last K8s service: name={svc['name']}, environment={svc.get('environment','')}")

        if resources.get("last_db"):
            db = resources["last_db"]
            lines.append(f"Last DB: name={db['name']}, environment={db.get('environment','')}")

        if history:
            last = history[-1]
            lines.append(f"Last action: {', '.join(last['intents'])}")

        return "\n".join(lines) if lines else ""

    def resolve_references(self, user_input: str) -> str:
        """Enrich vague pronouns with known resource names from context."""
        resources = self.session.get("resources", {})
        enriched  = user_input

        if resources.get("last_vm"):
            vm = resources["last_vm"]
            last_intents = self._last_intents()
            if any(i.startswith("compute.") for i in last_intents):
                enriched = enriched.replace(" it ", f" {vm['name']} ")
                enriched = enriched.replace(" it.", f" {vm['name']}.")

        if resources.get("last_service"):
            svc = resources["last_service"]
            last_intents = self._last_intents()
            if any(i.startswith("k8s.") for i in last_intents):
                enriched = enriched.replace(" it ", f" {svc['name']} ")
                enriched = enriched.replace(" it.", f" {svc['name']}.")

        if resources.get("last_db"):
            db = resources["last_db"]
            last_intents = self._last_intents()
            if any(i.startswith("db.") for i in last_intents):
                enriched = enriched.replace(" it ", f" {db['name']} ")
                enriched = enriched.replace(" it.", f" {db['name']}.")

        return enriched

    def _last_intents(self) -> list:
        history = self.session.get("history", [])
        if not history:
            return []
        return history[-1].get("intents", [])

    def get_history(self) -> list:
        return self.session.get("history", [])

    def clear(self):
        self.session["history"]   = []
        self.session["resources"] = {}
        self.save()
        print(f"  Context cleared for team: {self.team}")

    def summary(self) -> str:
        history   = self.session.get("history", [])
        resources = self.session.get("resources", {})
        lines = [
            f"  Team        : {self.team}",
            f"  Last active : {self.session.get('last_active', 'never')}",
            f"  Turns       : {len(history)}",
            f"  Resources   : {list(resources.keys()) if resources else 'none tracked'}"
        ]
        return "\n".join(lines)
