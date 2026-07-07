# Data Dictionary (v4.0)

This document defines the core data model used in IOS. It maps the conceptual fields used by the Python engines to the physical columns in the Excel workbook.

## Core Entities

### 1. `CompanyData`
The fundamental unit of analysis. Represents a single stock.
- `ticker`: Primary key (e.g. `TCS`, `CAMS`).
- `company_name`: Display name.
- `metrics`: Dictionary mapping a field name to a `Metric` object.

### 2. `Metric`
Wraps every data point in the system.
- `value`: The actual data (float, int, string).
- `provenance`: Audit trail object.

### 3. `Provenance`
Answers the question: "Where did this number come from?"
- `source`: E.g. `yfinance`, `Manual`, `Pipeline`.
- `confidence`: `1.0` for audited data, `< 1.0` for estimated/imputed data.
- `timestamp`: When the metric was calculated.

## Field Mappings

The mapping between Python fields and Excel columns is strictly controlled by `config/column_map.yaml`.

### Manual Zone (Untouched by IOS)
IOS is **forbidden** from modifying these columns.
- `Company`: Name of the company.
- `Ticker`: Stock symbol.
- `Industry`: Sector classification.
- `Notes`: Analyst commentary.
- `Manual Override`: User's manual score adjustments.

### System Zone (Managed by IOS)
IOS assumes ownership of these columns. Manual edits here will be overwritten on the next run.
- `Market Cap`: Sourced from `yfinance`.
- `Current Price`: Sourced from `yfinance`.
- `PE Ratio`: Sourced from `yfinance` or calculated by `FinancialEngine`.
- `ROCE`: Calculated by `FinancialEngine`.
- `FCF`: Calculated by `FinancialEngine`.
- `Intrinsic Value`: Calculated by `ValuationEngine`.
- `Margin of Safety`: Calculated by `RiskEngine`.
- `Business Score`: Calculated by `ScoringEngine`.
- `Investment Score`: Calculated by `RiskEngine`.
- `Target Allocation`: Calculated by `AllocationEngine`.

## Update Policy
The `UpdatePlanner` enforces the following rules:
1. **Never overwrite Manual Zone**: Attempted writes to non-System columns are silently rejected.
2. **Skip Nones**: If a provider fails to return data, IOS will leave the existing Excel value intact rather than deleting it.
3. **Audit Trail**: Every modified cell is logged in `workbook_diff.csv` and `app.log` with its `old_val`, `new_val`, and `provenance`.
