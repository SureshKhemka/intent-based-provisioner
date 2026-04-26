import json
import os
import uuid

import llm_client

CONFIG_DIR  = os.path.join(os.path.dirname(__file__), "config")
TESTS_DIR   = os.path.join(os.path.dirname(__file__), "tests")
OUTPUT_FILE = os.path.join(TESTS_DIR, "test_cases.json")


def _load_model_config() -> dict:
    path = os.path.join(CONFIG_DIR, "model_config.json")
    with open(path) as f:
        return json.load(f)

GENERATE_PROMPT = """Generate {count} realistic natural language requests that a developer might type to an infrastructure platform.

Intent: {name}
Description: {description}

Rules:
- Return ONLY a JSON array of {count} strings
- Each string is a natural language request
- Vary the wording, formality, and detail level
- Some casual, some formal, some with specific params, some vague
- Do NOT include the intent name in the utterance
- Do NOT wrap in markdown or any other text

Example output format:
["request one here", "request two here", "request three here"]
"""

COMPOUND_PROMPT = """Generate {count} natural language requests that combine MULTIPLE infrastructure actions in a single message.

Rules:
- Return ONLY a JSON array of {count} strings
- Each string should combine 2-3 different operations
- Make them realistic — things a developer would actually say
- Do NOT wrap in markdown or any other text

Example:
["spin up a VM called web1 and open port 80 on it", "backup prod-db then scale payments to 5 replicas"]
"""


def generate_utterances(intent_name: str, description: str, count: int = 5,
                        model_config: dict = None) -> list:
    if model_config is None:
        model_config = _load_model_config()

    prompt = GENERATE_PROMPT.format(
        name=intent_name,
        description=description,
        count=count
    )

    gen_config = {**model_config, "temperature": 0.8}
    raw = llm_client.generate(prompt, gen_config)

    # Strip think blocks if present
    if "<think>" in raw:
        raw = raw.split("</think>")[-1].strip()

    # Strip markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    parsed = json.loads(raw)

    if isinstance(parsed, list):
        return [str(u) for u in parsed]

    # Handle case where model returns a dict with a list value
    if isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, list):
                return [str(u) for u in v]

    return []


def generate_compound_cases(count: int = 15, model_config: dict = None) -> list:
    if model_config is None:
        model_config = _load_model_config()

    prompt = COMPOUND_PROMPT.format(count=count)

    gen_config = {**model_config, "temperature": 0.8}
    raw = llm_client.generate(prompt, gen_config)

    if "<think>" in raw:
        raw = raw.split("</think>")[-1].strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for v in parsed.values():
                if isinstance(v, list):
                    return v
        return []
    except Exception as e:
        print(f"  ⚠ Could not parse compound cases: {e}")
        return []


def make_id(intent_name: str, index: int) -> str:
    safe = intent_name.replace(".", "_")
    return f"{safe}_{index:04d}"


def main():
    os.makedirs(TESTS_DIR, exist_ok=True)

    with open(os.path.join(CONFIG_DIR, "taxonomy.json")) as f:
        taxonomy = json.load(f)

    model_config = _load_model_config()
    intents      = taxonomy["intents"]
    test_cases   = []

    print(f"Generating test cases for {len(intents)} intents...")
    print(f"  Provider : {llm_client.provider_label(model_config)}")
    print(f"  Model    : {model_config.get('model', '?')}\n")

    for idx, intent in enumerate(intents, 1):
        name        = intent["name"]
        description = intent["description"]
        print(f"  [{idx}/{len(intents)}] {name}... ", end="", flush=True)

        try:
            utterances = generate_utterances(name, description, count=5, model_config=model_config)
            for i, utt in enumerate(utterances):
                test_cases.append({
                    "id":               make_id(name, i + 1),
                    "utterance":        utt,
                    "expected_intents": [name],
                    "compound":         False,
                    "reviewed":         False,
                    "notes":            ""
                })
            print(f"{len(utterances)} cases generated")
        except Exception as e:
            print(f"⚠ Error: {e}")

    # Compound cases
    print(f"\n  [compound] Generating compound test cases... ", end="", flush=True)
    try:
        compound_utterances = generate_compound_cases(count=15, model_config=model_config)
        for i, utt in enumerate(compound_utterances):
            test_cases.append({
                "id":               f"compound_{i+1:04d}",
                "utterance":        utt,
                "expected_intents": [],   # fill in manually after review
                "compound":         True,
                "reviewed":         False,
                "notes":            "Review expected_intents before marking reviewed=true"
            })
        print(f"{len(compound_utterances)} cases generated")
    except Exception as e:
        print(f"⚠ Error: {e}")

    output = {"test_cases": test_cases}
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved {len(test_cases)} test cases to tests/test_cases.json")
    print("  Next: open that file, review cases, set 'reviewed': true, then run evaluate.py")


if __name__ == "__main__":
    main()
