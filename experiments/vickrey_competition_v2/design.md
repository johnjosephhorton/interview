# Research Design Memo: Strategic Shading Under Competition in First-Price Auctions

**Date:** 2026-02-13
**Status:** Pre-build
**Experiment:** `vickrey_competition_v2` (Iteration 2 of `vickrey_competition`)

---

## Research Question

Given that LLM agents execute the dominant strategy perfectly in Vickrey auctions, does switching to a first-price auction — where optimal bidding requires strategic shading — reveal competition-sensitive behavior? The Nash equilibrium bid in a first-price auction is valuation x (n-1)/n, which changes with the number of bidders. We test whether LLM agents adjust their shading correctly for different levels of competition, or whether they systematically overbid relative to the Nash prediction.

---

## Causal Model

### DAG

```
Competition Size (X) ──→ Strategic Uncertainty (M) ──→ Overbidding Gap (Y)
        │                           ↑                          ↑
        └───────────────────────────┼──────────────────────→  │ (direct)
                                    │                          │
                         Valuation Level (Z) ──────────────────┘
                                                     (Z moderates X→M→Y)
```

### Variable Definitions

| Variable | Type | Operationalization | Game captures it via |
|----------|------|-------------------|---------------------|
| Competition Size (X) | Treatment (between) | 2-bidder vs. 3-bidder first-price auction | Structural: separate game folders |
| Strategic Uncertainty (M) | Mediator (latent) | Difficulty computing optimal shading | Inferred from deviation magnitude |
| Overbidding Gap (Y) | Outcome (continuous) | (observed bid/val) - (Nash bid/val). Nash ratio = (n-1)/n | Computed from transcript bids |
| Valuation Level (Z) | Moderator (within) | Low ($3-$4) vs High ($7-$9) | Assigned per round |

### Testable Implications

1. LLMs deviate from Nash equilibrium in first-price auctions (unlike Vickrey where they were exact)
2. Bid/valuation ratio is higher in 3-bidder than 2-bidder condition (less shading under competition)
3. Overbidding gap (observed - Nash) is larger in 3-bidder condition (over-adjustment to competition)
4. Overbidding gap is larger for low-valuation rounds under competition

---

## Experimental Design

### Design Matrix

| Element | `auction_2bidder` | `auction_3bidder` |
|---------|-------------------|-------------------|
| Auction type | **First-price** sealed-bid | **First-price** sealed-bid |
| **Number of bidders** | **2 (Human + AI)** | **3 (Human + AI + NPC)** |
| Payment rule | **Winner pays own bid** | **Winner pays own bid** |
| Rounds | 6 | 6 |
| Bid range | $0.00 – $10.00 | $0.00 – $10.00 |
| Human valuations | $3, $8, $4, $9, $3, $7 | $3, $8, $4, $9, $3, $7 |
| AI valuations | $7, $4, $6, $3, $8, $5 | $7, $4, $6, $3, $8, $5 |
| **NPC valuations** | **N/A** | **$5, $6, $8, $4, $6, $3** |
| **Nash bid ratio** | **0.50** | **0.67** |
| AI strategy | Nash equilibrium (bid = val x 0.50) | Nash equilibrium (bid = val x 0.67) |
| **NPC strategy** | **N/A** | **Nash equilibrium (bid = val x 0.67)** |

### Outcome Measures

| Measure | Computation |
|---------|-------------|
| Bid/valuation ratio (primary) | bid / valuation per round |
| Overbidding gap (key) | (bid/val) - Nash ratio |
| Total earnings | Sum of per-round earnings |

### Analysis Plan

**Primary:** Compare overbidding gap between conditions: gap_3bidder vs gap_2bidder.
**Key test:** Welch's t-test on mean overbidding gap between conditions.
**Interaction:** gap ~ competition x valuation_level.

### Predictions

| Prediction | Direction | Test |
|-----------|-----------|------|
| LLMs deviate from Nash | ratio ≠ Nash ratio | One-sample t vs. theoretical |
| Competition increases ratio | ratio_3bid > ratio_2bid | Two-sample t |
| **Overbidding gap larger under competition** | **gap_3bid > gap_2bid** | **Two-sample t** |
| Gap larger for low valuations | interaction > 0 | Interaction test |

---

## Game Implementations

| Condition | Game folder | Description |
|-----------|------------|-------------|
| Control (2-bidder) | `games/auction_2bidder/` | 2-player first-price auction, AI bids at 50% of valuation |
| Treatment (3-bidder) | `games/auction_3bidder/` | 3-player first-price auction with NPC, AI+NPC bid at 67% of valuation |
