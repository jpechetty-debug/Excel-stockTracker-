# Operational Guide (v4.0)

This guide outlines the standard operating procedures for managing your portfolio using IOS.

## Stage 1: Weekly Workflow

**Goal**: Keep pricing and basic facts up to date, and catch sudden drift in valuation or scoring.

1. **Execute IOS**: Run `python run_ios.py` on your Master Tracker.
2. **Review the Diff**: Open `reports/workbook_diff.csv`.
   - *Did any Business Scores drop?*
   - *Did any Valuations cross into buy territory?*
3. **Execute Trades**: Act on the recommendations.
4. **Log Journal**: If you ignored a recommendation, record *why* in `POST_MORTEMS.md`.

## Stage 2: Monthly Review

**Goal**: Ensure data integrity and system health.

1. **Review Data Coverage**: Check `reports/run_summary.json`. 
   - *Are there persistent missing fields from `yfinance`?*
   - *Do we need to add a fallback provider for specific tickers?*
2. **Review False Positives/Negatives**: 
   - *Did IOS recommend a stock you know is a value trap?* 
   - *Did it hate a stock you know has a massive moat?*
   - Do NOT change the rules yet. Just log the anomalies.

## Stage 3: Quarterly Governance

**Goal**: Refine the investment methodology based on evidence.

1. **Review POST_MORTEMS**: Look at the last 3 months of overrides.
   - *Were you right to override IOS? Or did IOS beat your intuition?*
2. **Rule Change Requests**: If the methodology is genuinely flawed (e.g., ROCE thresholds are too strict for financials), propose a change.
3. **Execute Rule Change**:
   - Update `config/rules.yaml`.
   - Bump the `active_version` (e.g., to `v4.1`).
   - Log the change in `CHANGELOG.md`.

## Handling Edge Cases

### Overriding IOS
IOS is a tool, not a dictator. If a company scores a 40 but you know they just signed a transformative contract:
1. DO NOT change the score in the System Zone (IOS will just overwrite it next week).
2. DO use the `Manual Override` column (Manual Zone) to track your adjusted conviction.
3. Log the reasoning in `POST_MORTEMS.md`.

### Missing Tickers
If `yfinance` returns a 404 for an Indian stock, you may need to manually append `.NS` or `.BO` to the ticker symbol in your Master Tracker.
