# Module Map & Directory Structure (IOS v4.0)

## Directory Structure
```
ios_v4/
├── application/
│   ├── pipeline.py       # Deterministic ETL sequence
│   ├── rule_engine.py    # Rule configuration engine
│   └── services.py       # Application services
├── config/
│   ├── settings.yaml     # Application configuration & Scoring Rules
│   ├── column_map.yaml   # Excel column to model mapping
│   └── config_loader.py  # YAML parser
├── domain/
│   ├── company.py        # Core models
│   ├── portfolio.py
│   ├── valuation.py
│   ├── risk.py
│   └── scoring.py
├── infrastructure/
│   ├── providers/        # base.py, yfinance_provider.py, DataSourceFactory
│   ├── repositories/     # excel_repository.py, cache_repository.py
│   ├── validators/       # Data validation layer
│   └── logging/          # Categorized, structured logs
├── presentation/
│   ├── cli.py            # run_ios.py
│   ├── reports.py        # CSV generator
│   └── dashboard.py      # Excel dashboard manager
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── cache/
├── logs/
├── output/
└── run_ios.py            # Root executable wrapper
```

## Dependency Graph
```text
Presentation Layer
        ↓
Application Layer (Pipeline, Rule Engine)
        ↓
Infrastructure Layer (Data Sources, Repositories)
        ↓
Domain Layer (Models, Valuation, Scoring)
```
*(Dependencies flow from top to bottom; the domain layer does not depend on anything above it)*
