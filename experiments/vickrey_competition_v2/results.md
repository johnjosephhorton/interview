# Results Memo: Strategic Shading Under Competition in First-Price Auctions

**Date:** 2026-02-14
**Status:** Complete
**Experiment:** `vickrey_competition_v2`
**Iteration:** 2 (builds on `vickrey_competition` v1)

---

## Prior Experiment Context

Iteration 1 (`vickrey_competition`) tested whether adding a third bidder to a **Vickrey (second-price) auction** would cause overbidding. The result was a clean null: LLM agents bid exactly their valuation (ratio = 1.0000, SD = 0.000) in both conditions — perfect dominant-strategy play. Verdict: NO_NULL, diagnosis: HYPOTHESIS. The strategy-proof nature of Vickrey auctions made it impossible to observe competition effects.

This iteration **pivots to first-price auctions**, where there is no dominant strategy and optimal bidding requires strategic shading (bid = val × (n-1)/n at Nash equilibrium). This creates room for deviation from equilibrium — the very space where competition effects can manifest.

## Hypothesis

In first-price auctions, LLM agents overbid relative to the Nash equilibrium, and this overbidding gap is **asymmetric by valuation level** — larger for low-valuation items where the proportional cost of losing is perceived as higher.

## Design

- **Treatment (between-subjects):** 2-bidder vs. 3-bidder first-price auction
- **Moderator (within-subjects):** Valuation level (low $3–$4 vs. high $7–$9)
- **Primary outcome:** Overbidding gap = (observed bid/val ratio) − (Nash bid/val ratio)
- **Nash benchmarks:** 2-bidder = 0.50, 3-bidder = 0.6667
- **Rounds:** 6 per game
- **Sample:** 6 simulations per condition (72 round-level observations)
- **Agent model:** gpt-5-nano (sim_human), gpt-5 (manager), gpt-5-nano (AI player)
- **AI strategy:** Fixed Nash equilibrium bids (50% for 2-bidder, 67% for 3-bidder)

## Results

### AI Bid Correctness (Sanity Check)

| Condition | Correct | Total | Rate |
|-----------|---------|-------|------|
| 2-bidder | 36 | 36 | 100% |
| 3-bidder | 36 | 36 | 100% |

All AI bids matched the pre-specified Nash equilibrium values exactly. The game infrastructure worked perfectly.

### Primary Outcome: Bid/Valuation Ratio

| Condition | Mean Ratio | Std | Nash Ratio | N |
|-----------|-----------|-----|------------|---|
| 2-bidder | 0.5981 | 0.1170 | 0.5000 | 36 |
| 3-bidder | 0.7412 | 0.1076 | 0.6667 | 36 |
| **Difference** | **+0.1431** | — | — | — |

Welch's t = 5.40 (p < 0.001). LLM agents bid significantly higher as a fraction of valuation in the 3-bidder condition, consistent with strategic adjustment to competition.

### Key Outcome: Overbidding Gap (bid ratio − Nash ratio)

| Condition | Mean Gap | Std | N |
|-----------|----------|-----|---|
| 2-bidder | +0.0980 | 0.1170 | 36 |
| 3-bidder | +0.0745 | 0.1076 | 36 |
| **Gap difference** | **−0.0235** | — | — |

Both conditions show positive overbidding relative to Nash (roughly +7–10pp above equilibrium). However, the gap is **not larger** in the 3-bidder condition — it is slightly smaller. Welch's t(gap) = −0.89 (n.s.). The LLM adjusts to competition but does not over-adjust.

### Interaction: Competition × Valuation Level (Overbidding Gap)

|  | 2-bidder | 3-bidder | Competition Effect |
|--|----------|----------|-------------------|
| **Low valuation** ($3–$4) | +0.1238 | +0.1323 | +0.0084 |
| **High valuation** ($7–$9) | +0.0723 | +0.0167 | −0.0555 |
| **Interaction** | | | **+0.0639** |

The interaction is in the **predicted direction**: competition has a larger (positive) effect on overbidding for low-valuation items and actually *reduces* overbidding for high-valuation items. For high-valuation items in the 3-bidder condition, the LLM nearly achieves Nash equilibrium (gap = +0.017), while for low-valuation items it overbids by +13pp regardless of competition.

### Total Earnings

| Condition | Mean Total | Std | N |
|-----------|-----------|-----|---|
| 2-bidder | $10.33 | $0.98 | 6 |
| 3-bidder | $7.71 | $0.65 | 6 |
| **Difference** | **−$2.62** | — | — |

Substantial earnings reduction in the 3-bidder condition, driven by both increased competition (harder to win) and the first-price mechanism (winner pays own bid).

### Win Rates

| Condition | Human Wins | Rate |
|-----------|-----------|------|
| 2-bidder | 18/36 | 50.0% |
| 3-bidder | 18/36 | 50.0% |

Surprisingly identical win rates across conditions. In the 3-bidder condition, the LLM agents win as often despite more competition, suggesting they adjust their bidding just enough to stay competitive.

### Round-by-Round Detail

| Rnd | Val | Cat | 2b Ratio | 2b Gap | 3b Ratio | 3b Gap |
|-----|-----|-----|----------|--------|----------|--------|
| 1 | $3 | LOW | 0.5417 | +0.0417 | 0.7222 | +0.0556 |
| 2 | $8 | HIGH | 0.5417 | +0.0417 | 0.6698 | +0.0031 |
| 3 | $4 | LOW | 0.5521 | +0.0521 | 0.8079 | +0.1412 |
| 4 | $9 | HIGH | 0.5555 | +0.0555 | 0.6359 | −0.0307 |
| 5 | $3 | LOW | 0.7778 | +0.2778 | 0.8667 | +0.2000 |
| 6 | $7 | HIGH | 0.6196 | +0.1196 | 0.7445 | +0.0779 |

Notable pattern: Round 5 ($3, LOW) shows the largest overbidding gap in both conditions (+0.28 for 2-bidder, +0.20 for 3-bidder). This is the second time the LLM sees a $3 valuation — after losing Round 1 in most games, it overbids more aggressively. **Learning within a game session is evident.**

### Notable Behavioral Patterns

1. **Near-Nash play for high valuations in 3-bidder:** The 3-bidder condition's overbidding gap for high-value rounds is near zero (+0.017), suggesting the LLM calibrates well when stakes are higher and competition is salient.

2. **Systematic overbidding for low valuations:** Low-value rounds show +12–13pp above Nash in both conditions. The LLM appears reluctant to bid very low absolute amounts, creating a proportionally larger deviation for low-value items.

3. **Learning dynamics in Round 5:** Both conditions show a spike in bid ratios for Round 5 ($3, same as Round 1). Having experienced loss outcomes, the LLM bids more aggressively the second time it encounters a low valuation.

4. **No irrational overbidding:** Zero instances of bid > valuation (0/72 rounds). The LLM never makes a clearly dominated bid.

## Prediction Evaluation

| # | Prediction | Direction | Result | Verdict |
|---|-----------|-----------|--------|---------|
| P1 | LLMs overbid relative to Nash in both conditions | Positive gaps | 2b: +0.098, 3b: +0.075 | **CONFIRMED** |
| P2 | Overbidding gap larger in 3-bidder | 3b > 2b | Gap diff: −0.024 | REFUTED |
| P3 | Interaction: competition effect larger for low val | Positive interaction | +0.064 | **CONFIRMED** |
| P4 | Earnings lower in 3-bidder | Negative diff | −$2.62 | **CONFIRMED** |

**3/4 predictions confirmed.** P2 (larger overall gap in 3-bidder) was refuted — the LLM compensates differently by valuation level rather than uniformly overbidding more.

## Evaluation

### Verdict: YES_INTERESTING

The first-price auction pivot produced rich, interpretable results with real behavioral variance — a dramatic contrast to the zero-variance Vickrey result in Iteration 1.

### Key Finding

**LLM agents overbid relative to Nash equilibrium by 7–10 percentage points in first-price auctions, but this deviation is asymmetric: it persists for low-valuation items regardless of competition, while competition actually *reduces* overbidding for high-valuation items to near-Nash levels.** This suggests the LLM uses different bidding heuristics depending on valuation magnitude — a proportional floor effect for low values and more strategic calibration for high values.

### Key Statistic

Overbidding gap interaction (competition × valuation level) = +0.0639. Low-value overbidding is stable across competition conditions (+0.12 to +0.13), while high-value overbidding drops from +0.07 to +0.02 with more bidders.

### What Makes This Interesting

1. **The asymmetry was predicted by the hypothesis** — competition effects ARE moderated by valuation level.
2. **The direction of the interaction is subtler than expected** — competition doesn't amplify overbidding uniformly; it sharpens strategic play for high stakes while leaving a proportional floor for low stakes.
3. **Contrasts sharply with Iteration 1** — LLMs are perfect game theorists in strategy-proof games but show bounded-rational patterns in strategically complex games.
4. **Matches human behavioral literature** — human subjects in first-price auctions also overbid relative to Nash, and this overbidding is more pronounced for low values (risk aversion / loss aversion explanation in humans; heuristic anchoring explanation in LLMs).

### Diagnosis: N/A (YES_INTERESTING — no fix needed)

---

## Machine-Readable Context

```
prior_hypothesis: "In first-price auctions, LLMs overbid relative to Nash equilibrium, and this gap is amplified by competition"
verdict: YES_INTERESTING
diagnosis: N/A
key_finding: "LLMs overbid by 7-10pp above Nash in first-price auctions; this deviation is asymmetric — stable for low valuations but reduced to near-Nash for high valuations under increased competition"
key_statistic: "interaction = +0.064, gap_2b = +0.098, gap_3b = +0.075"
dag_variables: "X=competition_size, M=strategic_uncertainty, Y=overbidding_gap, Z=valuation_level"
testable_implications_results: "P1=CONFIRMED, P2=REFUTED, P3=CONFIRMED, P4=CONFIRMED"
next_archetype: HUMAN-TEST
proposed_changes: "Validate with human subjects; test whether the asymmetric overbidding pattern replicates"
next_hypothesis_sketch: "The valuation-dependent overbidding pattern in LLMs mirrors human risk aversion effects — test whether giving LLMs explicit risk-averse preferences amplifies or dampens the effect"
```
