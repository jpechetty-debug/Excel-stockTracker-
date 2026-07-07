# Changelog

All notable changes to the IOS project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v4.1.0] - Unreleased

### Fixed
- **FinancialEngine**: Removed the hardcoded `revenue_cagr_3y = 0.15` mock. CAGR is now computed from real multi-year revenue history returned by the provider; falls back to a warning (not a fake value) when history is unavailable.
- **YFinanceProvider**: `get_quote()` now returns `dividend_yield` under the correct key (was silently always `None` due to a `dividendYield`/`dividend_yield` mismatch in the consuming step).
- **YFinanceProvider**: Underlying fetch failures (which are not always `requests.RequestException`) are now wrapped in `ProviderUnavailableError` so the existing retry policy actually engages instead of failing fast on the first attempt.
- **ValuationEngine**: Confidence score now divides by 2 (DCF + Graham), the actual number of implemented models, instead of 3.
- **ValuationEngine**: `if dcf_val:` / `if graham_val:` truthiness checks replaced with `is not None`, so a legitimately-zero valuation is no longer discarded as "missing".
- **UpdatePlanner**: Replaced `str(old_val) == str(new_val)` change detection with a type-aware comparison (`math.isclose` for numeric values), preventing float formatting noise from producing false "UPDATED" diffs.

### Added
- **Caching**: `CacheManager` is now wired into `StepFetchData` (segmented by quotes/financials/balance_sheet/cash_flow, respecting `config.cache.enabled`).
- **Validation**: `DataValidator` is now wired into `StepFetchData` for `price`, `pe`, and `roe` before those values reach the engines.
- **Concurrency**: `StepFetchData` now fetches tickers in parallel via `ThreadPoolExecutor`, honoring `--threads` / `application.threads`. Previously this setting existed but had no effect.
- **SessionManager**: The shared `requests.Session` is now actually passed into `yf.Ticker(...)`.
- Unit tests for `FinancialEngine` (CAGR paths), `ValuationEngine` (confidence/truthiness), and `UpdatePlanner` (value comparison).

### Changed
- `MockProvider` now returns yfinance-shaped raw field names (e.g. `"Total Revenue"`) instead of pre-normalized names, so `--provider mock` is usable as a realistic offline stand-in for the full pipeline, not just isolated engine tests.
- Moved `scratch/debug_zero.py` out of the `ios_v4` package to a top-level `scripts/` folder.

## [v4.0.0] - 2026-07-07

### Architecture Freeze & Release Baseline


### Added
- **Pipeline Orchestrator**: Replaced monolithic script with a modular `PipelineRunner` and `PipelineStep` architecture.
- **Domain Models**: Introduced `CompanyData`, `Metric`, `EngineResult`, and `Provenance` for strict type safety and auditability.
- **Engines**: Separated business logic into `FinancialEngine`, `ValuationEngine`, `ScoringEngine`, `RiskEngine`, and `AllocationEngine`.
- **UpdatePlanner**: Implemented a firewall to protect the Excel workbook from erroneous overwrites and enforce System Zones.
- **Telemetry**: Added `run_summary.json` and `workbook_diff.csv` generation in `StepReports`.
- **Dry Run Mode**: Added `--dry-run` CLI flag to safely test execution against real portfolios.
- **Documentation**: Generated complete documentation suite (`ARCHITECTURE.md`, `OPERATIONAL_GUIDE.md`, etc.).

### Changed
- Refactored `ExcelReader` and `ExcelWriter` to interact with `UpdatePlanner` instead of directly parsing business logic.
- Externalized logic into `config/rules.yaml` and column mappings into `config/column_map.yaml`.

### Removed
- Deprecated v3.0 monolithic orchestration scripts (`main.py`, `app.py`).
