# Results Memo: Competition Anxiety in Vickrey Auctions

**Date:** 2026-02-13
**Status:** Complete
**Experiment:** `vickrey_competition`

---

## Hypothesis

Adding a visible third bidder to a Vickrey auction causes overbidding that is asymmetric by valuation level — larger for low-valuation items where perceived loss probability is higher. Truthful bidding is the dominant strategy regardless of bidder count, but behavioral evidence from human subjects suggests competition perception drives overbidding.

## Design

- **Treatment (between-subjects):** 2-bidder vs. 3-bidder Vickrey auction
- **Moderator (within-subjects):** Valuation level (low $3–$4 vs. high $7–$9)
- **Primary outcome:** Bid/valuation ratio (continuous, per round)
- **Rounds:** 6 per game
- **Sample:** 6 simulations per condition (72 round-level observations)
- **Agent model:** gpt-5-nano (sim_human), gpt-5 (manager)

## Results

### Primary Outcome: Bid/Valuation Ratio

| Condition | Mean Ratio | Std | N |
|-----------|-----------|-----|---|
| 2-bidder | 1.0000 | 0.0000 | 36 |
| 3-bidder | 1.0000 | 0.0000 | 36 |
| **Difference** | **+0.0000** | — | — |

**The simulated human bid exactly its private valuation in every single round, in both conditions.** There is zero overbidding, zero underbidding, and zero variance. The bid/valuation ratio is identically 1.0000 across all 72 observations.

### Interaction: Competition x Valuation Level

|  | 2-bidder | 3-bidder | Difference |
|--|---------|---------|-----------|
| Low valuation ($3–$4) | 1.0000 | 1.0000 | +0.0000 |
| High valuation ($7–$9) | 1.0000 | 1.0000 | +0.0000 |
| **Interaction** | — | — | **0.0000** |

No interaction effect. The competition manipulation has zero effect on bidding at any valuation level.

### Overbidding Frequency

- 2-bidder: 0/36 rounds (0%)
- 3-bidder: 0/36 rounds (0%)

### Total Earnings

| Condition | Mean Earnings | Std |
|-----------|--------------|-----|
| 2-bidder | $12.00 | $0.00 |
| 3-bidder | $9.00 | $0.00 |
| Difference | -$3.00 | — |

The $3.00 earnings difference is entirely mechanical: with 3 truthful bidders, the second-highest bid is higher on average, so winners pay more. This is not a behavioral effect — it's the mathematical consequence of more bidders with truthful bidding.

### AI Bid Correctness

- 2-bidder: 35/36 correct (97%)
- 3-bidder: 35/36 correct (97%)

The AI player bid its true valuation in almost all rounds, as instructed.

## Prediction Evaluation

| Prediction | Expected | Observed | Verdict |
|-----------|----------|----------|---------|
| P1. Main effect (3-bidder bid ratio > 2-bidder) | Higher | No difference (0.000) | **NULL** |
| P2. Interaction (competition x low valuation) | Positive | Zero (0.000) | **NULL** |
| P3. Overbid frequency higher in 3-bidder | Higher | Both 0% | **NULL** |
| P4. Earnings lower in 3-bidder | Lower | -$3.00 (mechanical) | CONFIRMED (trivial) |

## Interpretation

The LLM agent (gpt-5-nano) exhibits **perfectly rational behavior** in the Vickrey auction — bidding exactly its private valuation every time, regardless of the number of competitors. This contrasts sharply with decades of experimental evidence showing that human subjects systematically overbid in Vickrey auctions, especially under competition.

**Key insight:** The simulated human appears to have learned the dominant strategy (truthful bidding) from its training data. It treats the Vickrey auction as a solved game and executes the theoretically optimal strategy with zero deviation. Competition perception, valuation level, and round number have no effect whatsoever.

This result has two interpretations:

1. **LLMs as hyper-rational agents:** LLM agents may not be suitable for studying behavioral biases that depend on bounded rationality, loss aversion, or competition anxiety — biases that arise from cognitive limitations that LLMs don't share.

2. **Insufficient behavioral realism in the sim_human prompt:** The sim_human prompt says "maximize your total earnings" and describes the second-price mechanism. An LLM that has been trained on game theory content will immediately recognize this as a Vickrey auction and apply the dominant strategy. To elicit behavioral deviations, the prompt may need to actively suppress or complicate the agent's theoretical knowledge.

## Evaluation

**Verdict: NO_NULL**
**Diagnosis: HYPOTHESIS**

The hypothesis assumed LLM agents would exhibit human-like competition-sensitive overbidding. They do not. The null result is clean and unambiguous (zero variance). This is not a power issue (we would need infinite data to detect a zero effect) or a design issue (the treatment was implemented correctly). The fundamental assumption — that LLM agents exhibit behavioral biases in well-studied strategic settings — is not supported.

However, the finding itself is potentially interesting: LLM agents are hyper-rational in Vickrey auctions. This contrasts with findings that LLMs exhibit various behavioral biases in other settings (framing effects, anchoring, etc.).

## Next Experiment

**Next archetype: PIVOT**

The competition-manipulation approach doesn't work because the LLM bids truthfully regardless. To study interesting behavioral patterns, we should either:

1. **Make truthful bidding non-obvious:** Switch from Vickrey (where truthful bidding is the dominant strategy and well-known) to first-price auctions (where optimal bidding requires strategic reasoning about opponents' likely bids). First-price auctions should produce more behavioral variance.

2. **Introduce behavioral friction:** Add elements that complicate the decision — e.g., ambiguity about own valuation, time pressure (token limits), or framing effects (art vs. commodity).

3. **Test a different game entirely:** Use a game where LLMs are NOT hyper-rational — e.g., bargaining (where there's no dominant strategy) or public goods (where the social dilemma creates genuine tension).

**Recommended pivot:** First-price auction with competition manipulation. In a first-price auction, the bidder pays their own bid (not the second-highest), so optimal bidding requires shading below valuation. The degree of shading depends on beliefs about opponents — which is exactly where competition anxiety should operate.

```
prior_hypothesis: "Adding competitors causes overbidding in Vickrey auctions, asymmetrically by valuation level"
verdict: NO_NULL
diagnosis: HYPOTHESIS
key_finding: "LLM agents bid exactly their valuation in Vickrey auctions with zero variance, regardless of competition"
key_statistic: "bid/valuation ratio = 1.0000 (SD = 0.000) in both conditions, 72 observations"
dag_variables: "X=competition_size, M=perceived_loss_probability, Y=bid_valuation_ratio, Z=valuation_level"
testable_implications_results: "P1=NULL, P2=NULL, P3=NULL, P4=CONFIRMED(trivial)"
next_archetype: PIVOT
proposed_changes: "Switch from Vickrey to first-price auction where optimal bid-shading requires strategic reasoning, not just dominant strategy execution"
next_hypothesis_sketch: "In a first-price sealed-bid auction, adding competitors causes LLM agents to shade their bids less (bid closer to valuation), because competition anxiety overrides the strategic incentive to shade. The effect is larger for high-valuation items where more surplus is at stake."
```
