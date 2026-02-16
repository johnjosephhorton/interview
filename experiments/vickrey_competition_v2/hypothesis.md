# Hypothesis Memo: Strategic Shading Under Competition in First-Price Auctions

**Date:** 2026-02-13
**Status:** Pre-design
**Experiment:** `vickrey_competition_v2`
**Version:** v2 — Iteration of `vickrey_competition`

---

## Prior Experiment Context

**Experiment:** `vickrey_competition` (Iteration 1)
**Tested:** Whether adding a third bidder to a Vickrey (second-price) auction causes overbidding in LLM agents.
**Found:** The simulated human bid exactly its private valuation in every single round (bid/valuation ratio = 1.0000, SD = 0.000, N = 72) regardless of whether 2 or 3 bidders were present. Zero overbidding, zero variance, zero treatment effect.
**Verdict:** NO_NULL
**Diagnosis:** HYPOTHESIS — The Vickrey auction has a well-known dominant strategy (truthful bidding), and the LLM executed it perfectly. The game was "too solved" for behavioral effects to emerge.
**Iteration strategy:** PIVOT — Switch to a game where optimal play requires strategic reasoning, not dominant strategy execution.

---

## Research Question

Given that LLM agents execute the dominant strategy perfectly in Vickrey auctions (where truthful bidding is optimal regardless of competition), does switching to a **first-price auction** — where optimal bidding requires strategic shading below valuation — reveal competition-sensitive behavioral patterns? In first-price auctions, the winner pays their own bid, so bidders face a fundamental tradeoff: bid high (more likely to win, but lower profit) vs. bid low (higher profit if you win, but more likely to lose). The Nash equilibrium bid is valuation × (n-1)/n, which changes with the number of bidders: optimal shading is 50% with 2 bidders but only 33% with 3 bidders.

The core question is whether LLM agents can compute and execute this non-trivial equilibrium, and whether competition causes them to systematically deviate from it. If competition anxiety exists in LLMs, they should overbid relative to the Nash prediction — bidding closer to their valuation than the equilibrium prescribes, especially under higher competition.

This matters because the Iteration 1 result established that LLMs are hyper-rational in games with dominant strategies. First-price auctions test whether this rationality extends to games requiring Bayesian reasoning about opponents.

---

## Interestingness Argument

### Triviality Scorecard

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| **Prediction surprise** | 4 | The Iteration 1 result makes this genuinely uncertain. LLMs were perfectly rational in Vickrey auctions — but first-price auctions have no dominant strategy. Will they compute the Nash equilibrium? Overbid? Underbid? The prior result makes the answer non-obvious: if they're rational in Vickrey, maybe they compute the equilibrium here too. But the equilibrium requires reasoning about opponent beliefs, which is qualitatively harder. Experts would disagree. |
| **Literature gap** | 4 | Human overbidding in first-price auctions is well-documented (Cox, Roberson & Smith, 1982; Kagel & Levin, 1993). But LLM bidding in first-price auctions with varying competition is essentially unexplored. The Iteration 1 Vickrey result provides a novel contrast point: rational in second-price, but what about first-price? |
| **Mechanism specificity** | 3 | Two competing explanations for deviation from Nash: (a) *competition anxiety* — more bidders increases fear of losing, causing overbidding; (b) *computational difficulty* — the Nash equilibrium is harder to compute with more bidders (requires knowing n). The deviation-from-Nash measure separates strategy execution from bias. Valuation-level interaction helps further: anxiety predicts larger deviations at low valuations (more fear of losing), while computational difficulty predicts uniform deviations. |
| **Boundary conditions** | 4 | Multiple moderators: (1) competition level (2 vs 3 bidders), (2) valuation level (low vs high), (3) game type as a meta-moderator (Vickrey = rational, first-price = ?). The prior result provides a direct boundary condition: LLMs are rational when a dominant strategy exists, but may not be when strategic reasoning is required. |
| **Testability in games** | 5 | Bids, valuations, and the Nash equilibrium benchmark are all directly computable. The "overbidding gap" (observed ratio - equilibrium ratio) is the primary measure. Clean, quantitative, no subjective coding. |

**Total score: 20 / 25** — Strong hypothesis. No sharpening needed.

---

## Causal Model

### DAG

```
                     ┌──────────────────────────────────────────────────────┐
                     │                                              (direct) │
                     ▼                                                      │
Competition Size (X) ──→ Strategic Uncertainty (M) ──→ Overbidding Gap (Y)
                                     ↑                          ↑
                                     │                          │
                          Valuation Level (Z) ──────────────────┘
                                                      (Z moderates X→M→Y)
```

**Reading the DAG:**
- X → M → Y: More competitors increases strategic uncertainty (harder to predict opponents), which causes the LLM to deviate from the Nash equilibrium (overbid as a safety margin)
- X → Y (direct): Competition may directly increase bidding through training-data priors (LLMs may have learned that "more competitors = bid higher" as a heuristic)
- Z → M: Valuation level affects baseline strategic uncertainty (low valuation = already likely to lose, less to gain from strategic shading)
- Z → Y (moderation): Valuation level moderates the overbidding gap — high-valuation bidders have more surplus to protect and may shade less under competition

### Variable Definitions

| Variable | Type | Operationalization | How the game captures it |
|----------|------|-------------------|--------------------------|
| **Competition Size (X)** | Treatment (between) | 2-bidder vs. 3-bidder first-price auction | Structural: separate game folders. `auction_2bidder` has 2 bidders; `auction_3bidder` adds an NPC third bidder. |
| **Strategic Uncertainty (M)** | Mediator (latent) | The LLM's difficulty in computing the optimal bid-shading strategy | Inferred from deviation patterns. If deviations increase with n, this supports the strategic-uncertainty channel. |
| **Overbidding Gap (Y)** | Outcome (continuous) | (observed bid / valuation) − (Nash equilibrium bid / valuation). Nash ratio = (n-1)/n: 0.50 for n=2, 0.67 for n=3. Gap > 0 means overbidding relative to equilibrium. | Directly computed from transcript bids and known valuations. |
| **Valuation Level (Z)** | Moderator (within) | Low ($3–$4) vs. High ($7–$9) human valuations | Assigned per round, balanced across conditions. |

### Testable Implications

1. **LLMs deviate from Nash:** In the 2-bidder condition, the observed bid/valuation ratio differs from the Nash prediction of 0.50. (Direction unclear — could be over or under.)
2. **Competition changes behavior:** The bid/valuation ratio is higher (less shading) in the 3-bidder condition than the 2-bidder condition. (Both Nash theory and competition anxiety predict this direction — but the question is whether the LLM adjusts by the right amount.)
3. **Competition causes overbidding relative to Nash (key prediction):** The overbidding gap (observed - Nash) is LARGER in the 3-bidder condition than the 2-bidder condition. The LLM over-adjusts to competition — shading less than the Nash equilibrium prescribes.
4. **Valuation moderates the gap:** The overbidding gap under competition is larger for low-valuation rounds (where losing is more likely and competition anxiety bites harder).

### Identification Strategy

- **Randomized:** Treatment (2-bidder vs. 3-bidder) is structural — different game variants
- **Held constant:** Auction mechanism (first-price sealed-bid), valuation sequences (identical across conditions), number of rounds (6), bid range ($0–$10), AI strategy (Nash equilibrium bidding — a controlled constant)
- **Nash benchmark:** With uniform valuations, the symmetric Bayesian Nash equilibrium bid is `valuation × (n-1)/n`. This provides a theoretical benchmark against which to measure deviations:
  - n=2: bid = 0.50 × valuation
  - n=3: bid = 0.67 × valuation
- **NPC design (3-bidder only):** NPC bids at the Nash equilibrium rate (0.67 × valuation). This ensures the competitive environment is "well-calibrated" — deviations from Nash by the sim_human reflect its own behavioral tendencies, not reactions to irrational NPC behavior.
- **AI player strategy:** AI bids at Nash equilibrium for its condition (0.50 × valuation for 2-bidder, 0.67 × valuation for 3-bidder). This is held constant and serves as the "rational benchmark player."
- **Confounds addressed:** (a) Anchoring to NPC bids — mitigated by sealed bids; (b) Iteration 1 established the baseline: LLMs ARE rational when a dominant strategy exists — deviation here would be attributable to the absence of a dominant strategy.
- **Limitations:** (a) The Nash equilibrium assumes uniform valuation distributions, but our valuations are pre-determined — the LLM may not compute equilibrium based on the actual distribution; (b) The AI playing Nash means the sim_human's best response is also Nash — so deviations are strictly suboptimal.

---

## Next Steps

This hypothesis is ready for `/design-experiment` to map to a two-condition game design:
- **Condition 1:** `auction_2bidder` — 2-player first-price sealed-bid auction
- **Condition 2:** `auction_3bidder` — 3-player first-price sealed-bid auction (with NPC)

The design should use the same valuation sequences as Iteration 1, with AI and NPC playing Nash equilibrium strategies. The primary outcome is the overbidding gap (observed ratio - Nash ratio).
