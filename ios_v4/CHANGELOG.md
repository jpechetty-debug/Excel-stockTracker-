# Changelog

All notable changes to the IOS project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v4.3.0] - Unreleased

### Fixed
- **ValuationEngine**: The blended intrinsic value was an unconditional, unweighted average of only 2 models (DCF + Graham), despite `rules/valuation.yaml` describing a 4-model weighted design (dcf 40% / relative_pe 20% / graham 20% / owner_earnings 20%) that was never actually wired in. This was a real calibration bug, not just an incomplete feature: the Graham Number (`sqrt(22.5 * EPS * BVPS)`) is a book-value-based formula designed for stable, asset-heavy value stocks. Averaged 50/50 with DCF, it structurally read high-ROE, asset-light compounders (CAMS, Persistent, Cummins, etc. — low BVPS relative to earnings power) as deeply "overvalued" almost by construction, driving Margin of Safety to figures like -2100% for businesses with excellent Business Scores.
  - Added `calculate_relative_pe` (Gordon Growth justified P/E from payout ratio and growth — no book value) and `calculate_owner_earnings_value` (single-stage Gordon Growth on FCF/share) as two new, independent models.
  - `StepValuation` now loads `rules/valuation.yaml`'s weights (same pattern `StepScoring` already used for `rules/scoring.yaml`) and blends all available models by configured weight, renormalized over whichever models actually computed, instead of a flat average.
  - Confidence is now `len(models) / 4` to match.
  - Guarded against a real edge case found while building this: the two new perpetuity-style models require `growth_rate < discount_rate`, but high-ROE companies (exactly the ones this fix targets) often have a near-term SGR above the discount rate. Growth fed into those two models is now capped to a sustainable spread below the discount rate (mirroring how DCF already separates its near-term growth rate from a lower terminal growth rate), so the fix doesn't silently exclude the companies it's meant to help.
- Rewrote `test_valuation_engine.py` for the 4-model system, including a regression test for the growth-rate-cap edge case above and a test confirming the weighted blend no longer collapses to whatever the Graham Number alone implies for an asset-light profile.

## [v4.2.0] - Unreleased

### Fixed
- **UpdatePlanner**: Fixed a scale-mismatch bug where any field mapped to a `%`-named column (`ROE %`, `ROCE %`, `Margin of Safety %`, `FCF Yield %`, `Revenue Growth %`, `EPS Growth %`, `Growth Rate Used %`, `Target Allocation %`) could get permanently "stuck" showing a raw fraction (e.g. `-0.31`) instead of the intended percentage (e.g. `-31.01`), while every other row displayed correctly. Root cause: `ExcelWriter` multiplies numeric values by 100 for `%`-named columns *at write time*, but `UpdatePlanner`'s change-detection compared the pre-multiplication engine value against the post-multiplication cell value read back from the sheet. If a cell was ever written un-scaled (e.g. before this `*100` transform existed), every subsequent run would recompute essentially the same raw fraction, see it as numerically equal to that stale un-scaled cell, mark the field `UNCHANGED`, and skip writing it forever — freezing that one cell at the wrong scale indefinitely. `UpdatePlanner` now looks up each field's target column and applies the same `*100` transform before comparing, so a stuck cell is detected and self-corrects on the next run.

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
