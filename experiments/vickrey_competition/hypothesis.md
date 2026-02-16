# Hypothesis Memo: Competition Anxiety in Vickrey Auctions

**Date:** 2026-02-13
**Status:** Pre-design
**Experiment:** `vickrey_competition`

---

## Research Question

In a second-price sealed-bid (Vickrey) auction, does the visible number of competitors cause bidders to deviate from truthful bidding, even though the dominant strategy is invariant to the number of bidders? Standard auction theory delivers a clean prediction: in a Vickrey auction, bidding your true valuation is a weakly dominant strategy regardless of how many others are bidding. Yet a robust finding in experimental economics is that human subjects overbid in Vickrey auctions, and that overbidding intensifies with perceived competition. This experiment tests whether the same bias emerges in LLM-simulated bidders — and critically, whether the effect is moderated by the bidder's private valuation level, creating an asymmetry that theory does not predict.

This matters because if LLM agents reproduce human-like competition-sensitive overbidding in a setting where it is provably irrational, it reveals that these agents are importing behavioral biases from their training data rather than reasoning from first principles about the auction mechanism. The valuation-level interaction sharpens the test: if competition anxiety is driven by *perceived loss probability*, it should be strongest for low-valuation bidders (who are already likely to lose) and weakest for high-valuation bidders (who would win anyway).

---

## Interestingness Argument

### Triviality Scorecard

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| **Prediction surprise** | 3 | The main effect (more competitors causes overbidding) is moderately expected from behavioral auction theory. However, the directional interaction — low-valuation bidders overbid *more* than high-valuation bidders under competition — is genuinely ambiguous. One could equally argue high-valuation bidders overbid more because the stakes of winning are higher. Experts would disagree on the interaction direction. |
| **Literature gap** | 3 | Overbidding in Vickrey auctions is well-documented (Kagel & Levin, 1993; Cooper & Fang, 2008). The effect of bidder count on overbidding has been studied in first-price auctions but is less explored in second-price settings. Testing this in LLM agents (where "competition anxiety" shouldn't exist if the agent reasons correctly) is novel. |
| **Mechanism specificity** | 3 | Two competing mechanisms are identified: (a) *competition anxiety* — more competitors increases perceived loss probability, triggering defensive overbidding; (b) *NPC bid anchoring* — the mere presence of a third bidder's bid provides a reference point that pulls bids upward. The valuation-level interaction helps distinguish them: competition anxiety predicts stronger effects at low valuations (high loss probability), while anchoring predicts uniform effects across valuations. |
| **Boundary conditions** | 4 | The hypothesis includes a clear moderator: valuation level interacts with the competition treatment. The prediction is not "competition causes overbidding" (main effect) but "competition causes overbidding *asymmetrically*, with the largest effect at low valuations" (interaction). This is a testable boundary condition. |
| **Testability in games** | 5 | Bids and valuations are directly observable in game transcripts. The primary outcome (bid-to-valuation ratio) is a simple computation. Treatment assignment (2-bidder vs. 3-bidder) is structural. No latent variables or subjective coding required. |

**Total score: 18 / 25** — Meets threshold. Proceeding without sharpening.

---

## Causal Model

### DAG

```
                    ┌──────────────────────────────────────────────────────┐
                    │                                              (direct) │
                    ▼                                                      │
Competition Size (X) ──→ Perceived Loss Probability (M) ──→ Bid/Valuation Ratio (Y)
                                     ↑                              ↑
                                     │                              │
                          Valuation Level (Z) ──────────────────────┘
                                                          (Z moderates X→M→Y)
```

**Reading the DAG:**
- X → M → Y: More competitors increases perceived probability of losing, which causes overbidding (bidding above valuation)
- X → Y (direct): Competition may directly affect bidding through anchoring or arousal, bypassing the loss-probability channel
- Z → M: Valuation level affects baseline loss probability (low valuation = high baseline loss probability)
- Z → Y (moderation): Valuation level moderates the total effect of X on Y — the competition effect on overbidding is larger when Z is low

### Variable Definitions

| Variable | Type | Operationalization | How the game captures it |
|----------|------|-------------------|--------------------------|
| **Competition Size (X)** | Treatment (between-subjects) | 2-bidder auction (human vs. AI only) vs. 3-bidder auction (human vs. AI + NPC) | Structural: different game variants. 2-bidder game has no NPC; 3-bidder game has a third NPC bidder managed by the manager, whose bids are drawn from a fixed distribution. |
| **Perceived Loss Probability (M)** | Mediator (latent) | The bidder's implicit assessment of how likely they are to lose the auction | Not directly observable — inferred from the pattern of bid adjustments. If overbidding increases with competition only at low valuations (where loss is already likely), this supports the perceived-loss channel. |
| **Bid/Valuation Ratio (Y)** | Outcome (continuous) | Bid divided by private valuation for each round. Ratio = 1.0 means truthful bidding; ratio > 1.0 means overbidding; ratio < 1.0 means underbidding. | Directly computed from transcript: each round records the bid and the assigned valuation. |
| **Valuation Level (Z)** | Moderator (within-subjects) | The bidder's private valuation for a given round, categorized as Low (bottom tercile) or High (top tercile) of the valuation distribution. | Assigned by the game config. Each round has a pre-determined valuation; we analyze rounds grouped by valuation level. |

### Testable Implications

1. **Main effect of competition:** The mean bid/valuation ratio is higher in the 3-bidder condition than the 2-bidder condition. (Direction: positive)
2. **Interaction — Competition x Valuation Level:** The difference in bid/valuation ratio between 3-bidder and 2-bidder conditions is *larger* for low-valuation rounds than for high-valuation rounds. (This is the key prediction that distinguishes the hypothesis from a simple main effect.)
3. **Mechanism signature:** If competition anxiety (not anchoring) drives the effect, then overbidding in the 3-bidder condition should be concentrated in rounds where the NPC's bid is NOT revealed before the subject bids (sealed-bid). If we added a condition where the NPC bid is pre-announced, anchoring would predict the same effect but competition anxiety would predict a reduced effect. (This implication is reserved for iteration — not tested in v1.)
4. **Earnings consequence:** Overbidding in the 3-bidder condition should reduce the bidder's earnings relative to the truthful-bidding benchmark, because winners occasionally pay above their valuation (winner's curse from overbidding in second-price auction).

### Identification Strategy

- **Randomization:** Treatment (2-bidder vs. 3-bidder) is assigned structurally — different game variants. Each simulation is randomly assigned to one condition.
- **Held constant:** Auction mechanism (second-price sealed-bid), private valuation sequences (same valuations in both conditions), number of rounds, AI player strategy (truthful bidding), bid range ($0–$10).
- **NPC design (3-bidder condition):** The third bidder is an NPC controlled by the manager. NPC bids are drawn from a uniform distribution centered on the NPC's private valuation (truthful bidding + small noise). NPC valuations are pre-determined and identical across simulations. The NPC's bid is revealed simultaneously with the AI's bid (after the human bids).
- **Confounds addressed:** (a) Learning effects — controlled by using 5+ rounds with balanced valuation sequences; (b) NPC bid anchoring — partially addressed by not revealing NPC bids until after the human commits; if results are ambiguous, iteration v2 can add a "NPC bid pre-announced" condition. (c) Strategic interaction with NPC — controlled by fixing NPC strategy to truthful bidding.
- **Limitations:** (a) Perceived loss probability (M) is latent — we infer mechanism from the interaction pattern, not direct measurement; (b) LLM "competition anxiety" may differ qualitatively from human competition anxiety; (c) 3 rounds per game may not provide enough within-subject power for the valuation interaction.

---

## Next Steps

This hypothesis is ready for `/design-experiment` to map to a two-condition game design:
- **Condition 1:** `vickrey_2bidder` — standard 2-player Vickrey auction (human vs. AI)
- **Condition 2:** `vickrey_3bidder` — 3-player Vickrey auction (human vs. AI + NPC managed by manager)

The design should specify 5+ rounds per game (to increase within-subject observations for the valuation interaction), balanced valuation sequences, and the NPC's bidding rule.
