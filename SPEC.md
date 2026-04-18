# Technical Specification: Intent-Based Infrastructure Provisioner

**Version**: 1.0
**Status**: As-built specification (reflects implemented system)
**Last Updated**: 2026-04-18

---

## 1. Overview

### 1.1 Purpose

Build a local, fully offline infrastructure provisioning system where developers describe what they want in natural language and the system classifies their intent, extracts parameters, applies organizational policies, evaluates classification quality, and executes (or simulates) the appropriate infrastructure action.

### 1.2 Goals

- **Natural language interface** — developers say "spin up a VM in prod" instead of writing YAML or clicking through consoles
- **Compound intent detection** — a single utterance like "spin up a VM and create a database" produces multiple classified intents executed sequentially
- **Multi-turn conversation** — session context tracks previously mentioned resources so developers can say "now resize it" and the system resolves "it"
- **Policy-as-code** — organizational standards (encryption requirements, instance sizing, backup policies) are applied automatically via OPA/Rego, not hardcoded
- **Classification quality assurance** — a separate Judge LLM evaluates every classification in real time across multiple quality dimensions
- **Zero cloud dependency** — LLM inference, policy evaluation, and execution all run locally
- **Simulation-first** — two execution modes (dry-run and simulate) let developers explore safely before any real action

### 1.3 Non-Goals

- Not a production deployment tool — handlers are stubs that describe or simulate actions, they do not call real cloud APIs
- Not a general-purpose chatbot — the system classifies and executes infrastructure intents only
- Not a Kubernetes admission controller — policy logic lives here, Kyverno/admission webhooks are a separate concern
- Not a multi-user server — this is a single-user CLI tool with per-team context separation

---

## 2. Architecture

### 2.1 System Diagram

```
                              ┌──────────────────┐
                              │  config/*.json   │
                              │  (taxonomy,      │
                              │   defaults,      │
                              │   confirmation,  │
                              │   model_config,  │
                              │   judge_config,  │
                              │   policy_config) │
                              └────────┬─────────┘
                                       │
User ──→ interactive.py (REPL) ──→ classify.py ──→ Ollama LLM
              │                        │              (local)
              │                        ↓
              │               context_manager.py
              │               (pronoun resolution,
              │                session state)
              │                        │
              │                        ↓
              │               apply_defaults()
              │               (config/defaults.json)
              │                        │
              │                        ↓
              │               policy_enricher.py ──→ OPA Server
              │               (org-standard          (local,
              │                defaults)              optional)
              │                        │
              │                        ↓
              │               policy_validator.py ──→ OPA Server
              │               (guardrail              (Rego
              │                enforcement)            policies)
              │                        │
              │                        ↓
              │               judge.py ──→ Ollama LLM
              │               (classification         (separate
              │                quality eval)           model)
              │                    │
              │                    ├──→ stdio (printed scores)
              │                    └──→ logs/judge_evaluations.jsonl
              │                        │
              │                        ↓
              │               execution_router.py
              │               (confirmation gate,
              │                domain dispatch,
              │                audit log)
              │                        │
              │                        ↓
              │               handlers/*_handler.py
              │               (49 domain handlers,
              │                dry-run or simulate)
              │                        │
              └──→ context_manager.py ──→ context/{team}.json
                   (save turn to session)
```

### 2.2 Pipeline Order

This is the exact processing pipeline. Each stage transforms the intent data and passes it forward. The order is mandatory and must not be rearranged.

```
classify → apply_defaults → policy_enrich → policy_validate → judge → enforce_confirmation → execute
```

| Stage | Module | Input | Output | Can block? |
|-------|--------|-------|--------|------------|
| **Classify** | `classify.py` | User text + system prompt | `{intents, compound, raw_request, latency_s}` | No |
| **Apply Defaults** | `classify.py` | Intents + defaults.json | Intents with default params merged | No |
| **Policy Enrich** | `policy_enricher.py` | Intents | Intents with org-standard values + provenance | No (graceful skip if OPA down) |
| **Policy Validate** | `policy_validator.py` | Intents | Intents with allow/violations/warnings | Yes (violations block execution) |
| **Judge** | `judge.py` | User text + classifier output | Scores printed + logged | No (never blocks) |
| **Confirm** | `execution_router.py` | Intents + confirmation rules | User prompted if needed | Yes (user can cancel) |
| **Execute** | `handlers/*_handler.py` | Intent + params + mode | Action result | No |

### 2.3 Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Language | Python 3.12+ | stdlib + `requests` only |
| LLM | Ollama (local) | Any model — configurable per role |
| Policy Engine | OPA (Open Policy Agent) | REST API at localhost:8181, Rego policies |
| Data format | JSON (config, context, logs) | No database |
| Dependencies | `requests` | The ONLY external pip package |

### 2.4 Constraints

- No dataclasses, Pydantic, attrs, or abstract base classes — plain dicts everywhere
- No async, no FastAPI, no web framework
- No logging framework — `print()` only
- No exceptions across module boundaries — functions return `{"status": "...", "message": "..."}`
- One file = one responsibility, target ~150 lines per file (soft limit)
- No hardcoded values — all configuration in `config/*.json`
- No inline Rego — all policy logic lives in `.rego` files evaluated by OPA server

---

## 3. Intent Taxonomy

### 3.1 Structure

The taxonomy is a flat list of intent objects stored in `config/taxonomy.json`:

```json
{
  "intents": [
    {"name": "compute.provision", "description": "Create a new VM or compute instance"},
    {"name": "compute.terminate", "description": "Delete or destroy a VM"},
    ...
  ]
}
```

Intent naming convention: `<domain>.<action>` — the domain prefix is used for handler routing, policy lookup, and context tracking.

### 3.2 Domains and Intents (50 domains, 230 intents)

| Domain | Actions | Count |
|--------|---------|-------|
| **compute** | provision, terminate, resize, start_stop, status, list | 6 |
| **k8s** | deploy, scale, rollback, status, logs, exec, delete | 7 |
| **db** | provision, delete, resize, backup, restore, access, status | 7 |
| **net** | dns_create, dns_delete, lb_provision, lb_update, firewall, status | 6 |
| **cache** | provision, delete, resize, flush, status | 5 |
| **storage** | bucket_create, bucket_delete, upload, lifecycle, status | 5 |
| **queue** | create, delete, purge, status | 4 |
| **stream** | create, delete, scale, status | 4 |
| **serverless** | deploy, delete, invoke, update_config, status | 5 |
| **container** | push, pull, delete, list, status | 5 |
| **iam** | create_role, delete_role, attach_policy, create_user, status | 5 |
| **vpc** | create, delete, peer, status | 4 |
| **subnet** | create, delete, status | 3 |
| **vpn** | create, delete, status | 3 |
| **nat** | provision, delete, status | 3 |
| **waf** | create, delete, update_rules, status | 4 |
| **ddos** | enable, disable, status | 3 |
| **cdn** | create, delete, invalidate, status | 4 |
| **cert** | provision, delete, renew, status | 4 |
| **secret** | create, delete, rotate, get, status | 5 |
| **kms** | create_key, delete_key, rotate, encrypt, decrypt, status | 6 |
| **volume** | create, delete, resize, attach, detach, snapshot, status | 7 |
| **filesystem** | create, delete, resize, mount, status | 5 |
| **backup** | create_plan, delete_plan, run, restore, status | 5 |
| **snapshot** | create, delete, copy, restore, list | 5 |
| **autoscale** | create, delete, update_policy, status | 4 |
| **apigw** | create, delete, deploy_stage, update_route, status | 5 |
| **servicemesh** | install, uninstall, configure, status | 4 |
| **registry** | create, delete, push, pull, status | 5 |
| **monitor** | create_alert, delete_alert, create_dashboard, status | 4 |
| **log** | create_group, delete_group, query, export, status | 5 |
| **trace** | enable, disable, query, status | 4 |
| **notification** | create_topic, delete_topic, publish, subscribe, status | 5 |
| **email** | configure, send, verify_domain, status | 4 |
| **workflow** | create, delete, execute, status | 4 |
| **scheduler** | create, delete, enable, disable, status | 5 |
| **batch** | create_job, delete_job, submit, status | 4 |
| **etl** | create_pipeline, delete_pipeline, run, status | 4 |
| **warehouse** | provision, delete, resize, query, status | 5 |
| **datalake** | create, delete, set_permissions, status | 4 |
| **search** | create, delete, resize, reindex, status | 5 |
| **ml** | create_endpoint, delete_endpoint, deploy_model, status | 4 |
| **notebook** | create, delete, start, stop, status | 5 |
| **iot** | create_thing, delete_thing, create_rule, status | 4 |
| **transfer** | create_job, delete_job, start, status | 4 |
| **config** | create_rule, delete_rule, evaluate, status | 4 |
| **compliance** | run_scan, create_policy, status | 3 |
| **image** | create, delete, share, deregister, list | 5 |
| **dr** | create_plan, failover, failback, test, status | 5 |
| **meta** | cost, quota, tag, audit_log, unknown | 5 |

### 3.3 Adding a New Intent

Add one entry to `config/taxonomy.json`. If it's in a new domain, also create `handlers/<domain>_handler.py` and register it in `execution_router.py`'s `HANDLER_MAP`. No other code changes required.

---

## 4. LLM Classification

### 4.1 Classifier Configuration

Stored in `config/model_config.json`:

```json
{
  "model": "<ollama_model_name>",
  "ollama_endpoint": "http://localhost:11434",
  "temperature": 0.1,
  "think": false
}
```

- **model** — any model available in Ollama (e.g., `qwen3:4b`, `gemma4:31b`, `llama3:8b`)
- **temperature** — 0.1 for deterministic classification
- **think** — model-specific chain-of-thought toggle (set `false` for structured JSON output)

### 4.2 System Prompt Construction

The system prompt is built dynamically from `taxonomy.json` and includes:

1. Role definition ("You are an intent classifier for an infrastructure provisioning platform")
2. Instructions for multi-intent detection, parameter extraction, pronoun resolution, and confirmation flagging
3. The complete intent taxonomy (all 230 intent names)
4. Intent descriptions (one per intent)
5. Session context block (last VM, last DB, last service, last action) — if available
6. Strict output format requiring JSON only, no markdown or explanation

### 4.3 Classifier Output Format

```json
{
  "intents": [
    {
      "intent": "compute.provision",
      "confidence": 0.95,
      "requires_confirmation": false,
      "params": {
        "name": "web-server",
        "cpu": "4",
        "region": "us-east-1"
      }
    }
  ],
  "compound": false,
  "raw_request": "provision a 4 core VM called web-server in us-east-1"
}
```

- **compound** — `true` when multiple intents detected in one utterance
- **confidence** — 0.0 to 1.0, set by the LLM
- **requires_confirmation** — initially set by LLM, then overridden by deterministic rules
- **params** — only values explicitly mentioned by the user (not defaults)

### 4.4 LLM Interaction

- Endpoint: `POST {ollama_endpoint}/api/chat`
- Format: `"format": "json"` (forces JSON output from Ollama)
- Streaming: disabled (`"stream": false`)
- Post-processing: strips any leaked `<think>` blocks from response
- Latency is measured and attached to the result as `latency_s`

### 4.5 Think Block Handling

Some models (notably Qwen3) emit `<think>...</think>` blocks before JSON output even when `think: false` is set. The classifier strips everything before `</think>` to extract the JSON payload.

---

## 5. Parameter Defaults

### 5.1 Configuration

Stored in `config/defaults.json` as a flat map of intent name to default params:

```json
{
  "compute.provision": {
    "cpu": "2",
    "ram_gb": "8",
    "storage_gb": "50",
    "os": "ubuntu-22.04",
    "region": "ap-south-1",
    "environment": "staging"
  },
  "db.provision": {
    "engine": "postgres",
    "version": "15",
    "storage_gb": "100",
    "instance": "db.t3.medium",
    "environment": "staging"
  },
  "k8s.deploy": {
    "replicas": "2",
    "environment": "staging"
  },
  "net.lb_provision": {
    "type": "application",
    "scheme": "internal"
  }
}
```

### 5.2 Merge Semantics

`apply_defaults()` merges config defaults under user-specified params:

```python
merged = {**defaults[intent_name], **item["params"]}
```

This means user-specified values always win. The list of which fields came from defaults is tracked in `defaults_applied` on each intent item.

### 5.3 Precedence (highest to lowest)

1. User-specified params (from LLM extraction)
2. Policy enrichment (from OPA defaults)
3. Config defaults (from `defaults.json`)

---

## 6. Confirmation Rules

### 6.1 Configuration

Stored in `config/confirmation.json`:

```json
{
  "always": [
    "compute.terminate",
    "k8s.delete",
    "db.delete",
    "db.access",
    "db.restore"
  ],
  "when_prod": [
    "net.firewall",
    "k8s.deploy",
    "compute.provision"
  ]
}
```

### 6.2 Enforcement

`enforce_confirmation()` is a deterministic function that sets `requires_confirmation: true` based on rules. It runs after `apply_defaults()` so it can see the `environment` param.

- **always** — always requires confirmation regardless of environment
- **when_prod** — requires confirmation only when `params.environment` is `"prod"` or `"production"`

This is enforced in Python, not by the LLM. The LLM's `requires_confirmation` output is overridden by these rules.

### 6.3 Confirmation Gate (Execution Time)

In the execution router:
- **Dry-run mode**: prints a note that confirmation would be required, but does not prompt
- **Simulate mode**: prompts the user with `Proceed? (yes/no)` and cancels if declined

---

## 7. OPA Policy Integration

### 7.1 Architecture

OPA runs as a local sidecar (REST API at `http://localhost:8181`). Python never evaluates Rego — it sends JSON input to OPA and receives JSON output.

### 7.2 Configuration

Stored in `config/policy_config.json`:

```json
{
  "opa_endpoint": "http://localhost:8181",
  "eval_mode": "server",
  "health_path": "/health",
  "policy_paths": {
    "compute": {
      "defaults": "policies/compute/defaults",
      "guardrails": "policies/compute/guardrails"
    },
    "k8s": { ... },
    "db": { ... },
    "net": { ... }
  },
  "timeout_seconds": 3,
  "fallback_on_error": true
}
```

### 7.3 Policy Engine (`policy_engine.py`)

Three functions:

- `health_check(config) -> bool` — GET `{endpoint}/health`, returns true/false
- `query_policy(policy_path, input_data, config) -> dict` — POST to `{endpoint}/v1/data/{policy_path}` with `{"input": input_data}`, returns result dict
- `get_policy_path(domain, policy_type, config) -> str` — looks up path from config, returns empty string if no mapping

On connection failure with `fallback_on_error: true`, returns `{"status": "skipped", "reason": "..."}` instead of raising.

### 7.4 Policy Enrichment (`policy_enricher.py`)

**Stage**: runs after `apply_defaults()`, before `policy_validate()`

For each intent:
1. Extract domain from `intent.split(".")[0]`
2. Look up the `defaults` policy path for that domain
3. Query OPA with `{"intent": intent_name, "params": current_params}`
4. OPA returns: `{"enrichments": {...}, "source": "org_standard"}`
5. For each enrichment field: only set it if the user **didn't already specify it**
6. Track provenance in `policy_applied` list: `[{"field": "encryption", "value": "aes-256", "source": "org_standard"}]`

### 7.5 Policy Validation (`policy_validator.py`)

**Stage**: runs after `policy_enrich()`, before judge and execution

For each intent:
1. Extract domain, look up `guardrails` policy path
2. Query OPA with `{"intent": intent_name, "params": fully_enriched_params}`
3. OPA returns: `{"allow": bool, "violations": [...], "warnings": [...]}`
4. Attach as `policy_validation` on the intent item
5. If any intent has `allow: false`, execution is blocked

### 7.6 Rego Policy Structure

Each domain with policies has 4 files in `policies/<domain>/`:

```
policies/
├── compute/
│   ├── defaults.rego          # Enrichment rules
│   ├── defaults_test.rego     # Unit tests for enrichment
│   ├── guardrails.rego        # Validation rules
│   └── guardrails_test.rego   # Unit tests for validation
├── k8s/
├── db/
└── net/
```

**Defaults Rego pattern** (enrichment):

```rego
package policies.compute.defaults
import rego.v1

default enrichments := {}
default source := "org_standard"

enrichments := result if {
    input.intent == "compute.provision"
    result := _compute_provision_defaults
}

_base_compute_defaults := {
    "encryption": "aes-256",
    "backup_policy": "daily",
    "monitoring": "enabled",
    "tags": "managed-by:intent-provisioner"
}

_env_specific_defaults := {"instance_type": "c5.xlarge"} if {
    input.params.environment == "prod"
} else := {"instance_type": "t3.medium"}
```

**Guardrails Rego pattern** (validation):

```rego
package policies.compute.guardrails
import rego.v1

ALLOWED_REGIONS := {"ap-south-1", "us-east-1", "us-west-2", "eu-west-1"}
MAX_CPU := 32
MAX_RAM_GB := 128
MAX_STORAGE_GB := 2000

default allow := true

allow := false if { count(violations) > 0 }

violations contains msg if {
    region := input.params.region
    not region in ALLOWED_REGIONS
    msg := sprintf("Region '%s' is not allowed. Allowed: %v", [region, ALLOWED_REGIONS])
}

warnings contains msg if {
    cpu := to_number(input.params.cpu)
    cpu > 16
    msg := sprintf("Large instance requested (%d vCPU)", [cpu])
}
```

### 7.7 Domains with OPA Policies (4 of 50)

Only these four domains have Rego policies. The remaining 46 domains pass through enrichment and validation with no-op (enrichment returns no changes, validation returns `allow: true`).

| Domain | Enrichment Rules | Guardrail Rules |
|--------|-----------------|-----------------|
| **compute** | encryption, backup_policy, monitoring, tags, instance_type (env-dependent) | Allowed regions, max CPU/RAM/storage, prod encryption |
| **k8s** | monitoring, resource_limits, network_policy, pod_security | Max replicas, prod min replicas, prod delete protection |
| **db** | backup_retention, monitoring, deletion_protection, encryption | Allowed engines, storage limit, prod multi-AZ + encryption |
| **net** | logging, flow_logs | No SSH/RDP to 0.0.0.0/0, internet-facing LB requires WAF |

### 7.8 Graceful Fallback

If OPA is unavailable:
- `health_check()` returns `false`
- Startup banner shows `OPA Policy : UNAVAILABLE`
- Enrichment skips silently (returns intents unchanged)
- Validation returns `{"allow": true, "violations": [], "warnings": [], "note": "OPA unavailable — policy check skipped"}`
- Execution proceeds normally

---

## 8. Judge LLM

### 8.1 Purpose

A separate local LLM evaluates the classifier's output on every request. The judge provides real-time quality feedback without blocking the pipeline. It answers: "Did the classifier do a good job?"

### 8.2 Configuration

Stored in `config/judge_config.json`:

```json
{
  "enabled": true,
  "model": "<ollama_model_name>",
  "ollama_endpoint": "http://localhost:11434",
  "temperature": 0.1,
  "think": false,
  "log_file": "logs/judge_evaluations.jsonl",
  "dimensions": {
    "intent_correctness":     {"weight": 0.35, "max_score": 10},
    "slot_extraction":        {"weight": 0.30, "max_score": 10},
    "confidence_calibration": {"weight": 0.20, "max_score": 10},
    "safety_flags":           {"weight": 0.15, "max_score": 10}
  }
}
```

The judge model should be different from the classifier model for independent evaluation.

### 8.3 Pipeline Position

```
classify → apply_defaults → policy_enrich → policy_validate → ⚖️ JUDGE → confirm → execute
```

The judge sees the fully enriched, validated classification — the same data that execution will receive. It runs after policy but before confirmation/execution, so its output is visible before any action is taken.

### 8.4 Four Scoring Dimensions

Each dimension is scored 1–10 with a short rationale:

| Dimension | Criteria |
|-----------|----------|
| **Intent Correctness** | Right intent(s) from taxonomy? Correct domain and action? No missing or hallucinated intents? |
| **Slot Extraction** | All user-mentioned entities captured (name, region, size, etc.)? Values accurate? No confusion between user values and defaults? |
| **Confidence Calibration** | Confidence reasonable for the input's ambiguity? Clear requests should be 0.85+. Ambiguous requests should be lower. Penalize over/under-confidence. |
| **Safety Flags** | Does `requires_confirmation` match the safety rules? Destructive operations (terminate, delete, restore) and prod-targeting intents must be flagged. Read-only ops should not. |

### 8.5 Judge Input

The judge receives:
1. **System prompt** containing: the full intent taxonomy, confirmation rules (always + when_prod), scoring rubric, and output format specification
2. **User message** containing: the original user request text and the classifier's JSON output

### 8.6 Judge Output Format

```json
{
  "intent_correctness": {
    "score": 10,
    "rationale": "Correctly identified compute.provision for VM request."
  },
  "slot_extraction": {
    "score": 8,
    "rationale": "Captured name, region, CPU. RAM mapped to default instead of user value."
  },
  "confidence_calibration": {
    "score": 10,
    "rationale": "Unambiguous request; 0.95 confidence is appropriate."
  },
  "safety_flags": {
    "score": 10,
    "rationale": "Correctly flagged requires_confirmation for prod environment."
  },
  "overall_verdict": "pass",
  "summary": "Classification is accurate with correct safety flags."
}
```

### 8.7 Verdict Rules

| Verdict | Condition | Meaning |
|---------|-----------|---------|
| **PASS** | All scores >= 7 | Classification is reliable |
| **WARN** | Any score 4–6 | Classification is usable but has issues |
| **FAIL** | Any score <= 3 | Classification is unreliable |

### 8.8 Dual Output

1. **stdio** — pretty-printed with bar charts, rationale, and verdict icon during interactive and classify modes
2. **JSONL log** — appended to `logs/judge_evaluations.jsonl`, one record per line

### 8.9 Log Record Format

Each line in the JSONL file:

```json
{
  "timestamp": "2026-04-18T12:03:17.114890Z",
  "user_input": "the original user request",
  "classifier_output": {
    "intents": [...],
    "compound": false,
    "latency_s": 2.1
  },
  "judge_evaluation": {
    "intent_correctness": {"score": 10, "rationale": "..."},
    "slot_extraction": {"score": 8, "rationale": "..."},
    "confidence_calibration": {"score": 10, "rationale": "..."},
    "safety_flags": {"score": 10, "rationale": "..."},
    "overall_verdict": "pass",
    "summary": "...",
    "model": "gemma4:31b",
    "latency_s": 8.42,
    "status": "evaluated"
  }
}
```

### 8.10 Graceful Fallback

If the judge model is unavailable (Ollama down, model not pulled, timeout), the error is printed inline and logged. Execution continues normally. The judge never blocks the pipeline.

### 8.11 Runtime Toggle

The judge can be toggled on/off at runtime via the `judge` command in the REPL, without restarting. The `enabled` field in config controls the default state at startup.

---

## 9. Session Context and Conversation State

### 9.1 Architecture

`ContextManager` persists per-team session state to `context/{team}.json`. Each team has independent history and resource tracking.

### 9.2 State Structure

```json
{
  "team": "payments",
  "last_active": "2026-04-18T12:00:00",
  "history": [
    {
      "timestamp": "2026-04-18T11:55:00",
      "user_input": "spin up a VM called web-server",
      "intents": ["compute.provision"],
      "params": [{"name": "web-server", "cpu": "4"}]
    }
  ],
  "resources": {
    "last_vm": {"name": "web-server", "environment": "prod", "region": "us-east-1"},
    "last_service": {"name": "api-gateway", "environment": "staging", "namespace": "default"},
    "last_db": {"name": "prod-db", "environment": "prod"}
  }
}
```

### 9.3 Resource Tracking

When a turn completes, `add_turn()` extracts resources from params:
- `compute.*` intents with `params.name` → updates `last_vm`
- `k8s.*` intents with `params.service` → updates `last_service`
- `db.*` intents with `params.name` → updates `last_db`

### 9.4 Pronoun Resolution

`resolve_references()` replaces the word "it" with the last resource name, but only when the previous turn's domain matches:

- If last intent was `compute.*` → replace `" it "` with `" {last_vm.name} "`
- If last intent was `k8s.*` → replace with `last_service.name`
- If last intent was `db.*` → replace with `last_db.name`

Also handles `" it."` (with period) for end-of-sentence references.

### 9.5 Context Block for LLM

`build_context_block()` generates a text block injected into the system prompt:

```
Last VM: name=web-server, environment=prod, region=us-east-1
Last K8s service: name=api-gateway, environment=staging
Last DB: name=prod-db, environment=prod
Last action: compute.provision
```

### 9.6 History Limits

History is capped at 20 turns. Older turns are dropped on each save.

---

## 10. Execution Layer

### 10.1 Execution Modes

| Mode | Behavior | Side Effects |
|------|----------|-------------|
| **DRY-RUN** (default) | Describes what would happen, shows API endpoint | None |
| **SIMULATE** | Returns realistic fake responses (IDs, IPs, timestamps) | None (fake data only) |

### 10.2 Execution Router (`execution_router.py`)

The `ExecutionRouter` class:

1. Receives the full classification dict
2. If compound, prints header and processes intents sequentially
3. For each intent:
   - Skips `meta.*` intents (informational only)
   - Checks confirmation rules (prompts in simulate mode, notes in dry-run)
   - Dispatches to the appropriate domain handler via `HANDLER_MAP`
   - Catches handler exceptions and wraps in error dict
   - Writes audit log entry
   - Prints formatted result

### 10.3 Handler Map

`HANDLER_MAP` is a dict mapping domain name (string) to handler module. Routing extracts the domain from `intent.split(".")[0]` and looks up the module.

49 domains are registered (all taxonomy domains except `meta`).

### 10.4 Handler Convention

Every handler module in `handlers/` exports exactly one public function:

```python
def handle(intent: str, params: dict, dry_run: bool) -> dict
```

Internal structure:
- Private helper functions: `_fake_id(prefix)`, `_fake_ip()`
- Per-action functions: `_provision(params, dry_run)`, `_delete(params, dry_run)`, etc.
- Dispatch dict mapping intent name to action function

### 10.5 Handler Return Format

```python
# Dry-run
{
    "status": "dry_run",
    "message": "Would provision VM 'web-server' (4 vCPU / 8GB RAM)",
    "would_call": "POST /compute/v1/instances",
    "payload": {<params>}
}

# Simulate
{
    "status": "success",
    "message": "VM 'web-server' provisioned successfully",
    "resource_id": "i-a3f9c2d1",
    "private_ip": "10.42.17.93",
    "state": "running",
    "created_at": "2026-04-18T12:00:00Z"
}

# Error
{
    "status": "error",
    "message": "No compute handler for intent: compute.unknown_action"
}
```

### 10.6 Audit Logging

Every execution (not just errors) is printed as an audit entry:

```
  AUDIT  [DRY-RUN]  2026-04-18T12:00:00Z
         intent  : compute.provision
         event   : executed
         outcome : dry_run
         message : Would provision VM 'web-server'
```

---

## 11. Interactive REPL (`interactive.py`)

### 11.1 Startup Sequence

1. Load all config: taxonomy, defaults, confirmation, model_config
2. Initialize `ExecutionRouter(dry_run=True)`
3. Load judge config, check if enabled
4. Check OPA health
5. Print startup banner with: model name, intent count, exec mode, OPA status, judge status
6. Prompt for team name, load `ContextManager`

### 11.2 Commands

| Command | Action |
|---------|--------|
| `help` | Show intent list, commands, current mode |
| `history` | Show last 10 turns (timestamp + summary) |
| `clear` | Reset session context for current team |
| `switch` | Change to a different team context |
| `mode` | Toggle between DRY-RUN and SIMULATE |
| `classify` | Toggle classify-only mode (skips execution) |
| `judge` | Toggle judge LLM evaluation on/off |
| `quit` / `exit` | Exit the REPL |

### 11.3 Request Processing Flow

For any input that isn't a command:

```
1. resolve_references(user_input)      → "resize it" becomes "resize web-server"
2. build_context_block()               → session context for LLM
3. build_system_prompt(taxonomy, ctx)  → full system prompt
4. classify_intent(...)                → LLM classification
5. policy_enrich(intents)              → OPA defaults
6. policy_validate(intents)            → OPA guardrails
7. print_classification(result)        → show intents, params, tags
8. print_policy_result(item)           → show warnings/violations
9. judge_evaluate(...)                 → judge scores (if enabled)
10. judge_print(evaluation)            → show judge output
11. judge_log(...)                     → append to JSONL
12. if blocked → print block message
13. elif not classify_only → router.execute(result)
14. context.add_turn(user_input, result) → save to session
```

### 11.4 Display Tags

In the classification output, each parameter shows its provenance:

- `(default)` — came from `config/defaults.json`
- `(policy)` — came from OPA policy enrichment
- No tag — user-specified

---

## 12. Evaluation Harness

### 12.1 Test Case Format (`tests/test_cases.json`)

```json
{
  "test_cases": [
    {
      "id": "TC001",
      "utterance": "spin up a 4 core VM in us-east-1",
      "expected_intents": ["compute.provision"],
      "compound": false,
      "reviewed": true
    }
  ]
}
```

Only cases with `"reviewed": true` are executed by the evaluator.

### 12.2 Evaluation Metrics (`evaluate.py`)

- **Intent accuracy** — exact match of expected vs actual intent set
- **Compound detection** — boolean match
- **Per-intent breakdown** — accuracy percentage per intent type, flagged at <80%
- **Latency** — average and P95

### 12.3 Session Test Scenarios (`tests/session_scenarios.json`)

15 multi-turn scenarios covering all 50 domains:
- 120 total turns
- 42 compound turns
- Each scenario tests a realistic workflow (e.g., "New Microservice Launch", "Database Migration")

### 12.4 E2E Session Test (`tests/e2e_session_test.py`)

Runs a 5-turn session through the complete pipeline (classify → defaults → enrich → validate → execute) with verbose output at every stage. Validates handler routing, policy application, and result format.

---

## 13. File Inventory

### 13.1 Python Modules (root)

| File | Lines | Responsibility |
|------|-------|---------------|
| `interactive.py` | ~250 | Main REPL entry point |
| `classify.py` | ~136 | LLM classification + defaults + confirmation |
| `judge.py` | ~230 | Judge LLM evaluation + logging + printing |
| `context_manager.py` | ~141 | Per-team session state + pronoun resolution |
| `execution_router.py` | ~224 | Handler dispatch + confirmation gate + audit |
| `policy_engine.py` | ~68 | OPA REST client |
| `policy_enricher.py` | ~49 | Policy enrichment (fill org defaults) |
| `policy_validator.py` | ~67 | Policy validation (check guardrails) |
| `evaluate.py` | ~214 | Batch evaluation harness |
| `generate_tests.py` | ~207 | Synthetic test case generator |
| `generate_handlers.py` | ~369 | Bulk handler file generator |

### 13.2 Configuration Files

| File | Purpose |
|------|---------|
| `config/taxonomy.json` | 230 intents with names and descriptions |
| `config/defaults.json` | Default params for 4 intent types |
| `config/confirmation.json` | 5 always-confirm + 3 when-prod rules |
| `config/model_config.json` | Classifier LLM model and endpoint |
| `config/judge_config.json` | Judge LLM model, dimensions, log path |
| `config/policy_config.json` | OPA endpoint, policy path mappings |

### 13.3 Handler Files (49 files in `handlers/`)

One file per domain. Each follows the identical pattern described in Section 10.4.

Domains: compute, k8s, db, net, cache, storage, queue, stream, serverless, container, iam, vpc, subnet, vpn, nat, waf, ddos, cdn, cert, secret, kms, volume, filesystem, backup, snapshot, autoscale, apigw, servicemesh, registry, monitor, log, trace, notification, email, workflow, scheduler, batch, etl, warehouse, datalake, search, ml, notebook, iot, transfer, config, compliance, image, dr.

### 13.4 Rego Policies (16 files in `policies/`)

4 domains x 4 files each (defaults, defaults_test, guardrails, guardrails_test).

Domains with policies: compute, k8s, db, net.

### 13.5 Test Files

| File | Purpose |
|------|---------|
| `tests/test_cases.json` | Generated test cases for evaluate.py |
| `tests/session_scenarios.json` | 15 multi-turn scenario definitions |
| `tests/e2e_session_test.py` | Full pipeline session test runner |
| `tests/test_policy.py` | Policy pipeline unit tests (7 tests) |

### 13.6 Runtime-Generated

| Path | Purpose | Format |
|------|---------|--------|
| `context/{team}.json` | Per-team session state | JSON |
| `logs/judge_evaluations.jsonl` | Judge evaluation log | JSONL (one record per line) |
| `tests/results/report_{timestamp}.json` | Evaluation run reports | JSON |

---

## 14. External Dependencies

### 14.1 Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | any | HTTP calls to Ollama and OPA |

No other pip packages. Everything else is Python stdlib (`json`, `os`, `time`, `datetime`, `random`, `string`).

### 14.2 External Services

| Service | Required? | Default Endpoint | Purpose |
|---------|-----------|-----------------|---------|
| **Ollama** | Yes | `http://localhost:11434` | LLM inference for classifier and judge |
| **OPA** | No (graceful fallback) | `http://localhost:8181` | Policy enrichment and validation |

### 14.3 LLM Models

At least one Ollama model is required for the classifier. A second model is recommended (but optional) for the judge. Any Ollama-compatible model works — the system is model-agnostic.

---

## 15. Error Handling Philosophy

- **No exceptions across module boundaries** — every function returns a dict with `"status"` and `"message"`
- **Graceful degradation** — OPA down? Skip policy. Judge down? Skip judge. Execution continues.
- **Fallback values** — missing config fields have sensible defaults (e.g., `model_config.get("model", "qwen3:4b")`)
- **Handler isolation** — handler exceptions are caught by the router and wrapped in error dicts
- **LLM failure** — empty or unparseable LLM responses produce `meta.unknown` with `confidence: 0.0`

---

## 16. Data Flow Example

User says: `"spin up a 4 core VM called payments-api in us-east-1 for production"`

**Step 1 — Classify**
```json
{
  "intents": [{
    "intent": "compute.provision",
    "confidence": 0.95,
    "requires_confirmation": false,
    "params": {"cpu": "4", "name": "payments-api", "region": "us-east-1", "environment": "production"}
  }],
  "compound": false
}
```

**Step 2 — Apply Defaults**
```
params += {ram_gb: "8", storage_gb: "50", os: "ubuntu-22.04"}
defaults_applied: ["ram_gb", "storage_gb", "os"]
```
(cpu, name, region, environment were user-specified so they're not overwritten)

**Step 3 — Policy Enrich (OPA)**
```
params += {encryption: "aes-256", backup_policy: "daily", monitoring: "enabled",
           tags: "managed-by:intent-provisioner", instance_type: "c5.xlarge"}
policy_applied: [{field: "encryption", value: "aes-256", source: "org_standard"}, ...]
```
(instance_type is "c5.xlarge" because environment is production)

**Step 4 — Policy Validate (OPA)**
```
allow: true, violations: [], warnings: []
```
(us-east-1 is allowed, CPU 4 is under 32 max, encryption is aes-256 for prod)

**Step 5 — Confirm**
```
requires_confirmation: true  (because compute.provision + environment=production)
```
(In dry-run: prints note. In simulate: prompts user.)

**Step 6 — Execute**
```json
{
  "status": "dry_run",
  "message": "Would provision VM 'payments-api' (4 vCPU / 8GB RAM / 50GB disk) running ubuntu-22.04 in us-east-1 [production]",
  "would_call": "POST /compute/v1/instances"
}
```

**Step 7 — Judge** (parallel to display)
```
Intent Correctness:      10/10 — Correct intent identified
Slot Extraction:          8/10 — All params captured, minor default confusion
Confidence Calibration:  10/10 — Unambiguous request, 0.95 appropriate
Safety Flags:            10/10 — Correctly flagged for prod confirmation
Verdict: PASS
```

**Step 8 — Save Context**
```json
resources.last_vm = {"name": "payments-api", "environment": "production", "region": "us-east-1"}
```

Next turn: `"now resize it to 8 cores"` → resolves to `"now resize payments-api to 8 cores"`
