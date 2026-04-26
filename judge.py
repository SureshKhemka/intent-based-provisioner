"""
Judge LLM — evaluates classifier output for correctness, completeness, and safety.

Uses a separate local LLM to score classifications across four dimensions:
  1. Intent label correctness
  2. Slot/entity extraction completeness
  3. Confidence calibration reasonableness
  4. Safety flag appropriateness

Outputs structured JSON to stdio and appends to a JSONL log file.
"""

import json
import os
import time
from datetime import datetime

import requests

import llm_client

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
BASE_DIR   = os.path.dirname(__file__)

# ── Dimension labels ─────────────────────────────────────────────────────────
DIMENSIONS = [
    "intent_correctness",
    "slot_extraction",
    "confidence_calibration",
    "safety_flags",
]


def load_judge_config() -> dict:
    path = os.path.join(CONFIG_DIR, "judge_config.json")
    if not os.path.exists(path):
        return {"enabled": False}
    with open(path) as f:
        return json.load(f)


def _build_judge_prompt(taxonomy_intents: list, confirmation_rules: dict) -> str:
    intent_list = ", ".join(taxonomy_intents)
    always_confirm = ", ".join(confirmation_rules.get("always", []))
    prod_confirm   = ", ".join(confirmation_rules.get("when_prod", []))

    return f"""
You are a Judge LLM that evaluates an intent classifier's output.
You receive the user's original request, the classifier's JSON output,
and the valid intent taxonomy. Your job is to score the classification
on four dimensions.

## Valid Intent Taxonomy
{intent_list}

## Safety Rules
Intents that ALWAYS require confirmation: {always_confirm}
Intents that require confirmation in prod: {prod_confirm}

## Scoring Dimensions (each 1-10)

1. **intent_correctness** — Did the classifier pick the right intent(s)
   from the taxonomy? Consider: correct domain, correct action, no
   missing intents, no hallucinated intents.

2. **slot_extraction** — Are the extracted parameters complete and
   accurate? Did it capture all entities the user mentioned (name,
   region, size, etc.)? Are values correct (not defaults mixed with
   user values)?

3. **confidence_calibration** — Is the stated confidence reasonable?
   Clear unambiguous requests should be 0.85+. Ambiguous or vague
   requests should be lower. Penalize overconfidence on ambiguous input
   or underconfidence on clear input.

4. **safety_flags** — Does requires_confirmation match the safety rules?
   Destructive operations and prod-targeting intents must be flagged.
   Non-destructive read-only ops should NOT be flagged.

## Output Format
Respond ONLY with JSON. No markdown, no explanation.
{{
  "intent_correctness": {{
    "score": <1-10>,
    "rationale": "<1-2 sentences>"
  }},
  "slot_extraction": {{
    "score": <1-10>,
    "rationale": "<1-2 sentences>"
  }},
  "confidence_calibration": {{
    "score": <1-10>,
    "rationale": "<1-2 sentences>"
  }},
  "safety_flags": {{
    "score": <1-10>,
    "rationale": "<1-2 sentences>"
  }},
  "overall_verdict": "pass" | "warn" | "fail",
  "summary": "<1 sentence overall assessment>"
}}

Verdict rules:
- "pass" if all scores >= 7
- "warn" if any score is 4-6
- "fail" if any score <= 3
""".strip()


def _build_judge_user_message(user_input: str, classifier_output: dict) -> str:
    clean_output = {
        "intents": classifier_output.get("intents", []),
        "compound": classifier_output.get("compound", False),
        "raw_request": classifier_output.get("raw_request", user_input),
    }
    return (
        f"## User Request\n{user_input}\n\n"
        f"## Classifier Output\n{json.dumps(clean_output, indent=2)}"
    )


def evaluate(user_input: str, classifier_output: dict,
             taxonomy_intents: list, confirmation_rules: dict,
             judge_config: dict) -> dict:
    """
    Send the classifier's output to the judge LLM for evaluation.
    Returns structured evaluation dict or error dict.
    """
    if not judge_config.get("enabled", False):
        return {"status": "skipped", "message": "Judge is disabled"}

    system_prompt = _build_judge_prompt(taxonomy_intents, confirmation_rules)
    user_message  = _build_judge_user_message(user_input, classifier_output)
    provider_name = llm_client.provider_label(judge_config)
    endpoint      = llm_client._endpoint(judge_config)

    try:
        start = time.time()
        raw   = llm_client.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            judge_config,
            json_format=True,
        )
        latency = round(time.time() - start, 2)

        if "<think>" in raw:
            raw = raw.split("</think>")[-1].strip()

        evaluation = json.loads(raw)
        evaluation["status"]    = "evaluated"
        evaluation["latency_s"] = latency
        evaluation["model"]     = judge_config.get("model", "unknown")
        return evaluation

    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": f"Cannot connect to {provider_name} at {endpoint}"}
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Judge LLM timed out (120s)"}
    except (json.JSONDecodeError, KeyError) as e:
        return {"status": "error", "message": f"Judge returned invalid JSON: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Judge error: {e}"}


def log_evaluation(user_input: str, classifier_output: dict,
                   evaluation: dict, judge_config: dict):
    """Append a full evaluation record to the JSONL log file."""
    log_path = judge_config.get("log_file", "logs/judge_evaluations.jsonl")
    if not os.path.isabs(log_path):
        log_path = os.path.join(BASE_DIR, log_path)

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    record = {
        "timestamp":         datetime.utcnow().isoformat() + "Z",
        "user_input":        user_input,
        "classifier_output": {
            "intents":  classifier_output.get("intents", []),
            "compound": classifier_output.get("compound", False),
            "latency_s": classifier_output.get("latency_s", 0),
        },
        "judge_evaluation":  evaluation,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")


def print_evaluation(evaluation: dict):
    """Pretty-print the judge evaluation to stdio."""
    if evaluation.get("status") == "skipped":
        return
    if evaluation.get("status") == "error":
        print(f"\n  ⚖️  Judge: ERROR — {evaluation.get('message', 'unknown')}")
        return

    verdict = evaluation.get("overall_verdict", "unknown")
    icon    = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(verdict, "❓")
    latency = evaluation.get("latency_s", 0)

    print(f"\n  ⚖️  Judge Evaluation ({evaluation.get('model', 'unknown')}, {latency}s)")
    print(f"  {'─' * 54}")

    for dim in DIMENSIONS:
        dim_data  = evaluation.get(dim, {})
        score     = dim_data.get("score", 0)
        rationale = dim_data.get("rationale", "")
        bar       = "█" * score + "░" * (10 - score)
        label     = dim.replace("_", " ").title()
        print(f"  {label:<26} [{bar}] {score:>2}/10")
        if rationale:
            print(f"  {'':26}   {rationale}")

    print(f"  {'─' * 54}")
    print(f"  Verdict : {icon} {verdict.upper()}")
    summary = evaluation.get("summary", "")
    if summary:
        print(f"  Summary : {summary}")
