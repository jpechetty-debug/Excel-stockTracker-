# User Guide (v4.0)

Welcome to the Investment Operating System (IOS) v4.0. IOS is designed to act as your objective co-pilot for equity research and portfolio management.

## Installation & Setup

1. **Prerequisites**: Python 3.10+
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuration**:
   Ensure `config/settings.yaml` and `config/column_map.yaml` exist.
   Ensure your Master Tracker matches the columns defined in `column_map.yaml`.

## Running IOS

IOS operates via a Command Line Interface (CLI). 
To execute a standard run:

```bash
cd ios_v4
python run_ios.py --input "../IOS_Master_Tracker_Filled_9(2).xlsx"
```

### CLI Arguments

| Argument | Description | Example |
|---|---|---|
| `--input` | Path to your Master Workbook. | `--input "my_portfolio.xlsx"` |
| `--dry-run` | Prevents IOS from modifying the original workbook. | `--dry-run` |
| `--limit` | Limits execution to the first N companies. | `--limit 5` |
| `--tickers` | Limits execution to specific tickers. | `--tickers TCS,CAMS` |

### Recommended: Dry Run Testing
When tweaking rules or testing new API logic, always use dry run:
```bash
python run_ios.py --input "master.xlsx" --dry-run
```
This produces `master_DRYRUN.xlsx` and prevents catastrophic overwrites.

## Viewing Results

After execution, IOS generates three artifacts:
1. **The Updated Workbook**: Your `.xlsx` file is updated inline (or copied if `--dry-run`).
2. **The Diff Report**: `reports/workbook_diff.csv` shows every cell that changed.
3. **The Summary**: `reports/run_summary.json` shows API usage, provider coverage, and timing stats.

## Interpreting Output

- **Warnings**: If you see `[Ticker] Valuation warnings...`, it means the data provider was missing critical inputs (e.g., FCF) required to calculate a score. IOS will safely skip those calculations.
- **Failures**: If a fatal error occurs, the pipeline will rollback and exit, leaving your workbook untouched.
