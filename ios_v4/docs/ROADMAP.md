# Roadmap

The philosophy of IOS is that **Software Architecture is secondary to Investment Performance**. 
Features are not added because they are technically interesting; they are added because they solve a proven operational bottleneck or improve investment decision quality.

## Current Status: v4.0 (Frozen)
The core infrastructure, domain modeling, and pipeline execution are complete. The focus is now on Stage 1-3 operational validation using the live portfolio.

---

## Short Term: v4.1 (Score Drift & Usability)
Focuses on making the output easier to interpret week-to-week.

- **Score Drift Report**: Generate a matrix showing how and *why* a company's score changed from the previous run (e.g. `CAMS: 91 -> 93 (+2) | ROCE improved`).
- **Data Freshness Indicators**: Alerting when provider data is older than X days, signaling that a score might be based on stale financials.
- **Provider Fallbacks**: Improved handling of Indian tickers (auto-appending `.NS` or `.BO`) to reduce 404s.

## Medium Term: v5.0 (Investment Journal Engine)
Focuses on creating a feedback loop between IOS recommendations and human decisions.

- **Journal Engine**: A persistence layer for `POST_MORTEMS.md`. Every recommendation (Buy/Hold/Sell) and the human override decision is recorded.
- **Outcome Evaluation**: Automated 6-month lookbacks comparing IOS recommendations against the human overrides to determine which added more value.
- **Methodology Validation**: Statistical analysis of which rules correlate highest with actual future returns.

## Long Term: v6.0 (Portfolio Intelligence)
Focuses on day-to-day workflow management rather than just scoring.

- **Allocation Drift Alerts**: Automated warnings when portfolio weights drift >5% from target allocations.
- **Research Backlog**: Tracking which companies on the watchlist have stale manual research notes.
- **Valuation Triggers**: Automated alerts when a high-quality company's price dips below its Intrinsic Value (MoS > 20%).

## Not Planned
- **Machine Learning (v7.0+)**: AI/ML features will not be considered until the deterministic rule engine (v4.0) is mathematically proven to generate alpha, and a robust historical dataset of manual overrides (v5.0) has been collected.
