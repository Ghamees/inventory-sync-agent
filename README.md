# Inventory Sync Agent

An idempotent multi-warehouse inventory synchronisation agent that detects stock conflicts, decides on corrective actions, applies safe corrections, and prevents duplicate alerts or transactions across repeated runs.

## Overview

This project simulates three independent warehouse management systems that do not share a database.

The Inventory Sync Agent acts as a reconciliation layer between these systems. On each run, it:

1. Queries every warehouse through its independent REST API.
2. Builds a unified view of inventory.
3. Detects quantity mismatches and missing SKUs.
4. Decides how each conflict should be handled.
5. Automatically applies safe corrections when there is sufficient evidence.
6. Flags ambiguous situations for recount or manual review.
7. Records handled conflicts in a persistent SQLite action ledger.
8. Prevents duplicate alerts, recount requests, and unintended repeated actions.

The implementation focuses particularly on **idempotency, deterministic decision-making, auditability, and safe failure behaviour**.

---

## Architecture

```text
Warehouse A API ─┐
                 │
Warehouse B API ─┼──> Inventory Sync Agent
                 │             │
Warehouse C API ─┘             │
                               ├── Conflict Detector
                               │
                               ├── Decision Engine
                               │
                               ├── Action Executor
                               │
                               └── SQLite Action Ledger
```

Each warehouse runs as an independent FastAPI service and has its own inventory state.

```text
Warehouse A → http://127.0.0.1:8001
Warehouse B → http://127.0.0.1:8002
Warehouse C → http://127.0.0.1:8003
```

The agent communicates with the warehouses exclusively through their HTTP APIs rather than directly accessing their Python inventory variables. This models the requirement that the warehouse systems do not share a database.

---

## Agent Workflow

The reconciliation process follows:

```text
QUERY
  ↓
NORMALISE
  ↓
COMPARE
  ↓
DETECT CONFLICT
  ↓
DECIDE ACTION
  ↓
CHECK IDEMPOTENCY
  ↓
EXECUTE
  ↓
RECORD ACTION
```

This separates detection, decision-making, execution, and persistence into individual components.

---

## Conflict Scenarios

### 1. Quantity Mismatch

The default demo contains the following inventory state:

```text
Warehouse A: SKU-100 = 15
Warehouse B: SKU-100 = 15
Warehouse C: SKU-100 = 18
```

The agent detects that the three systems disagree.

Because two independent systems report `15`, the decision engine treats `15` as the majority consensus.

The resulting decision is:

```text
Action: adjust_stock
Target warehouse: warehouse_c
Target quantity: 15
Reason: Majority warehouse consensus
```

The agent then sends an HTTP PATCH request to Warehouse C and changes:

```text
SKU-100: 18 → 15
```

After the correction:

```text
Warehouse A: 15
Warehouse B: 15
Warehouse C: 15
```

The systems are reconciled.

---

### 2. Missing SKU

The demo also contains:

```text
Warehouse A: SKU-300 = 20
Warehouse B: SKU-300 = 20
Warehouse C: SKU-300 = missing
```

The agent identifies this as a `missing_sku` conflict.

It deliberately does **not** automatically create the product in Warehouse C.

Existence in two warehouse systems does not necessarily prove that the SKU should exist in every warehouse. Automatically creating it could introduce an invalid product record or phantom stock.

The decision is therefore:

```text
Action: manual_review
Target warehouse: warehouse_c
Reason: SKU is missing from one or more warehouse systems
```

---

### 3. No Quantity Consensus

The decision engine also handles situations such as:

```text
Warehouse A: SKU-200 = 10
Warehouse B: SKU-200 = 12
Warehouse C: SKU-200 = 14
```

No two systems agree.

Automatically selecting one of these quantities would be unsafe.

The agent therefore chooses:

```text
Action: trigger_recount
Reason: No warehouse quantity consensus
```

This behaviour is covered by the automated test suite.

---

## Decision Policy

The current deterministic policy is:

| Situation | Action |
|---|---|
| All warehouses agree | No action |
| Two or more warehouses agree | Correct the outlier |
| All quantities disagree | Trigger recount |
| SKU missing from warehouse | Manual review |

The decision engine is intentionally deterministic rather than LLM-driven.

Inventory changes affect real operational state. Deterministic rules make decisions:

- reproducible
- explainable
- testable
- auditable
- easier to safely retry

---

## Idempotency

Idempotency is one of the main design concerns of this project.

Running the agent repeatedly must not:

- double-correct inventory
- create duplicate alerts
- create duplicate recount requests
- create phantom transactions
- repeatedly record the same unresolved event

### Conflict Fingerprints

Each detected conflict is converted into a canonical JSON representation.

The canonical representation is hashed using SHA-256 to generate a deterministic conflict identifier.

Conceptually:

```text
SKU-300
Warehouse A = 20
Warehouse B = 20
Warehouse C = missing

        ↓

Canonical conflict representation

        ↓

SHA-256

        ↓

Unique conflict ID
```

The conflict ID is stored in a persistent SQLite action ledger.

---

## SQLite Action Ledger

Handled actions are stored in an SQLite database.

The action table records information including:

```text
conflict_id
sku
action
details
status
created_at
```

Before creating non-mutating actions such as manual-review alerts or recount requests, the agent checks whether that exact conflict has already been completed.

If it has, the action is suppressed.

For example, the first run may produce:

```text
SKU: SKU-300
Type: missing_sku

Decision:
Action: manual_review

Action applied:
Manual review required
```

Running the agent again against the unchanged conflict produces:

```text
SKU: SKU-300
Type: missing_sku

Already handled. No duplicate alert or recount created.
```

This prevents repeated runs from generating duplicate operational noise.

---

## Safe Stock Corrections

Stock corrections use **absolute quantities** instead of relative adjustments.

The agent performs:

```text
Set SKU-100 quantity to 15
```

rather than:

```text
Subtract 3 from SKU-100
```

This distinction is important.

If a relative operation were accidentally executed twice:

```text
18 - 3 = 15
15 - 3 = 12
```

the second execution would corrupt the inventory.

An absolute update:

```text
Set quantity = 15
```

is naturally safer to retry.

---

## Reoccurring Conflicts

A previously handled stock mismatch may genuinely occur again later.

For example:

```text
Initial state:
Warehouse C = 18

Agent corrects:
Warehouse C = 15

Later external change:
Warehouse C = 18 again
```

The agent should not permanently ignore the problem simply because the same state existed previously.

For this reason, persistent suppression is primarily used for non-mutating actions such as:

- manual-review alerts
- recount requests

Stock corrections remain safe to reapply because they set an absolute desired state.

---

## Project Structure

```text
inventory-sync-agent/
│
├── agent/
│   ├── __init__.py
│   ├── action_executor.py
│   ├── action_ledger.py
│   ├── conflict_detector.py
│   ├── decision_engine.py
│   ├── inventory_agent.py
│   └── warehouse_client.py
│
├── warehouses/
│   ├── __init__.py
│   ├── warehouse_a.py
│   ├── warehouse_b.py
│   └── warehouse_c.py
│
├── tests/
│   ├── test_conflict_detector.py
│   ├── test_decision_engine.py
│   ├── test_idempotency.py
│   └── test_missing_sku.py
│
├── reset_demo.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Technologies

The project uses:

- Python
- FastAPI
- Uvicorn
- HTTPX
- SQLite
- Pytest
- Git
- GitHub

The project was developed using Python 3.14.

---

## Requirements

You need:

```text
Python 3.11+
pip
```

Git is also recommended if cloning the repository.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Ghamees/inventory-sync-agent.git
```

Move into the project directory:

```bash
cd inventory-sync-agent
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Warehouse APIs

The three warehouse systems run independently.

Open three terminals.

### Terminal 1 — Warehouse A

```bash
python -m uvicorn warehouses.warehouse_a:app --reload --port 8001
```

Warehouse A will run at:

```text
http://127.0.0.1:8001
```

Inventory endpoint:

```text
http://127.0.0.1:8001/inventory
```

---

### Terminal 2 — Warehouse B

```bash
python -m uvicorn warehouses.warehouse_b:app --reload --port 8002
```

Warehouse B will run at:

```text
http://127.0.0.1:8002
```

Inventory endpoint:

```text
http://127.0.0.1:8002/inventory
```

---

### Terminal 3 — Warehouse C

```bash
python -m uvicorn warehouses.warehouse_c:app --reload --port 8003
```

Warehouse C will run at:

```text
http://127.0.0.1:8003
```

Inventory endpoint:

```text
http://127.0.0.1:8003/inventory
```

---

## Demo Inventory

The initial demo intentionally contains inconsistent data.

Warehouse A:

```text
SKU-100 = 15
SKU-200 = 8
SKU-300 = 20
```

Warehouse B:

```text
SKU-100 = 15
SKU-200 = 8
SKU-300 = 20
```

Warehouse C:

```text
SKU-100 = 18
SKU-200 = 8
SKU-300 = missing
```

Therefore, the agent should detect:

```text
Conflict 1:
SKU-100 quantity mismatch

Conflict 2:
SKU-300 missing from Warehouse C
```

---

## Running the Agent

Once all three APIs are running, open another terminal and execute:

```bash
python agent/inventory_agent.py
```

The first run should detect the quantity mismatch:

```text
SKU: SKU-100
Type: quantity_mismatch

warehouse_a: 15
warehouse_b: 15
warehouse_c: 18
```

The decision engine should choose:

```text
Action: adjust_stock
Reason: Majority warehouse consensus
Target quantity: 15
Target warehouses: ['warehouse_c']
```

The action executor then updates Warehouse C.

The same run also detects the missing SKU:

```text
SKU: SKU-300
Type: missing_sku
```

and creates a manual-review action.

---

## Proving Idempotency

Immediately run the agent again:

```bash
python agent/inventory_agent.py
```

Warehouse C now reports:

```text
SKU-100 = 15
```

Therefore, the quantity conflict no longer exists and no second stock correction is performed.

The missing `SKU-300` conflict still exists, but the ledger recognises that it has already been handled.

The agent outputs:

```text
Already handled. No duplicate alert or recount created.
```

This demonstrates that repeated execution does not create duplicate operational actions.

---

## Resetting the Demo

A reset utility is included to make the demonstration reproducible.

Run:

```bash
python reset_demo.py
```

This removes the local SQLite action ledger.

You should then restart Warehouse C so its in-memory inventory returns to:

```text
SKU-100 = 18
SKU-300 = missing
```

The system is then ready to demonstrate the complete flow again.

---

## Running the Tests

Run the complete test suite with:

```bash
python -m pytest tests/ -v
```

The current test suite contains six tests covering the main behaviours.

Expected result:

```text
6 passed
```

---

## Test Coverage

The automated tests verify:

### Matching inventory

When all warehouses contain the same quantities:

```text
15 / 15 / 15
```

no conflict is produced.

### Quantity mismatch detection

The system correctly detects:

```text
15 / 15 / 18
```

as a quantity mismatch.

### Majority consensus

The decision engine selects `15` as the authoritative quantity when two systems agree.

### Ambiguous quantities

A state such as:

```text
10 / 12 / 14
```

does not result in an arbitrary stock correction.

A recount is requested instead.

### Missing SKU

A product present in Warehouse A and B but missing from Warehouse C is detected and sent for manual review.

### Idempotency

Once a conflict has been recorded as completed, the ledger recognises the same conflict on subsequent checks.

---

## Key Engineering Decisions

### 1. Three Independent APIs

Each warehouse is represented by its own FastAPI application running on a different port.

The reconciliation agent communicates with them through HTTP.

This avoids coupling the agent directly to warehouse implementation details.

### 2. Deterministic Resolution

Stock reconciliation uses explicit business rules rather than probabilistic decision-making.

This makes the behaviour easier to explain, test, and audit.

### 3. Majority Consensus

When two independent warehouse systems agree and one differs, the agreeing quantity is treated as the current source of truth.

This is appropriate for the demonstration but would be configurable in a production system.

### 4. Conservative Missing-SKU Handling

Missing products are not created automatically.

A missing product can represent:

- catalogue configuration differences
- discontinued products
- delayed replication
- warehouse-specific inventory
- an actual data error

Manual review is therefore safer.

### 5. Persistent Idempotency Ledger

SQLite provides lightweight persistence across separate executions of the agent.

The agent therefore remembers previously handled conflicts even after the Python process exits.

---

## Failure and Edge-Case Behaviour

The project deliberately handles several non-happy-path scenarios.

### No consensus

The agent refuses to guess and requests a recount.

### Missing SKU

The agent escalates rather than creating phantom stock.

### Repeated execution

Previously handled alerts are suppressed.

### Reoccurring quantity mismatch

Absolute stock updates make it safe to reconcile the desired state again.

---

## Current Limitations

This project is intentionally lightweight and designed as a technical demonstration rather than a production warehouse platform.

Current limitations include:

- warehouse inventory is stored in memory
- no API authentication
- no distributed locking
- no concurrent-agent protection
- no retry queue
- no exponential backoff
- no dead-letter queue
- no event streaming
- no real email/Slack notification integration
- no warehouse-specific trust configuration
- no production database
- no transaction coordination across warehouse systems
- no inventory reservation model

---

## What I Would Do Next

With more development time, I would extend the system in several areas.

### Persistent Warehouse Storage

Replace the in-memory dictionaries with independent databases for each warehouse.

### Distributed Locking

Introduce a distributed lock or database-level claim mechanism so multiple agent instances cannot process the same conflict concurrently.

### Retry Strategy

Add retry policies with exponential backoff for temporary warehouse API failures.

### Transaction State Machine

Track actions through states such as:

```text
detected
pending
executing
completed
failed
retrying
```

This would make recovery from partial failures more robust.

### Inventory Snapshots

Store warehouse snapshots so the system can determine whether a conflict is:

- new
- unchanged
- resolved
- reoccurring

### Real Notifications

Integrate a notification provider for manual-review and recount actions.

For example:

```text
Slack
Email
PagerDuty
Internal operations dashboard
```

### Observability

Add:

- structured JSON logging
- metrics
- reconciliation latency
- conflict counts
- API failure rates
- correction counts

### Docker Compose

Containerise each warehouse service and the reconciliation agent so the complete environment can be started with one command.

### Authentication

Add service authentication and signed requests between the reconciliation agent and warehouse APIs.

### Configurable Trust Rules

Real warehouse systems may not have equal authority.

A production implementation could assign trust levels such as:

```text
Primary WMS > regional WMS > fulfilment cache
```

The decision engine could then use trust scores instead of simple majority consensus.

### Integration Testing

Add end-to-end tests that start all warehouse APIs, introduce a conflict, run reconciliation, verify the remote correction, run reconciliation again, and verify that no duplicate action occurs.

---

## Three-Minute Demo Flow

The demonstration is designed to show the complete behaviour quickly.

### 1. Show the independent warehouse systems

Show that Warehouse A, B, and C are running independently.

Highlight:

```text
Warehouse A → SKU-100 = 15
Warehouse B → SKU-100 = 15
Warehouse C → SKU-100 = 18
```

Also show that Warehouse C does not contain `SKU-300`.

### 2. Run the agent

Execute:

```bash
python agent/inventory_agent.py
```

Explain that the agent queries each API rather than sharing their internal state.

### 3. Show conflict detection

Highlight:

```text
SKU-100
quantity_mismatch
15 / 15 / 18
```

### 4. Show the decision

Highlight:

```text
Action: adjust_stock
Reason: Majority warehouse consensus
Target quantity: 15
```

### 5. Show the correction

The agent updates Warehouse C:

```text
18 → 15
```

### 6. Show missing-SKU handling

Highlight:

```text
SKU-300
missing_sku

Action: manual_review
```

Explain why automatically creating a missing product could create phantom inventory.

### 7. Run the agent again

Execute:

```bash
python agent/inventory_agent.py
```

The quantity mismatch should now be gone.

For the unchanged missing SKU, the agent should display:

```text
Already handled. No duplicate alert or recount created.
```

This demonstrates idempotency.

### 8. Show automated tests

Run:

```bash
python -m pytest tests/ -v
```

Show:

```text
6 passed
```

---

## Summary

This project demonstrates an autonomous reconciliation workflow across disconnected warehouse systems:

```text
Observe → Detect → Decide → Act → Record → Verify
```

The implementation demonstrates:

- multiple independent data sources
- inventory comparison
- realistic conflict detection
- automatic corrective action
- conservative handling of ambiguous data
- persistent action tracking
- idempotent repeated execution
- automated tests
- reproducible demonstration setup

The main design principle is that inventory reconciliation should be **safe, deterministic, auditable, and repeatable**.