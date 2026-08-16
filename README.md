# Inventory Sync Agent

An idempotent multi-warehouse inventory synchronisation agent that detects stock conflicts, automatically resolves discrepancies, and prevents duplicate corrections.

## Project Status

🚧 Currently under development.

## Goal

The goal of this project is to maintain a consistent view of product inventory across independent warehouse management systems.

The agent will:

- Query multiple independent warehouse APIs.
- Compare inventory levels across systems.
- Detect missing SKUs and quantity mismatches.
- Decide whether to automatically correct a conflict or flag it for review.
- Apply corrections to warehouse systems.
- Record actions in a persistent ledger.
- Prevent duplicate corrections, alerts, and transactions across repeated runs.

## Technology

- Python
- FastAPI
- SQLite
- HTTPX
- Pytest