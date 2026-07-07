# Rulebook & Methodology (v4.0)

IOS evaluates companies objectively using externalized YAML configurations. The `ScoringEngine`, `RiskEngine`, and `AllocationEngine` blindly execute these rules, ensuring separation of business logic and software implementation.

## 1. Business Scoring Methodology
Located in `config/rules.yaml` -> `business_score`.

**Purpose**: Identifies the fundamental quality of the underlying business, irrespective of the current stock price.

**Core Metrics**:
- **ROCE**: Weighted at 40%. Evaluates capital efficiency. Minimum threshold typically > 15%.
- **Debt to Equity**: Weighted at 30%. Evaluates balance sheet health. Maximum threshold typically < 0.5.
- **Revenue Growth**: Weighted at 30%. Evaluates business expansion. Minimum threshold typically > 10%.

## 2. Investment Scoring (Risk) Methodology
Located in `config/rules.yaml` -> `investment_score`.

**Purpose**: Identifies the risk of taking a position at the *current* market price.

**Core Metrics**:
- **Margin of Safety (MoS)**: Heavily weighted. The discount of the current price compared to the Intrinsic Value calculated by the Valuation Engine.
- **Valuation Penalty**: If current PE > Historical PE, penalties are applied.
- **Liquidity Penalty**: If Market Cap is micro-cap, penalties are applied.

## 3. Valuation Methodology
Located in `domain/engines/valuation.py`.

**Purpose**: Calculates the intrinsic value of the business.

**Models Used**:
- **DCF (Discounted Cash Flow)**: Projects FCF forward and discounts it back to present value using WACC.
- **Graham Number**: Defines a defensive price based on EPS and BVPS.
- **Historical PE**: Values the company based on its historical multiple.

**Final Value**: IOS takes a blended average of these models, dropping outliers if they exceed standard deviation bounds.

## 4. Allocation Constraints
Located in `config/rules.yaml` -> `portfolio_allocation`.

**Purpose**: Prevents overexposure to single names or sectors.

**Rules**:
- **Max Weight**: No single stock can exceed X% of the portfolio (e.g. 15%).
- **Score Requirement**: To achieve max allocation, Business Score must be > 80.
- **Scale-in**: Allocation targets scale linearly between a score of 50 and 80.

## 5. Rule Versioning Process
Direct modification of the `rules.yaml` without governance destroys the feedback loop. 

**Governance Process**:
1. File a Rule Change Request (e.g. `R-024` in `POST_MORTEMS.md`).
2. Document the evidence supporting the change.
3. Update `rules.yaml`.
4. Update the `active_version` tag inside `rules.yaml` (e.g. from `v4.0` to `v4.1`).
5. This version stamp is permanently attached to the `Provenance` of every score calculated from that point forward.
