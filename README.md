# Intent-Based Infrastructure Provisioner

A local LLM-powered intent classifier and execution engine for infrastructure provisioning, built on Ollama + Qwen3:4b. Developers describe what they want in natural language — the platform classifies the intent, extracts parameters, and executes (or simulates) the right infrastructure action.

---

## How It Works

```
Developer types:  "spin up a 4 core VM in prod and open port 8080 on it"
                                    ↓
                          Intent Classifier
                     (Qwen3:4b via Ollama, no-think mode)
                                    ↓
              ┌─────────────────────────────────────────┐
              │  intents: [compute.provision, net.firewall]
              │  params:  {cpu:4, environment:prod, port:8080}
              │  compound: true                          │
              └─────────────────────────────────────────┘
                                    ↓
                          Execution Router
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
├── context_manager.py      ← Per-team session context (persisted to disk)
├── execution_router.py     ← Routes intents to handlers, confirmation gate, audit log
├── generate_tests.py       ← Synthetic test case generator
├── evaluate.py             ← Evaluation harness (accuracy + latency metrics)
│
├── handlers/               ← Execution stub handlers (one per domain)
│   ├── compute_handler.py  ← compute.provision/terminate/resize/start_stop/status/list
│   ├── k8s_handler.py      ← k8s.deploy/scale/rollback/status/logs/exec/delete
│   ├── db_handler.py       ← db.provision/delete/resize/backup/restore/access/status
│   └── net_handler.py      ← net.dns_create/dns_delete/lb_provision/lb_update/firewall/status
│
├── config/                 ← All configuration — no code changes needed
│   ├── taxonomy.json       ← 29 intents + descriptions
│   ├── defaults.json       ← Default params per intent
│   └── confirmation.json   ← Which intents need confirmation + conditions
│
├── tests/
│   ├── test_cases.json     ← Generated + reviewed test cases
│   └── results/            ← Timestamped eval reports (JSON)
│
└── context/
    └── <team>.json         ← Persisted session context per team (auto-created)
```

---

## Prerequisites

```bash
brew install ollama
ollama pull qwen3:4b
brew services start ollama
```

---

## Quick Start

```bash
python3 interactive.py
```

You will be prompted for a team name (e.g. `payments`, `platform`, `default`). Context is persisted per team across sessions.

---

## Intent Taxonomy

29 intents across 5 domains:

| Domain | Intents |
|---|---|
| **compute** | provision, terminate, resize, start_stop, status, list |
| **k8s** | deploy, scale, rollback, status, logs, exec, delete |
| **db** | provision, delete, resize, backup, restore, access, status |
| **net** | dns_create, dns_delete, lb_provision, lb_update, firewall, status |
| **meta** | cost, quota, unknown |

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
               ram_gb      = 8        (default)
               storage_gb  = 50       (default)
               os          = ubuntu-22.04  (default)
               region      = ap-south-1   (default)

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

## Confirmation Rules

Defined in `config/confirmation.json`. Two rule types:

- **always** — always require confirmation regardless of environment (e.g. `compute.terminate`, `db.delete`, `db.restore`)
- **when_prod** — require confirmation only when `environment=prod` (e.g. `net.firewall`, `k8s.deploy`)

Confirmation is enforced in Python — not just prompted to the model — so it cannot be bypassed by model output.

---

## Configuration

### Adding a new intent
Edit `config/taxonomy.json` — add one line. No code changes needed.

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

---

## Roadmap

- [x] Intent taxonomy (29 intents, config-driven)
- [x] Core classifier (Qwen3:4b, no-think mode, compound detection)
- [x] Defaults and confirmation rules (JSON config)
- [x] Interactive REPL with team context
- [x] Conversation context with pronoun resolution
- [x] Synthetic test generator + evaluation harness
- [x] Execution layer with stub handlers (dry-run + simulate modes)
- [ ] FastAPI service wrapper
- [ ] Fine-tuning on domain-specific utterances
- [ ] Two-stage router for scaling to 100+ intents
