# CLAUDE.md — Intent-Based Infrastructure Provisioner

## Project Overview

Local LLM-powered intent classifier + execution engine for infrastructure provisioning. Developers describe what they want in natural language → classify intent → extract params → enrich with org policies (OPA/Rego) → validate guardrails → execute or simulate. Fully local: Ollama + Qwen3:4b, no cloud dependencies.

## Tech Stack

- Python 3.12+, pure stdlib + `requests` (the ONLY external dependency)
- LLM: Ollama qwen3:4b at `http://localhost:11434/api/chat`, JSON format, `"think": false`, temp 0.1
- Policy engine: OPA at `http://localhost:8181`, Rego policies, REST API
- Config: JSON files in `config/` — no hardcoded values anywhere

## Current Focus — OPA Policy Integration

Adding a policy layer between classification and execution. Two new pipeline stages:

1. **Policy Enrichment** — after `apply_defaults()`, query OPA to fill org-standard values (instance sizing, encryption, backup policies, required labels) into params the user didn't specify.
2. **Policy Validation** — after enrichment, validate fully-assembled params against hard guardrails (allowed regions, max resource limits, mandatory encryption in prod).

### Pipeline Order (preserve this exactly)
```
classify → apply_defaults → policy_enrich → policy_validate → enforce_confirmation → execute
```

### Design Decisions

- **Two-pass policy**: Enrich first (fill blanks), validate second (check constraints). Never combine — validator needs to see fully-enriched params.
- **Param precedence**: user-specified > policy enrichment > config/defaults.json
- **OPA as sidecar**: REST API calls to OPA server, never embed Rego in Python. Wrap in `policy_engine.py` with graceful fallback if OPA is down.
- **Rego returns structured JSON**, not booleans. Enrichment returns `{"enrichments": {...}, "source": "org_standard"}`. Validation returns `{"allow": bool, "violations": [...], "warnings": [...]}`.
- **Policy routing by domain**: Split `intent.split(".")[0]` to load `policies/<domain>/defaults.rego` or `guardrails.rego`. Same dispatch pattern as `execution_router.py`.
- **Track provenance**: Add `policy_applied` list to each intent's params showing which fields came from policy vs user vs config defaults.

### New Files to Create

- `policies/<domain>/defaults.rego` + `guardrails.rego` — per domain (compute, k8s, db, net)
- `policy_engine.py` — OPA REST client wrapper with health check + CLI fallback
- `policy_enricher.py` — queries OPA defaults, merges into params
- `policy_validator.py` — queries OPA guardrails, returns allow/deny + violations
- `config/policy_config.json` — OPA endpoint, eval mode, policy paths

## Code Conventions (match existing codebase)

- Plain dicts for data passing — no dataclasses, Pydantic, or attrs
- Functions return `{"status": "...", "message": "...", ...}` — no exceptions across module boundaries
- Print-based output formatting (not logging framework)
- One file = one responsibility, cap at ~150 lines per file
- Handler convention: `handle(intent, params, dry_run)` function, not classes
- Constants at module top as `UPPER_SNAKE_CASE`

## What NOT To Do

- Do NOT modify `classify.py`'s LLM interaction — classifier must not know about policies
- Do NOT embed Rego in Python — no `regopy`, no inline Rego strings, always OPA server/CLI
- Do NOT use Kyverno here — that's a separate k8s admission webhook project
- Do NOT introduce async, FastAPI, dataclasses, Pydantic, or abstract base classes
- Do NOT change `config/defaults.json` semantics — policy enrichment layers on top
- Do NOT add pip dependencies without flagging it explicitly
- Do NOT let the LLM generate policy decisions — all policy logic is deterministic OPA

## Testing

- Rego: `opa test policies/` — every `.rego` gets a `*_test.rego` companion
- Python: extend `evaluate.py` pattern with JSON test cases in `tests/`
- Key scenarios: enrichment fills correct defaults, validation blocks disallowed configs, user params override policy, compound intents get independent policy evaluation
