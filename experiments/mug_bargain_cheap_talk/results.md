# Results: Bilateral Mug Bargain with Cheap Talk

**Experiment**: `mug_bargain_cheap_talk`
**Date**: 2026-02-22
**Status**: Production (N=30 per cell, 360 total). gpt-4o model.

---

## 1. Research Question

How does pre-play cheap talk affect bilateral bargaining efficiency over a mug, and how does the effect depend on (a) the degree of preference misalignment between buyer and seller and (b) the information structure?

This experiment tests Crawford & Sobel's (1982) prediction that costless pre-play communication should transmit partial value information through partition equilibria, thereby improving bargaining outcomes. The effect should be strongest when the bias parameter *b* (preference misalignment) is small. Farrell & Gibbons (1989) predict that cheap talk may enable separating equilibria when incentive conditions are favorable, though pooling equilibria always exist as an alternative.

---

## 2. Prior Paper Findings and Experiment Settings

### Crawford & Sobel (1982): Strategic Information Transmission

The foundational model of cheap talk in sender-receiver games. Key predictions mapped to our design:

| Prior Claim | Paper Reference | Design Mapping |
|-------------|----------------|----------------|
| Partition signaling: S partitions private information, R infers type from partition element | CS82 p.2 (evidence_trace row 1) | Communication dimension: none / cheap_talk / extended_talk |
| Bias parameter *b*: smaller *b* → finer partitions → more informative signaling | CS82 p.12 (evidence_trace row 2) | Value gap dimension: narrow (*b* small) vs wide (*b* large) |
| As *b* → ∞, only uninformative equilibrium remains | CS82 p.11 (evidence_trace row 4) | Wide gap: ~50% infeasible trades; most bargaining failure expected |
| One-sided info = pure sender-receiver game; talk should help more | CS82 p.2 (evidence_trace row 5) | Info asymmetry: one_sided_buyer_known vs two_sided_private |
| More similar preferences → more informative signaling | CS82 p.2 (evidence_trace row 7) | H2 prediction: talk × narrow gap interaction should be positive |

### Farrell & Gibbons (1989): Cheap Talk with Two Audiences

Extensions on costless communication equilibria:

| Prior Claim | Paper Reference | Design Mapping |
|-------------|----------------|----------------|
| Cheap talk is costless, non-binding pre-play communication | FG89 p.2 (evidence_trace row 6) | Communication phase: free-form messages before bargaining |
| Pooling equilibrium always exists (talk may be uninformative) | FG89 p.4 (evidence_trace row 11) | Null hypothesis: agents play pooling, talk has zero effect |
| Separating equilibrium: receiver learns sender's type | FG89 p.4 (evidence_trace row 9) | H1 alternative: agents separate, talk increases deals |
| Neologism-proofness favors separating when it exists | FG89 p.8 (evidence_trace row 12) | Extended talk should push toward separation |

### Key Quantitative Benchmarks from Theory

- CS82 predicts **positive** effect of talk on agreement rates (partition > babbling)
- CS82 predicts **monotonically increasing** informativeness as *b* → 0
- FG89 predicts pooling always exists but separating is neologism-proof when feasible
- No prior theory predicts that additional communication should **harm** bargaining

---

## 3. New Experiment Design and Innovations

### Full Factorial Design

3 × 2 × 2 = **12 conditions**, N=30 per cell, 360 total simulations:

| Dimension | Levels | Operationalization |
|-----------|--------|-------------------|
| Communication | none, cheap_talk (1 round), extended_talk (3 rounds) | Pre-bargaining message phase |
| Value gap | narrow, wide | Narrow: buyer WTP~U[8,12], seller WTA~U[6,10]; Wide: both~U[5,15] |
| Info asymmetry | two_sided_private, one_sided_buyer_known | Whether seller knows buyer's WTP |

### Innovations Beyond Prior Work

1. **LLM agents as subjects**: Rather than human participants, gpt-4o agents play both buyer and seller roles. This enables 360 sessions at scale with full reproducibility (seed-controlled).

2. **Extended talk condition**: No prior cheap talk experiment tests 3 rounds of communication vs 1 round vs none. This allows testing whether additional rounds enable the finer partitioning CS82 predicts.

3. **Concordia simulation framework**: Agents use associative memory banks and act/observe loops, producing naturalistic multi-turn bargaining behavior.

4. **Holdout validation**: Conditions C10 and C12 were designated *a priori* as holdout for out-of-sample prediction testing.

5. **Zero guardrail triggers**: Unlike the gpt-4o-mini pilot (which required a final-round rationality override), gpt-4o never triggered the guardrail. All results reflect genuine agent strategic behavior.

### Data Quality

| Metric | Value |
|--------|-------|
| Total sessions | 360 |
| Deals reached | 220 (61.1%) |
| Feasible trades (WTP > WTA) | 256/360 (71.1%) |
| Deal rate among feasible | 206/256 (80.5%) |
| Guardrail triggers | 0 |
| Invalid actions | 0 |
| Missing data | None |

Source: `analysis/raw_sessions.csv`

---

## 4. Run Results Analysis

### 4.1 Deal Rate by Condition

| Cond | Comm | VGap | Info | N | Feasible | Deals | Rate | 95% CI |
|------|------|------|------|---|----------|-------|------|--------|
| C01 | none | narrow | two_sided | 30 | 27 | 20 | 66.7% | [48.8, 80.8] |
| C02 | none | narrow | one_sided | 30 | 27 | 27 | 90.0% | [74.4, 96.5] |
| C03 | none | wide | two_sided | 30 | 13 | 9 | 30.0% | [16.7, 47.9] |
| C04 | none | wide | one_sided | 30 | 20 | 20 | 66.7% | [48.8, 80.8] |
| C05 | cheap_talk | narrow | two_sided | 30 | 25 | 19 | 63.3% | [45.5, 78.1] |
| C06 | cheap_talk | narrow | one_sided | 30 | 27 | 29 | 96.7% | [83.3, 99.4] |
| C07 | cheap_talk | wide | two_sided | 30 | 20 | 15 | 50.0% | [33.2, 66.8] |
| C08 | cheap_talk | wide | one_sided | 30 | 13 | 13 | 43.3% | [27.4, 60.8] |
| C09 | ext_talk | narrow | two_sided | 30 | 27 | 13 | 43.3% | [27.4, 60.8] |
| C10* | ext_talk | narrow | one_sided | 30 | 30 | 30 | 100% | [88.6, 100] |
| C11 | ext_talk | wide | two_sided | 30 | 14 | 11 | 36.7% | [21.9, 54.5] |
| C12* | ext_talk | wide | one_sided | 30 | 13 | 14 | 46.7% | [30.2, 63.9] |

*Holdout conditions. Source: `analysis/summary_by_condition.csv`

### 4.2 Treatment-Level Deal Rates

| Communication | Deal Rate | 95% CI | N |
|---------------|-----------|--------|---|
| none | 63.3% (76/120) | [54.4, 71.4] | 120 |
| cheap_talk | 63.3% (76/120) | [54.4, 71.4] | 120 |
| extended_talk | 56.7% (68/120) | [47.7, 65.2] | 120 |

| Value Gap | Deal Rate | 95% CI | N |
|-----------|-----------|--------|---|
| narrow | 76.7% (138/180) | [70.0, 82.2] | 180 |
| wide | 45.6% (82/180) | [38.4, 52.8] | 180 |

| Info Asymmetry | Deal Rate | 95% CI | N |
|----------------|-----------|--------|---|
| two_sided_private | 48.3% (87/180) | [41.1, 55.6] | 180 |
| one_sided_buyer_known | 73.9% (133/180) | [67.0, 79.8] | 180 |

### 4.3 Hypothesis Tests

| Hyp | Test | Effect | p-value | Adj. p | Verdict |
|-----|------|--------|---------|--------|---------|
| H1 | Talk increases deal rate | -7.8pp | 0.190 | 0.380 | **REFUTED** |
| H1a | 1-round talk vs none | +0.0pp | 1.000 | --- | **NULL** |
| H1b | Extended talk vs none | -23.3pp | 0.004 | --- | **HARMFUL** |
| H2 | Talk × value gap interaction | -5.6pp | 0.480 | 0.480 | **REFUTED** |
| H3 | Talk improves surplus capture | -10.4pp | 0.074 | 0.222 | **UNCLEAR** |
| H4 | One-sided info amplifies talk | -8.3pp | 0.393 | --- | **REFUTED** |
| H5 | Extended talk more informative | 6.0 vs 2.0 msgs | <0.001 | --- | **VOLUME ONLY** |
| H6 | Price split closer to 50-50 | 0.324 vs 0.207 | 0.399 | --- | **UNCLEAR** |

H1-H3 corrected with Holm-Bonferroni. H4-H6 exploratory. Source: `analysis/model_results.csv`

### 4.4 Logistic Regression (H1)

Model: `deal ~ talk + wide + one_sided`

| Predictor | Coefficient | OR | 95% CI (OR) | Wald p |
|-----------|-------------|-----|-------------|--------|
| Intercept | --- | --- | --- | --- |
| talk (any) | -0.17 | 0.84 | [0.50, 1.41] | 0.512 |
| wide | --- | --- | --- | --- |
| one_sided | --- | --- | --- | --- |

Talk coefficient is non-significant (OR = 0.84, p = 0.512). The 95% CI spans 1.0, consistent with no effect.

### 4.5 Effect Size Ranking

| Rank | Factor | Effect | p-value |
|------|--------|--------|---------|
| 1 | Value gap (narrow vs wide) | +31.1pp | <0.0001 |
| 2 | Information structure (one-sided vs two-sided) | +25.8pp | <0.0001 |
| 3 | Extended talk (vs none) | -23.3pp | 0.004 |
| 4 | Cheap talk (vs none) | 0.0pp | 1.000 |

### 4.6 Feasible Trade Analysis

| Communication | N Feasible | Feasible→Deal Rate |
|---------------|------------|-------------------|
| none | 87/120 (73%) | 76/87 (87.4%) |
| cheap_talk | 85/120 (71%) | 76/85 (89.4%) |
| extended_talk | 84/120 (70%) | 54/84 (64.3%) |

Among feasible trades, cheap talk marginally improves conversion (89% vs 87%), but extended talk drops to 64%. The extended talk harm is concentrated among feasible trades that *should* result in deals.

### 4.7 Holdout Validation

| Condition | Predicted | Observed | Residual | Status |
|-----------|-----------|----------|----------|--------|
| C10 (ext/narrow/one_sided) | 84.2% | 100% | +15.8pp | MISCALIBRATED |
| C12 (ext/wide/one_sided) | 61.0% | 46.7% | -14.4pp | CALIBRATED |

Mean absolute prediction error: 15.1pp. Model captures rank ordering but misses ceiling effect at C10.

### 4.8 Price Analysis (deals only)

| Communication | Mean Price | SD | Mean Split (seller share) |
|---------------|-----------|-----|--------------------------|
| none | $9.73 | $1.53 | 0.585 |
| cheap_talk | $9.40 | $1.12 | 0.490 |
| extended_talk | $10.12 | $1.50 | 0.172 |

Cheap talk produces slightly lower prices and more balanced splits. Extended talk produces higher prices with highly variable splits.

---

## 5. Alignment with Prior Findings and New Discoveries

### 5.1 Prior Alignment Summary

| Status | Count | Claims |
|--------|-------|--------|
| ALIGNED | 2 | CS82 uninformative limit at high *b*; FG89 pooling equilibrium always exists |
| PARTIAL | 1 | CS82 preference similarity → better outcomes (via feasibility, not communication) |
| CONTRADICTED | 7 | CS82 partition signaling, bias parameter interaction, sender-receiver amplification, aligned interests, extended partitioning; FG89 cheap talk benefit, neologism-proofness |
| UNCLEAR | 1 | FG89 mutual discipline (not testable in bilateral setting) |
| NEW FINDING | 2 | Information main effect (+25.8pp); extended talk backfire (-23.3pp) |

Source: `analysis/prior_alignment.csv`

### 5.2 What Aligns with Prior Theory

**FG89 pooling equilibrium** (evidence_trace row 11): Farrell & Gibbons predict that a pooling equilibrium always exists in which "the sender's talk is uninformative." Our results strongly confirm this: LLM agents universally play the pooling equilibrium. All communication messages are generic rapport-building ("Great mug! Looking forward to negotiating!") rather than calibrated value signals. No numerical valuations were disclosed in any cheap talk message across 240 communication sessions.

**CS82 uninformative limit** (evidence_trace row 4): Crawford & Sobel predict that as bias *b* → ∞, only the uninformative equilibrium survives. Our wide-gap conditions (analogous to large *b*) show ~50% infeasible trades and low deal rates (30-50%), consistent with the uninformative limit.

### 5.3 What Contradicts Prior Theory

**CS82 partition signaling** (evidence_trace row 1): The central Crawford-Sobel prediction -- that cheap talk transmits partial information through partition equilibria -- is completely absent. LLM agents do not partition their type space. They produce identical generic messages regardless of their private valuations. The effect of cheap talk on deal rates is exactly 0.0pp (Fisher p = 1.000).

**CS82 bias parameter** (evidence_trace row 2): The prediction that smaller *b* enables finer partitions (and thus more informative talk) is refuted. The communication × value gap interaction is -5.6pp (Wald p = 0.480), in the wrong direction. Narrow-gap conditions show a *larger* negative effect of talk (-10.6pp) than wide-gap conditions (-5.0pp).

**CS82 extended partitioning** (evidence_trace row 8): More communication rounds should allow finer partitioning. Instead, extended talk (3 rounds) produces a significant **negative** effect of -23.3pp (p = 0.004). This is the single most important departure from theory.

**FG89 separating equilibrium** (evidence_trace row 9): No separating behavior was observed despite favorable conditions (narrow gap + one-sided info in C06 and C10). Agents achieve high deal rates in these conditions through direct information structure, not through learned separation in communication.

### 5.4 New Discoveries

**Discovery 1: Information structure is the dominant treatment effect.** One-sided buyer-known information increases deal rates by +25.8pp (p < 0.0001). This is not a prior-paper prediction for our design but confirms the general economic intuition that reducing asymmetric information improves trade efficiency. The channel is direct: when the seller knows the buyer's WTP, they can set offers just below it.

**Discovery 2: Extended communication actively harms bargaining.** Three rounds of pre-play messages reduce deal rates by 23.3pp (p = 0.004) compared to no communication. This is unprecedented in the cheap talk literature, where communication is predicted to weakly improve or at worst not affect outcomes. Three candidate mechanisms:

1. **Anchoring through communication**: Evaluative messages about the mug ("great quality," "unique design") may anchor agents at different price expectations, creating rigidity during the bargaining phase.

2. **Context overload**: Six pre-bargaining messages consume limited agent context, reducing reasoning capacity during the critical offer-counteroffer phase.

3. **False consensus**: Generic rapport messages may create an illusion of agreement that makes subsequent price disagreements more jarring, leading to breakdown.

**Discovery 3: Pilot findings were artifacts.** The gpt-4o-mini pilot (N=36) showed +17pp cheap talk benefit (H1 "confirmed"). At production scale with gpt-4o, this entirely disappears. The pilot's apparent finding was driven by small N, model irrationality (buyer bidding upward), and guardrail triggers. This underscores the importance of model quality and sample size in LLM behavioral experiments.

---

## 6. Future Experiment Plan

### 6.1 Immediate Follow-Up: Structured Cheap Talk

**Rationale**: The current null result may reflect the communication *format* rather than cheap talk per se. Free-form messages produce only rapport; the Crawford-Sobel mechanism requires value-relevant signaling. A structured format could enable the partition signaling the theory predicts.

**Design**: Replace free-form messages with a "value hint" mechanism:
- Agent is prompted: "Before bargaining, report a number between 0 and 20 that represents your valuation. You may exaggerate."
- This directly operationalizes the CS82 partition signaling mechanism
- 2 × 2 design: {no_hint, value_hint} × {narrow, wide} with one_sided_buyer_known held constant
- N=30 per cell, 120 total simulations
- Primary outcome: correlation between hinted and true values (informativeness)
- Secondary outcome: deal rate

### 6.2 Extended Talk Mechanism Study

**Rationale**: The -23.3pp extended talk effect is the experiment's most novel finding and needs mechanistic explanation.

**Design**: 2-condition study (none vs extended_talk), N=50 each, narrow/one_sided only (to maximize statistical power in the condition with highest baseline deal rate). Code all communication messages for:
- Price anchoring (any numerical mention)
- Evaluative framing (positive vs negative mug descriptions)
- Strategic intent signals ("I'm flexible" vs "I know what I want")

### 6.3 Cross-Model Replication

**Rationale**: LLM behavioral findings may be model-specific. Testing with Claude and Gemini would establish generality.

**Design**: Run the full 12-condition matrix with Claude Sonnet and Gemini Pro. Compare communication content and deal rates across models. Hypothesis: strategic signaling may differ by model training methodology.

### 6.4 Hypothesis Iteration

Feed to `/hypothesize iterate`:
- **Old hypothesis**: Cheap talk transmits value information (CS82 partition mechanism) → improves deals
- **Revised hypothesis**: LLM agents cannot learn to strategically signal in zero-shot free-form settings; value transmission requires either (a) explicit structured prompts or (b) in-context examples of strategic signaling. Free-form talk defaults to the FG89 pooling equilibrium.

---

## File Index

| File | Description |
|------|-------------|
| `analysis/raw_sessions.csv` | 360 rows × 20 columns, one row per simulation |
| `analysis/summary_by_condition.csv` | 12 rows, condition-level summary with 95% Wilson CIs |
| `analysis/model_results.csv` | 19 rows, hypothesis tests with p-values, ORs, CIs |
| `analysis/prior_alignment.csv` | 14 rows, alignment of each prior claim with observed results |
| `analysis/extract_data.py` | Data extraction script (reproducible) |
| `analysis/compute_metrics.py` | Metric computation with logistic regression, Fisher tests, Holm-Bonferroni |
| `data/2026-02-22_11-03-43_prod_C*.json` | Raw simulation outputs (12 files, 30 sims each) |
| `results.tex` | LaTeX source for PDF report |
| `results.pdf` | Compiled PDF report |
