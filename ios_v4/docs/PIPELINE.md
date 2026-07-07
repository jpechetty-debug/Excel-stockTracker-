# Pipeline Architecture (v4.0)

The core orchestration of IOS v4.0 uses the **Command / Pipeline Pattern**. This ensures each operational unit does exactly one job, is easily testable, and fails gracefully.

## Execution Flow

The `PipelineRunner` acts as the conductor. It instantiates the `ExecutionContext` and sequentially executes the following steps:

### 1. `StepLoadConfig`
Loads `settings.yaml` and `column_map.yaml`, validates their structures, and injects them into the `ExecutionContext`.

### 2. `StepOpenWorkbook`
Uses `ExcelReader` to parse the `master_file`, applying `--limit` or `--tickers` if specified. Outputs `List[CompanyData]` and `existing_data` into `context.artifacts`.

### 3. `StepFetchData`
Batches requests to the provider layer (e.g., `yfinance`). Handles rate-limits and timeouts. Outputs raw dictionary metrics to `context.artifacts.market_data`.

### 4. `StepFinancial`
Passes `market_data` into the `FinancialEngine`. Outputs derived objective metrics (e.g., Margins) to `context.artifacts.financials`.

### 5. `StepValuation`
Passes data into the `ValuationEngine`. Outputs pricing facts to `context.artifacts.valuations`.

### 6. `StepScoring`
Loads business rules from the configuration context and runs the `ScoringEngine`. Outputs `context.artifacts.business_scores`.

### 7. `StepRisk`
Loads risk rules and runs the `RiskEngine`. Outputs `context.artifacts.risks`.

### 8. `StepAllocation`
Loads portfolio constraints and runs the `AllocationEngine`. Outputs `context.artifacts.allocations`.

### 9. `StepWriteExcel`
Transforms artifacts into `Metric` domains, runs the `UpdatePlanner` to generate a diff, and calls `ExcelWriter` to physically update the tracker.

### 10. `StepReports`
Generates the run telemetry, provider coverage reports, and writes `run_summary.json`.

## Error Handling

If any `validate()` or `execute()` method returns `False` or raises an exception:
1. The Pipeline is halted.
2. The `context.state` transitions to `FAILED`.
3. The `PipelineRunner` iterates backwards through executed steps, calling `rollback()`.
