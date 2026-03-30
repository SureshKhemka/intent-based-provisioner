# Intent Classifier — Infrastructure Provisioning Platform

Local LLM-powered intent classifier using Ollama + Qwen3:4b.

## Project Structure

```
intent/
├── interactive.py        ← Main entry point — interactive REPL with context
├── classify.py           ← Core classification module (imported by others)
├── context_manager.py    ← Session context engine (per-team, persisted)
├── generate_tests.py     ← Synthetic test case generator
├── evaluate.py           ← Evaluation harness with accuracy + latency metrics
├── config/
│   ├── taxonomy.json     ← All intents + descriptions (edit to add intents)
│   ├── defaults.json     ← Default params per intent
│   └── confirmation.json ← Which intents need confirmation + conditions
├── tests/
│   ├── test_cases.json   ← Generated + reviewed test cases
│   └── results/          ← Timestamped eval reports (JSON)
└── context/
    └── <team>.json       ← Persisted session context per team
```

## Prerequisites

```bash
brew install ollama
ollama pull qwen3:4b
brew services start ollama
```

## Usage

### Interactive classifier (main workflow)
```bash
python3 interactive.py
```

Commands inside the REPL:
- `help`    — list all intents
- `history` — show last 10 turns
- `clear`   — clear context for current team
- `switch`  — switch to a different team context
- `quit`    — exit

### Generate test cases
```bash
python3 generate_tests.py
```
Then open `tests/test_cases.json`, review each case, set `"reviewed": true`.

### Run evaluation
```bash
python3 evaluate.py
```

## Adding a New Intent

1. Edit `config/taxonomy.json` — add one entry to the `intents` array
2. Optionally add defaults to `config/defaults.json`
3. Optionally add confirmation rules to `config/confirmation.json`
4. Restart `interactive.py` — no code changes needed

## Key Design Decisions

- **Config-driven** — taxonomy, defaults, and confirmation rules all live in JSON files
- **No-think mode** — `"think": False` skips Qwen3 chain-of-thought for low-latency classification
- **Confirmation enforcement** — safety rules enforced in Python, not just prompted to the model
- **Context persistence** — per-team session context saved to disk, survives restarts
- **Compound intent detection** — handles multi-action requests in a single call
