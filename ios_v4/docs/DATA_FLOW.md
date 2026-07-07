# Data Flow & Pipeline: Institutional Investment Operating System (IOS v4.0)

## Deterministic Pipeline Execution

The system uses a strictly deterministic pipeline (no event bus) to maximize testability and trace execution:

1. **Load Configuration**: Initialize `settings.yaml`, `column_map.yaml`, setup Rule Engine.
2. **Open Workbook**: `WorkbookRepository` loads `Master Universe` and creates a backup.
3. **Read Companies**: Extract current tickers, skip recently updated (via cache check).
4. **Fetch Market Data**: `DataSourceFactory` uses configured provider to fetch batch data concurrently.
5. **Validate Data**: Process raw data through `validators.py` and assign Confidence Scores.
6. **Calculate Financial Metrics**: Domain layer computes trailing metrics, margins, and growth.
7. **Calculate Valuation**: Domain computes DCF, multiples.
8. **Calculate Scores**: `RuleEngine` drives Business Score and Investment Score logic.
9. **Risk Analysis**: Domain analyzes concentration, volatility.
10. **Allocation**: Compute position sizing and Core/Bench/Research categorizations.
11. **Generate Reports**: Presentation layer dumps states to `reports/` CSVs.
12. **Update Workbook**: Safely write calculated fields back to Excel, preserving all manual research.
13. **Finish**: Produce execution benchmarks and metadata.
