zhu# Research Design Memo: Competition Anxiety in Vickrey Auctions

**Date:** 2026-02-13
**Status:** Pre-build
**Experiment:** `vickrey_competition`

---

## Research Question

Does the visible number of competitors in a second-price sealed-bid (Vickrey) auction cause bidders to deviate from truthful bidding, even though the dominant strategy is invariant to bidder count? Standard theory predicts bid = valuation regardless of the number of competitors. We test whether adding a visible third bidder (NPC) causes systematic overbidding in LLM-simulated agents, and whether this effect is moderated by the bidder's private valuation level — with low-valuation bidders expected to overbid more due to higher perceived loss probability.

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

### Variable Definitions

| Variable | Type | Operationalization | Game captures it via |
|----------|------|-------------------|---------------------|
| Competition Size (X) | Treatment (between) | 2-bidder vs. 3-bidder auction | Structural: separate game folders. `vickrey_2bidder` has no NPC; `vickrey_3bidder` adds an NPC third bidder managed by the manager. |
| Perceived Loss Probability (M) | Mediator (latent) | Bidder's implicit estimate of losing | Not directly observable. Inferred from the interaction pattern: if overbidding increases with competition only at low valuations, this supports the loss-probability channel over anchoring. |
| Bid/Valuation Ratio (Y) | Outcome (continuous) | bid / private valuation per round | Directly computed from transcript. Ratio = 1.0 is truthful; > 1.0 is overbidding; < 1.0 is underbidding. |
| Valuation Level (Z) | Moderator (within) | Low ($3–$4) vs. High ($7–$9) | Assigned per round. 3 low-valuation rounds and 3 high-valuation rounds per game, balanced across conditions. |

### Testable Implications

1. **Main effect:** Mean bid/valuation ratio is higher in the 3-bidder condition than the 2-bidder condition.
2. **Interaction (key prediction):** The competition-induced increase in bid/valuation ratio is larger for low-valuation rounds than for high-valuation rounds.
3. **Earnings cost:** Mean total earnings are lower in the 3-bidder condition (overbidding creates winner's curse risk in second-price auctions).
4. **Overbidding frequency:** The proportion of rounds with ratio > 1.0 is higher in the 3-bidder condition, especially for low-valuation rounds.

### Identification Strategy

- **Randomized:** Treatment (2-bidder vs. 3-bidder) is structural — different game variants randomly assigned to simulations
- **Held constant across conditions:** Auction mechanism (second-price sealed-bid), private valuation sequences (identical), number of rounds (6), AI strategy (truthful bidding), bid range ($0–$10)
- **NPC design (3-bidder only):** Third bidder is an NPC controlled by the manager. NPC bids truthfully (valuation = bid). NPC valuations are pre-determined and identical across simulations. NPC bid is revealed simultaneously with the AI's bid, after the human submits.
- **Confounds addressed:** (a) Anchoring to NPC bids — mitigated by sealed bids (NPC bid unknown at decision time); (b) Learning — 6 rounds with alternating low/high valuations; (c) Order effects — same valuation sequence in both conditions
- **Limitations:** (a) Perceived loss probability is latent; (b) LLM behavior may not mirror human behavioral biases; (c) NPC presence changes the game outcome distribution (possible 3-way ties), which could affect behavior independently of competition anxiety

---

## Experimental Design

### Design Matrix

| Element | `vickrey_2bidder` | `vickrey_3bidder` |
|---------|-------------------|-------------------|
| Auction type | Second-price sealed-bid | Second-price sealed-bid |
| **Number of bidders** | **2 (Human + AI)** | **3 (Human + AI + NPC)** |
| Rounds | 6 | 6 |
| Bid range | $0.00 – $10.00 | $0.00 – $10.00 |
| Human valuations | $3, $8, $4, $9, $3, $7 | $3, $8, $4, $9, $3, $7 |
| AI valuations | $7, $4, $6, $3, $8, $5 | $7, $4, $6, $3, $8, $5 |
| **NPC valuations** | **N/A** | **$5, $6, $8, $4, $6, $3** |
| **NPC announced?** | **No** | **Yes — "There are 3 bidders"** |
| Winner determination | Highest bid wins, pays 2nd-highest bid | Highest bid wins, pays 2nd-highest bid |
| AI strategy | Truthful bidding (earnings maximizer) | Truthful bidding (earnings maximizer) |
| Sim human strategy | Earnings maximizer (no script) | Earnings maximizer (no script) |

**Bold** = elements that differ between conditions.

### Condition Descriptions

**`vickrey_2bidder` (Control):** Standard 2-player Vickrey auction. The human and AI each have a private valuation per round and simultaneously submit sealed bids. The highest bidder wins and pays the second-highest bid. This is the baseline — any overbidding here represents the agent's default bias in Vickrey auctions.

**`vickrey_3bidder` (Treatment):** Identical to control, except a third NPC bidder is announced at the start. The manager tells the human "There are 3 bidders in this auction: you, the AI, and a third bidder." Each round, the NPC's bid is determined internally by the manager (truthful bidding on pre-set valuations). After the human submits their bid, all three bids are revealed and the winner is determined. The NPC's presence is the only manipulation — everything else is held constant.

### Valuation Sequence Design

Rounds alternate between low and high human valuations to ensure within-subject variation:

| Round | Human Val | Category | AI Val | NPC Val (3-bidder only) |
|-------|-----------|----------|--------|------------------------|
| 1 | $3.00 | Low | $7.00 | $5.00 |
| 2 | $8.00 | High | $4.00 | $6.00 |
| 3 | $4.00 | Low | $6.00 | $8.00 |
| 4 | $9.00 | High | $3.00 | $4.00 |
| 5 | $3.00 | Low | $8.00 | $6.00 |
| 6 | $7.00 | High | $5.00 | $3.00 |

- **Low-valuation rounds (1, 3, 5):** Human values $3–$4. In these rounds, the human is likely to lose even with truthful bidding — competition anxiety should peak here.
- **High-valuation rounds (2, 4, 6):** Human values $7–$9. The human is likely to win — less incentive to overbid.
- NPC valuations are spread across $3–$8 to create realistic competition without always dominating.

### Outcome Measures

| Measure | Type | Computation | Level |
|---------|------|-------------|-------|
| **Bid/Valuation Ratio** (primary) | Continuous | bid / valuation per round | Round |
| Overbid indicator | Binary | 1 if ratio > 1.0, else 0 | Round |
| Total earnings | Continuous | Sum of per-round earnings | Game |
| Earnings efficiency | Continuous | Actual earnings / max possible earnings | Game |
| Round-by-round bid trend | Continuous | Bid ratio by round number | Round |

---

## Analysis Plan

### Primary Analysis

Mixed-effects linear regression on round-level data:

```
bid_ratio ~ competition + valuation_level + competition × valuation_level + round + (1 | simulation_id)
```

- `competition`: 0 = 2-bidder, 1 = 3-bidder (between-subjects)
- `valuation_level`: 0 = high ($7–$9), 1 = low ($3–$4) (within-subjects)
- `round`: 1–6 (controls for learning/time trends)
- Random intercept for simulation (repeated measures within game)

**Primary coefficient of interest:** β₃ (competition × valuation_level interaction). The hypothesis predicts β₃ > 0 — competition increases bid ratio more for low-valuation rounds.

### Secondary Analyses

1. **Overbidding frequency:** Logistic regression: overbid ~ competition × valuation_level
2. **Earnings:** t-test comparing total earnings between conditions
3. **Round dynamics:** Does the competition effect persist, grow, or decay over rounds?
4. **NPC interaction (3-bidder only):** Does the sim_human's bid correlate with the NPC's bid from the previous round? (anchoring check)

### Power Considerations

- 6 rounds per game × 30 simulations per condition = 180 round-level observations per condition
- 360 total observations for the interaction test
- With repeated measures (6 obs/simulation), effective sample for between-subjects comparison is ~30 per condition
- Sufficient for detecting medium-to-large effect sizes (Cohen's d > 0.5) on the interaction

### Predictions

| Prediction | Direction | Test | Threshold |
|------------|-----------|------|-----------|
| Main effect of competition on bid ratio | Higher in 3-bidder | β₁ > 0 | p < 0.05 |
| **Interaction: competition × low valuation** | **Positive (key prediction)** | **β₃ > 0** | **p < 0.05** |
| Overbid frequency: competition × low val | Higher in 3-bidder + low val | Logistic β₃ > 0 | p < 0.05 |
| Total earnings | Lower in 3-bidder | Two-sample t-test | p < 0.10 |

---

## Game Implementations

| Condition | Game folder | Description |
|-----------|------------|-------------|
| Control (2-bidder) | `games/vickrey_2bidder/` | Standard 2-player Vickrey auction, 6 rounds |
| Treatment (3-bidder) | `games/vickrey_3bidder/` | 3-player Vickrey auction with NPC third bidder, 6 rounds |

---

## 12-Item Specs

### Spec 1: vickrey_2bidder (Control)

```
Game spec: Vickrey Auction — 2 Bidders
─────────────────────────────
1.  Name:           vickrey_2bidder
2.  Display name:   Vickrey Auction (2 Bidders)
3.  Description:    6-round second-price sealed-bid auction, 2 bidders — control condition
4.  Structure:      Auction (sealed-bid, second-price)
5.  Rounds:         6
6.  Roles:          Human = Bidder 1, AI = Bidder 2
7.  Actions:        Each round, both players simultaneously submit sealed bids ($0.00–$10.00)
8.  Turn structure: Simultaneous sealed bids each round
9.  Payoffs:        Winner (highest bid) earns: valuation − 2nd-highest bid.
                    Loser earns $0. Ties broken by coin flip; winner pays tied amount.
                    Examples:
                    - Human val $8, bids $8, AI bids $4 → Human wins, pays $4, earns $4.00
                    - Human val $3, bids $3, AI bids $7 → AI wins, Human earns $0.00
                    - Human val $4, bids $5, AI bids $6 → AI wins, Human earns $0.00
10. Hidden info:    Each player knows ONLY their own valuation. AI valuations are secret.
                    Human learns their valuation at the start of each round only.
                    No future valuations revealed.
11. AI goal:        Maximize total earnings across 6 rounds.
                    Guardrails: bid ∈ [$0.00, $10.00]. Never bid negative.
12. Sim human goal: Maximize total earnings across 6 rounds.
                    Guardrails: bid ∈ [$0.00, $10.00]. No scripted strategy.
```

### Spec 2: vickrey_3bidder (Treatment)

```
Game spec: Vickrey Auction — 3 Bidders
─────────────────────────────
1.  Name:           vickrey_3bidder
2.  Display name:   Vickrey Auction (3 Bidders)
3.  Description:    6-round second-price sealed-bid auction, 3 bidders (2 players + NPC) — treatment
4.  Structure:      Auction (sealed-bid, second-price, 3 bidders)
5.  Rounds:         6
6.  Roles:          Human = Bidder 1, AI = Bidder 2, NPC = Bidder 3 (manager-controlled)
7.  Actions:        Each round, Human and AI simultaneously submit sealed bids ($0.00–$10.00).
                    NPC bid is determined by manager (truthful bidding on pre-set valuations).
8.  Turn structure: Simultaneous sealed bids each round (NPC bid resolved internally)
9.  Payoffs:        Winner (highest of 3 bids) earns: valuation − 2nd-highest bid.
                    Two losers each earn $0. Ties broken randomly; winner pays 2nd-highest.
                    Examples:
                    - Human val $8, bids $8, AI bids $4, NPC bids $6 → Human wins, pays $6, earns $2.00
                    - Human val $3, bids $4, AI bids $7, NPC bids $5 → AI wins, Human earns $0.00
                    - Human val $9, bids $9, AI bids $3, NPC bids $4 → Human wins, pays $4, earns $5.00
10. Hidden info:    Each player knows ONLY their own valuation. AI and NPC valuations secret.
                    NPC existence is announced ("3 bidders"), but NPC valuation is not revealed.
                    Bids revealed simultaneously after human submits.
11. AI goal:        Maximize total earnings across 6 rounds.
                    Guardrails: bid ∈ [$0.00, $10.00]. IDENTICAL to 2-bidder condition.
12. Sim human goal: Maximize total earnings across 6 rounds.
                    Guardrails: bid ∈ [$0.00, $10.00]. No scripted strategy. IDENTICAL to 2-bidder.
```

---

## Limitations

- **Perceived loss probability is latent.** We cannot directly measure the mediator — we infer the mechanism from the interaction pattern. A significant interaction is consistent with competition anxiety but does not prove it.
- **LLM agents may not exhibit human behavioral biases.** If the LLM reasons from first principles about Vickrey auctions, it may bid truthfully regardless of competitor count, yielding a null result. This would itself be an interesting finding (LLMs as "hyper-rational" agents).
- **NPC changes outcome distribution.** In the 3-bidder condition, the second-highest bid is mechanically higher on average (more bidders → higher second price). This changes expected earnings even for a truthful bidder. The bid/valuation *ratio* (not raw bid) controls for this, but the changed payoff landscape could affect behavior independently of competition anxiety.
- **Fixed valuation sequences.** Using pre-determined valuations ensures cross-condition comparability but limits generalizability. The specific valuation levels ($3–$4 for low, $7–$9 for high) may interact with the $0–$10 bid range in ways that don't generalize.
- **6 rounds may introduce learning effects.** Bidders may learn that truthful bidding is optimal over rounds, potentially washing out competition anxiety in later rounds. The round covariate in the primary analysis controls for this trend.
