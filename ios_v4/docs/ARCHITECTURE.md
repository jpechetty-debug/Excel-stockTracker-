# Architecture Overview (v4.0)

## Layered Architecture

IOS v4.0 uses a strict layered architecture to separate concerns, improve testability, and isolate the core investment logic from external dependencies (like Excel or network providers).

### 1. Domain Model (`domain/`)
The absolute core of the system. Contains the vocabulary of the investment framework (`CompanyData`, `Metric`, `Provenance`, `EngineResult`). 
- **Rule**: Has zero dependencies on anything else in the system.

### 2. Engines (`domain/engines/`)
The business logic. They take Domain Models as input and return `EngineResult` objects as output.
- **Financial Engine**: Calculates objective facts (e.g. FCF, EPS).
- **Valuation Engine**: Calculates pricing facts (e.g. DCF, Graham).
- **Scoring Engine**: Evaluates investment policy (e.g. Business Score).
- **Risk Engine**: Decomposes risk factors.
- **Allocation Engine**: Applies constraints for portfolio weights.

### 3. Pipeline Layer (`pipeline/`)
The orchestrator. It executes the steps in a specific sequence, passing the `ExecutionContext` and `PipelineArtifacts` between steps. It acts as the glue that binds the engines, infrastructure, and domain together.

### 4. Infrastructure Layer (`infrastructure/`)
Handles the dirty work of the real world.
- **Excel Module**: Reading/writing, system zone validation, diff generation.
- **Providers**: Network calls (e.g. `yfinance`), rate limiting, retries.
- **Logging**: Formatting output and audit trails.

## Domain Boundaries
By defining strict boundaries, the core engines don't know that data comes from `yfinance` or is saved to an `.xlsx` file. If we decide to swap out `yfinance` for Bloomberg, or `.xlsx` for PostgreSQL, the Domain and Engine layers require zero changes.

## Design Principles
1. **Explainability Over Black Boxes**: Every metric must have a `Provenance` (Source, Provider, Confidence, Rule Version, Timestamp) attached to it.
2. **Defensive Excel Parsing**: The `UpdatePlanner` acts as a firewall between engine outputs and the physical workbook file. 
3. **Graceful Degradation**: If an API provider fails to return a specific metric, the system logs a warning and skips the update rather than crashing or overwriting the workbook with `None`.

## Extension Points
- **Providers**: New data providers can be added to `infrastructure/providers/` simply by subclassing `BaseProvider`.
- **Rules**: New rules can be added to `config/rules.yaml` without changing the `ScoringEngine` Python code.
- **Pipeline Steps**: The orchestration can be extended by creating a new `PipelineStep` subclass and registering it in `run_ios.py`.
