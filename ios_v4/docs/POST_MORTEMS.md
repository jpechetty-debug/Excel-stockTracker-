# Investment Post-Mortems & Governance Log

This document is the permanent record for human investment decisions and methodology changes. It exists to connect the software's recommendations to actual investment outcomes.

---

## 1. Rule Change Requests

*Use this section to propose, approve, and track changes to `rules.yaml`.*

### Example RCR
**ID**: R-024
**Date**: 2026-07-15
**Reason**: ROCE threshold (15%) is too strict for capital-intensive industries (e.g. utilities).
**Evidence**: High-quality utility stocks on the watchlist are artificially suppressed, generating false negatives.
**Expected Impact**: Lower false negatives in the utility sector; overall Business Scores for utilities should rise by ~10 points.
**Approved**: Yes
**Effective Version**: v4.1

---

## 2. Investment Journal

*Use this section to record overrides. Whenever you disagree with IOS, document it here.*

| Date | Company | IOS View | Human Decision | Reason for Override | Outcome (6mo) |
|---|---|---|---|---|---|
| 2026-07-10 | CAMS | Buy | Bought | Agreed with MoS and Business Score. | Pending |
| 2026-08-14 | Lupin | Hold | Increased position | IOS didn't capture the upcoming FDA approval catalyst. | Pending |
| 2026-09-01 | TCS | Reduce | Ignored (Held) | Margin compression is temporary; long-term contracts secure. | Pending |

---

## 3. Quarterly Review Findings

*At the end of every quarter, evaluate the Investment Journal outcomes.*

### Q3 2026 Review (Example)
- **IOS Accuracy**: IOS 'Buy' recommendations outperformed the benchmark by X%.
- **Override Accuracy**: Human overrides underperformed IOS recommendations in 3/4 cases, indicating intuition was flawed regarding short-term catalysts.
- **Action Item**: Stop overriding Valuation penalties. Trust the MoS calculation.
