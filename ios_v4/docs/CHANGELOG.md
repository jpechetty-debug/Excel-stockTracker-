# Changelog

All notable changes to the IOS project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
