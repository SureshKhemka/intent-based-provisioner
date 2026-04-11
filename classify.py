import requests
import json
import os
import time

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")


def load_config():
    def read(filename):
        with open(os.path.join(CONFIG_DIR, filename)) as f:
            return json.load(f)
    return read("taxonomy.json"), read("defaults.json"), read("confirmation.json"), read("model_config.json")


def build_system_prompt(taxonomy: dict, context_block: str = "") -> str:
    intent_names = [i["name"] for i in taxonomy["intents"]]
    intent_list  = ", ".join(intent_names)
    descriptions = "\n".join(
        f"  {i['name']}: {i['description']}"
        for i in taxonomy["intents"]
    )

    context_section = ""
    if context_block:
        context_section = f"""
## Session Context
Use the context below to resolve pronouns like "it", "that", "the service" etc.
{context_block}
"""

    return f"""
You are an intent classifier for an infrastructure provisioning platform.
Developers send you natural language requests. Your job is to:
1. Identify ALL intents in the request (there may be more than one)
2. Extract only the parameters explicitly mentioned by the user
3. Use session context to resolve any pronouns or implicit references
4. Flag sensitive intents that require confirmation before execution
{context_section}
## Intent Taxonomy
{intent_list}

## Intent Descriptions
{descriptions}

## Output Format
Respond ONLY with a JSON object. No explanation, no markdown, no preamble.
{{
  "intents": [
    {{
      "intent": "<domain.action>",
      "confidence": <0.0 to 1.0>,
      "requires_confirmation": <true or false>,
      "params": {{}}
    }}
  ],
  "compound": <true if more than one intent, false otherwise>,
  "raw_request": "<original user text>"
}}
""".strip()


def apply_defaults(intents: list, defaults: dict) -> list:
    for item in intents:
        intent_name = item.get("intent", "")
        if intent_name in defaults:
            merged = {**defaults[intent_name], **item.get("params", {})}
            item["params"] = merged
            item["defaults_applied"] = [
                k for k in defaults[intent_name]
                if k not in item.get("params", {}) or item.get("params", {}).get(k) == defaults[intent_name][k]
            ]
    return intents


def enforce_confirmation(intents: list, confirmation: dict) -> list:
    always    = set(confirmation.get("always", []))
    when_prod = set(confirmation.get("when_prod", []))
    for item in intents:
        intent = item.get("intent", "")
        params = item.get("params", {})
        env    = params.get("environment", "").lower()
        if intent in always:
            item["requires_confirmation"] = True
        if intent in when_prod and env in ("prod", "production"):
            item["requires_confirmation"] = True
    return intents


def classify_intent(user_request: str, system_prompt: str,
                    defaults: dict, confirmation: dict,
                    model_config: dict = None) -> dict:
    if model_config is None:
        model_config = {}
    model    = model_config.get("model", "qwen3:4b")
    endpoint = model_config.get("ollama_endpoint", "http://localhost:11434")
    temp     = model_config.get("temperature", 0.1)
    think    = model_config.get("think", False)

    start = time.time()
    response = requests.post(
        f"{endpoint}/api/chat",
        json={
            "model": model,
            "format": "json",
            "options": {"temperature": temp},
            "think": think,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_request}
            ],
            "stream": False
        }
    )
    latency = round(time.time() - start, 2)

    raw = response.json()["message"]["content"].strip()

    # Strip any leaked <think> blocks
    if "<think>" in raw:
        raw = raw.split("</think>")[-1].strip()

    if not raw:
        return {
            "intents": [{"intent": "meta.unknown", "confidence": 0.0,
                         "requires_confirmation": False, "params": {}}],
            "compound": False,
            "raw_request": user_request,
            "latency_s": latency
        }

    result = json.loads(raw)
    result["intents"] = apply_defaults(result.get("intents", []), defaults)
    result["intents"] = enforce_confirmation(result.get("intents", []), confirmation)
    result["latency_s"] = latency
    return result
