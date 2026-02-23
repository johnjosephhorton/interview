# Analysis Plan: Bilateral Mug Bargain with Cheap Talk

## Primary Estimands

### H1: Cheap talk increases deal rate
- **Estimand**: P(deal | communication ∈ {cheap_talk, extended_talk}) − P(deal | communication = none)
- **Model**: Logistic regression: `deal ~ communication + value_gap + info_asymmetry + communication:value_gap`
- **Primary test**: Wald test on communication coefficient(s), α = 0.05
- **Direction**: Positive (cheap talk increases deals), per Crawford-Sobel prediction that communication transmits some information even with misaligned interests

### H2: Cheap talk effect is larger when value gap is narrow
- **Estimand**: Interaction (communication × value_gap) on deal rate
- **Model**: Same logistic model as H1; test interaction term
- **Direction**: Positive interaction (cheap talk helps more when b is small), per Crawford-Sobel: "the closer b approaches zero, the finer partition equilibria there can be" (p.12)
- **Primary test**: Likelihood ratio test comparing model with and without interaction, α = 0.05

### H3: Cheap talk improves surplus capture
- **Estimand**: E[surplus_captured | cheap_talk] − E[surplus_captured | none], conditional on WTP > WTA
- **Model**: OLS: `surplus_captured ~ communication + value_gap + info_asymmetry + communication:value_gap` (subset: feasible trades only)
- **Primary test**: t-test on communication coefficient, α = 0.05

## Secondary Estimands

### H4: One-sided info structure amplifies cheap talk benefit
- **Estimand**: Triple interaction communication × value_gap × info_asymmetry on deal rate
- **Rationale**: When buyer WTP is known, the bargaining maps to a pure Crawford-Sobel game (seller = Sender). Cheap talk should be more effective because only one side needs to signal.
- **Model**: Full factorial logistic model
- **Test**: LR test, α = 0.10 (exploratory)

### H5: Extended talk produces more informative signals than single-round talk
- **Estimand**: Correlation(communicated_value_signal, true_value) for extended_talk vs. cheap_talk
- **Operationalization**: Code each communication-phase message for any numerical value mentioned. Compute correlation with true WTP/WTA.
- **Test**: Fisher z-test comparing correlations, α = 0.05

### H6: Price split is closer to 50-50 with cheap talk
- **Estimand**: Var(price_split_ratio | cheap_talk) vs Var(price_split_ratio | none)
- **Test**: Levene's test, α = 0.10 (exploratory)

## Heterogeneity Checks

1. **By feasibility**: Repeat H1-H3 separately for sessions where WTP > WTA (feasible) and WTP ≤ WTA (infeasible). In infeasible sessions, cheap talk might *correctly* lead to faster breakdown.
2. **By value realization**: Bin buyer WTP into terciles and check whether cheap talk effects differ by buyer type.

## Out-of-Sample Validation

Conditions C10 and C12 (extended_talk × one_sided_buyer_known × {narrow, wide}) are held out:
1. Fit all models on the 10 non-holdout conditions
2. Generate predicted deal_rate and surplus_captured for C10 and C12
3. Compare predictions to observed values; report RMSE and calibration

## Multiple Comparisons

- Primary hypotheses (H1, H2, H3): Holm-Bonferroni correction across 3 tests
- Secondary hypotheses (H4, H5, H6): reported as exploratory; no family-wise correction but clearly labeled

## Data Extraction

From each simulation transcript, extract:
- `condition_id`: from manifest
- `buyer_wtp`, `seller_wta`: from game manager's hidden state
- `deal`: 1 if transaction, 0 otherwise
- `final_price`: agreed price or null
- `rounds_to_agreement`: count of offer rounds before acceptance
- `comm_messages`: list of all communication-phase messages
- `comm_value_signals`: any numerical values mentioned in communication phase

## Minimum Detectable Effect

With N=30 per cell and 12 cells:
- Deal rate: MDE ≈ 20 percentage points (two-sample z-test, power=0.80, α=0.05)
- Surplus captured: MDE ≈ 0.35 SD (two-sample t-test, power=0.80, α=0.05)

If initial results are noisy, increase to N=50 per cell (600 total simulations).

## Software

- Statistical analysis: Python (statsmodels, scipy)
- Visualization: matplotlib
- Transcript parsing: custom extraction script per `/analyze-results` workflow
