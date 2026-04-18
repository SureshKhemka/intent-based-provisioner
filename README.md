# Intent-Based Infrastructure Provisioner

A local LLM-powered intent classifier and execution engine for infrastructure provisioning. Developers describe what they want in natural language — the platform classifies the intent, extracts parameters, enriches with org policies, validates guardrails, and executes (or simulates) the right infrastructure action. A separate Judge LLM evaluates every classification for correctness and safety. Fully local: Ollama, no cloud dependencies.

---

## How It Works:

```
Developer types:  "spin up a 4 core VM in prod and open port 8080 on it"
                                    ↓
                        ┌───────────────────────┐
                        │   Intent Classifier   │
                        │  (configurable model   │
                        │   via Ollama)          │
                        └───────────┬───────────┘
                                    ↓
              ┌─────────────────────────────────────────┐
              │  intents: [compute.provision, net.firewall]
              │  params:  {cpu:4, environment:prod, port:8080}
              │  compound: true                          │
              └─────────────────────────────────────────┘
                                    ↓
                      Apply Defaults (config/defaults.json)
                                    ↓
                      Policy Enrichment (OPA defaults)
                   fills: encryption, backups, instance sizing
                                    ↓
                      Policy Validation (OPA guardrails)
                   checks: regions, limits, prod requirements
                                    ↓
              ┌─────────────────────────────────────────┐
              │         ⚖️  Judge LLM Evaluation         │
              │  (separate model scores classification)  │
              │                                         │
              │  Intent correctness      [██████████] 10│
              │  Slot extraction         [████████░░]  8│
              │  Confidence calibration  [█████████░]  9│
              │  Safety flags            [██████████] 10│
              │  Verdict: ✅ PASS                        │
              └─────────────────────────────────────────┘
                       ↓ logged to JSONL          ↓ printed to stdio
                                    ↓
                      Confirmation Gate + Execution Router
                                    ↓
              ┌─────────────────────────────────────────┐
              │  compute_handler → provision VM          │
              │  net_handler     → open firewall port    │
              └─────────────────────────────────────────┘
                                    ↓
                     Audit log + response to user
```

---

## Project Structure

```
intent-based-provisioner/
├── interactive.py          ← Main entry point — interactive REPL
├── classify.py             ← Core classification module
├── judge.py                ← Judge LLM — evaluates classifier output (4 dimensions)
├── context_manager.py      ← Per-team session context (persisted to disk)
├── execution_router.py     ← Routes intents to 49 domain handlers, confirmation gate, audit
├── generate_tests.py       ← Synthetic test case generator
├── generate_handlers.py    ← Bulk handler generator for all domains
├── evaluate.py             ← Evaluation harness (accuracy + latency metrics)
│
├── handlers/               ← Execution stub handlers (one per domain, 49 total)
│   ├── compute_handler.py  ← compute.provision/terminate/resize/start_stop/status/list
│   ├── k8s_handler.py      ← k8s.deploy/scale/rollback/status/logs/exec/delete
│   ├── db_handler.py       ← db.provision/delete/resize/backup/restore/access/status
│   ├── net_handler.py      ← net.dns_create/dns_delete/lb_provision/lb_update/firewall/status
│   ├── cache_handler.py    ← cache.provision/delete/resize/flush/status
│   ├── storage_handler.py  ← storage.bucket_create/bucket_delete/upload/lifecycle/status
│   ├── ...                 ← 43 more domain handlers (iam, vpc, waf, cdn, ml, iot, dr, etc.)
│   └── dr_handler.py       ← dr.create_plan/failover/failback/test/status
│
├── policy_engine.py        ← OPA REST client with health check + graceful fallback
├── policy_enricher.py      ← Queries OPA defaults, merges org-standard values into params
├── policy_validator.py     ← Queries OPA guardrails, blocks execution on violations
│
├── config/                 ← All configuration — no code changes needed
│   ├── taxonomy.json       ← 230 intents across 50 domains
│   ├── defaults.json       ← Default params per intent
│   ├── confirmation.json   ← Which intents need confirmation + conditions
│   ├── model_config.json   ← Classifier LLM model, endpoint, temperature
│   ├── judge_config.json   ← Judge LLM model, endpoint, scoring dimensions, log path
│   └── policy_config.json  ← OPA endpoint, timeout, policy path mappings
│
├── policies/               ← OPA Rego policies (per domain)
│   ├── compute/
│   │   ├── defaults.rego / defaults_test.rego
│   │   └── guardrails.rego / guardrails_test.rego
│   ├── k8s/ db/ net/       ← Same structure per domain
│   └── ...
│
├── logs/
│   └── judge_evaluations.jsonl  ← Judge evaluation log (auto-created)
│
├── tests/
│   ├── test_cases.json          ← Generated + reviewed test cases
│   ├── session_scenarios.json   ← 15 multi-turn session test scenarios (120 turns)
│   ├── e2e_session_test.py      ← End-to-end pipeline test runner
│   ├── test_policy.py           ← Policy pipeline unit tests
│   └── results/                 ← Timestamped eval reports (JSON)
│
└── context/
    └── <team>.json         ← Persisted session context per team (auto-created)
```

---

## Prerequisites

```bash
# LLM (required)
brew install ollama
ollama pull qwen3:4b       # classifier (or any model — configurable)
ollama pull gemma4:31b     # judge (optional — configurable, can be any model)
brew services start ollama

# OPA (optional — enrichment/validation gracefully skipped if unavailable)
brew install opa
```

---

## Quick Start

```bash
python3 interactive.py
```

You will be prompted for a team name (e.g. `payments`, `platform`, `default`). Context is persisted per team across sessions.

---

## Intent Taxonomy

230 intents across 50 domains:

| Domain | Intents | Domain | Intents |
|---|---|---|---|
| **compute** | provision, terminate, resize, start_stop, status, list | **cache** | provision, delete, resize, flush, status |
| **k8s** | deploy, scale, rollback, status, logs, exec, delete | **storage** | bucket_create, bucket_delete, upload, lifecycle, status |
| **db** | provision, delete, resize, backup, restore, access, status | **queue** | create, delete, purge, status |
| **net** | dns_create, dns_delete, lb_provision, lb_update, firewall, status | **serverless** | deploy, delete, invoke, status |
| **iam** | create_role, delete_role, attach_policy, create_user, status | **vpc** | create, delete, peer, status |
| **waf** | create, delete, add_rule, status | **cdn** | create, delete, invalidate, status |
| **secret** | create, delete, rotate, status | **kms** | create_key, rotate, disable, status |
| **monitor** | create_alert, delete_alert, create_dashboard, status | **log** | create_group, delete_group, query, status |
| **ml** | create_endpoint, delete_endpoint, deploy_model, status | **iot** | create_thing, delete_thing, create_rule, status |
| **dr** | create_plan, failover, failback, test, status | **meta** | cost, quota, unknown |

Plus 30 more domains: stream, container, subnet, vpn, nat, ddos, cert, volume, filesystem, backup, snapshot, autoscale, apigw, servicemesh, registry, trace, notification, email, workflow, scheduler, batch, etl, warehouse, datalake, search, notebook, transfer, config, compliance, image.

All intents and descriptions are defined in `config/taxonomy.json`.

---

## Execution Modes

The platform has two execution modes toggled with the `mode` command:

| Mode | Command | Behaviour |
|---|---|---|
| 🔵 DRY-RUN | `mode` | Describes what would happen — no side effects |
| 🟢 SIMULATE | `mode` | Returns realistic fake responses (IDs, IPs, timestamps) |

**Default is DRY-RUN** — safe to use freely. Switch to SIMULATE to see realistic output.

---

## Interactive Commands

| Command | Description |
|---|---|
| `mode` | Toggle between DRY-RUN 🔵 and SIMULATE 🟢 |
| `classify` | Toggle classify-only mode (skips execution) |
| `judge` | Toggle Judge LLM evaluation on/off |
| `help` | Show all intents and commands |
| `history` | Show last 10 turns for current team |
| `clear` | Clear session context for current team |
| `switch` | Switch to a different team context |
| `quit` | Exit |

---

## Example Session

```
> provision a VM called web-server1 in prod with 4 cpu

  Intent     : compute.provision  ⚠️  REQUIRES CONFIRMATION
  Confidence : [████████████████████] 0.96
  Params     :
               name        = web-server1
               cpu         = 4
               environment = prod
               ram_gb      = 8              (default)
               storage_gb  = 50             (default)
               os          = ubuntu-22.04   (default)
               region      = ap-south-1     (default)
               encryption  = aes-256        (policy)
               backup_policy = daily        (policy)
               monitoring  = enabled        (policy)
               instance_type = c5.xlarge    (policy)

  ── Execution ────────────────────────────────────────
  🔵 [DRY-RUN] compute.provision
  ✓ Would provision VM 'web-server1' (4 vCPU / 8GB RAM / 50GB disk)
  → API: POST /compute/v1/instances

> now open port 8080 on it

  🔗 Resolved: "now open port 8080 on web-server1"
  Intent     : net.firewall
  Params     :
               port        = 8080
               name        = web-server1

> mode
  ⚙️  Execution mode set to: SIMULATE 🟢

> backup prod-db

  ⚠️  CONFIRMATION REQUIRED
     Intent : db.backup
     name   : prod-db
  Proceed? (yes/no): yes

  🟢 [SIMULATE] db.backup
  ✓ Snapshot of 'prod-db' created
  snapshot_id     : snap-a3f9c2d1
  size_gb         : 47
  created_at      : 2026-03-22T10:14:33Z
```

---

## Compound Intent Detection

The platform handles multi-action requests in a single call:

```
> spin up a VM and backup prod-db

  ⚡ Compound request — 2 intents detected
  [1] Intent : compute.provision
  [2] Intent : db.backup

  ── Execution ────────────────────────────────────────
  Executing 2 intents sequentially...
```

---

## OPA Policy Layer

The platform integrates with [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) for a two-pass policy check between classification and execution:

```
classify → apply_defaults → policy_enrich → policy_validate → enforce_confirmation → execute
```

### Policy Enrichment (Pass 1)

After defaults are applied, OPA is queried for org-standard values that the user didn't specify. These fill in fields like encryption, backup policies, instance sizing, and monitoring — varying by environment (e.g., prod gets `c5.xlarge`, staging gets `t3.medium`).

**Param precedence**: user-specified > policy enrichment > config/defaults.json

Each enriched field is tracked with provenance (`policy_applied`) and displayed with a `(policy)` tag in the REPL.

### Policy Validation (Pass 2)

After enrichment, fully-assembled params are validated against hard guardrails:

| Domain | Example Guardrails |
|---|---|
| **compute** | Allowed regions, max CPU/RAM/storage, prod must use AES-256 encryption |
| **k8s** | Max replica count, prod requires 2+ replicas, no delete in prod default namespace |
| **db** | Allowed engines (postgres/mysql/mariadb), prod must have multi-AZ + deletion protection |
| **net** | No SSH/RDP open to 0.0.0.0/0, internet-facing LBs require WAF |

Violations **block execution**. Warnings are displayed but don't block.

### Running OPA

```bash
# Start OPA server with the bundled policies
opa run --server policies/

# Run Rego unit tests
opa test policies/
```

### Graceful Fallback

If OPA is unavailable, the platform logs a notice and continues without enrichment/validation. The startup banner shows OPA status:

```
  OPA Policy : CONNECTED ✓        ← OPA is running
  OPA Policy : UNAVAILABLE (...)  ← skipped, execution proceeds normally
```

Configuration is in `config/policy_config.json` (endpoint, timeout, fallback behavior).

---

## Judge LLM

A separate local LLM acts as a judge to evaluate the classifier's output on every request. The judge runs after policy enrichment/validation and before execution, providing real-time quality feedback without blocking the pipeline.

### Pipeline Position

```
classify → apply_defaults → policy_enrich → policy_validate → ⚖️ judge → confirm → execute
```

The judge evaluates the **fully enriched, validated classification** — so it sees what execution will actually receive.

### Four Scoring Dimensions (each 1–10)

| Dimension | What it checks |
|---|---|
| **Intent Correctness** | Did the classifier pick the right intent(s) from the taxonomy? Correct domain, correct action, no missing or hallucinated intents. |
| **Slot Extraction** | Are the extracted parameters complete and accurate? All entities captured (name, region, size)? Values correct vs defaults? |
| **Confidence Calibration** | Is the stated confidence reasonable? Clear requests should be 0.85+, ambiguous ones lower. Penalizes over/under-confidence. |
| **Safety Flags** | Does `requires_confirmation` match the safety rules? Destructive and prod-targeting ops must be flagged. |

### Verdicts

- **PASS** — all scores ≥ 7
- **WARN** — any score 4–6 (classification usable but has issues)
- **FAIL** — any score ≤ 3 (classification is unreliable)

### Example Output

```
  ⚖️  Judge Evaluation (gemma4:31b, 8.42s)
  ──────────────────────────────────────────────────────
  Intent Correctness         [██████████] 10/10
                               Correctly identified 'compute.provision' for VM request.
  Slot Extraction            [████████░░]  8/10
                               Captured name, region, and CPU correctly. RAM mapped to default.
  Confidence Calibration     [██████████] 10/10
                               Unambiguous request; 0.95 confidence is appropriate.
  Safety Flags               [██████████] 10/10
                               Correctly flagged requires_confirmation for prod environment.
  ──────────────────────────────────────────────────────
  Verdict : ✅ PASS
  Summary : Classification is accurate with correct safety flags for production deployment.
```

### Logging

Every evaluation is appended to `logs/judge_evaluations.jsonl` as a structured record:

```json
{
  "timestamp": "2026-04-18T12:03:17.114890Z",
  "user_input": "Spin up a 4 core 16GB VM called payments-api in us-east-1 for production",
  "classifier_output": { "intents": [...], "compound": false, "latency_s": 2.1 },
  "judge_evaluation": {
    "intent_correctness": { "score": 10, "rationale": "..." },
    "slot_extraction": { "score": 8, "rationale": "..." },
    "confidence_calibration": { "score": 10, "rationale": "..." },
    "safety_flags": { "score": 10, "rationale": "..." },
    "overall_verdict": "pass",
    "summary": "...",
    "model": "gemma4:31b",
    "latency_s": 8.42
  }
}
```

### Configuration

Edit `config/judge_config.json`:

```json
{
  "enabled": true,
  "model": "gemma4:31b",
  "ollama_endpoint": "http://localhost:11434",
  "temperature": 0.1,
  "think": false,
  "log_file": "logs/judge_evaluations.jsonl"
}
```

- **`enabled`** — toggle judge on/off (also togglable at runtime with the `judge` command)
- **`model`** — any Ollama model (use a different model than the classifier for independent evaluation)
- **`log_file`** — path to the JSONL evaluation log

### Graceful Fallback

If the judge model is unavailable (Ollama down, model not pulled), the error is printed inline and logged — execution continues normally. The judge never blocks the pipeline.

---

## Confirmation Rules

Defined in `config/confirmation.json`. Two rule types:

- **always** — always require confirmation regardless of environment (e.g. `compute.terminate`, `db.delete`, `db.restore`)
- **when_prod** — require confirmation only when `environment=prod` (e.g. `net.firewall`, `k8s.deploy`)

Confirmation is enforced in Python — not just prompted to the model — so it cannot be bypassed by model output.

---

## Configuration

### Adding a new intent
Edit `config/taxonomy.json` — add one line. No code changes needed.

### Changing the classifier model
Edit `config/model_config.json` — change `"model"` to any Ollama model name.

### Changing the judge model
Edit `config/judge_config.json` — change `"model"` or set `"enabled": false` to disable.

### Changing defaults
Edit `config/defaults.json`. Takes effect on next restart.

### Changing confirmation rules
Edit `config/confirmation.json`. Takes effect on next restart.

---

## Evaluation

### Generate test cases
```bash
python3 generate_tests.py
```
Opens `tests/test_cases.json`. Review each case, set `"reviewed": true`.

### Run evaluation
```bash
python3 evaluate.py
```

Sample output:
```
  Intent accuracy     : 91.2%  (52/57 correct)
  Compound detection  : 85.7%  (6/7 correct)
  Avg latency         : 1.84s
  P95 latency         : 2.31s

  ── Per-intent accuracy ─────────────────────────────
  compute.provision   [██████████] 100%  (5/5)
  db.access           [████████░░]  80%  (4/5)  ⚠
  k8s.exec            [██████░░░░]  60%  (3/5)  ⚠
```

Intents below 80% are flagged with ⚠ for prompt or taxonomy improvement.

### Run policy tests
```bash
# Rego unit tests (requires OPA CLI)
opa test policies/

# Python policy pipeline tests
python3 tests/test_policy.py
```

---

## Roadmap

- [x] Intent taxonomy (230 intents across 50 domains, config-driven)
- [x] Core classifier (configurable model via Ollama, compound detection)
- [x] Defaults and confirmation rules (JSON config)
- [x] Interactive REPL with team context
- [x] Conversation context with pronoun resolution
- [x] Synthetic test generator + evaluation harness
- [x] Execution layer with 49 domain handlers (dry-run + simulate modes)
- [x] OPA policy integration (enrichment + validation with Rego policies)
- [x] Configurable LLM model (`config/model_config.json`)
- [x] Judge LLM for classification quality evaluation (4-dimension scoring + JSONL logging)
- [x] End-to-end session test suite (15 scenarios, 120 turns, all 50 domains)
- [ ] FastAPI service wrapper
- [ ] Fine-tuning on domain-specific utterances
- [ ] Two-stage router for scaling to 500+ intents
