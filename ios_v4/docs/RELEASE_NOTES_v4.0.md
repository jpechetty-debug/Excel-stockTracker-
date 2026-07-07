# Release Notes: IOS v4.0
**Date**: 2026-07-07
**Status**: Stable / Frozen

## Executive Summary
IOS v4.0 marks the transition from an experimental script to a production-grade Investment Operating System. The architecture has been completely rewritten using a Pipeline/Command pattern, decoupling domain logic from infrastructure concerns. The framework is now mathematically rigorous, highly auditable, and safe to run against live portfolios.

## Features
- **Strict Layered Architecture**: Total separation of Domain, Engines, Pipeline, and Infrastructure.
- **UpdatePlanner (Firewall)**: Engine outputs never write directly to Excel. The Planner compares metrics, enforces System Zones, and generates a unified `WorkbookUpdatePlan`.
- **Explainability**: Every calculated metric includes a `Provenance` object tracking the source, confidence, timestamp, and rule version.
- **Dry-Run Mode**: Safely test portfolio updates using `--dry-run`, which creates a sandbox copy (`_DRYRUN.xlsx`) and prevents modification of the Master Tracker.
- **Telemetry & Diffs**: Every run produces a `workbook_diff.csv` detailing exact cell changes, and a `run_summary.json` containing provider coverage and timing statistics.
- **Externalized Rules**: Investment policies and column mappings are now fully managed in YAML files, requiring zero code changes to tweak methodologies.

## Tested Environment
- **Python**: 3.10+
- **Providers**: `yfinance`
- **Excel Library**: `openpyxl`
- **OS**: Windows / Linux / macOS

## Known Limitations
- `yfinance` requires `.NS` or `.BO` suffixes for Indian equities. Tickers without these suffixes may return 404 errors.
- Extensive fallback providers are not yet implemented; missing provider data results in a graceful skip (leaving the Excel cell unchanged).

## Roadmap for v4.1 and v5.0
- **v4.1**: Addition of a **Score Drift Report** to explicitly identify why a score changed from the previous run.
- **v5.0**: Introduction of the **Investment Journal Engine**, a feedback loop to track IOS recommendations vs human overrides to statistically validate the methodology over time.
