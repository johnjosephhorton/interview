# Pilot Results: `bargain_1s_notalk` (Condition 1 of 4)

**Date:** 2026-02-12 | **Seed:** 1022 | **Design:** Full factorial (3 x 3 = 9 sessions) | **Model:** gpt-5

---

## What was built

### Infrastructure changes

1. **Randomization-aware skill** (`/create-2-player-game`). The skill now supports two new spec items:
   - **Item 13 (Parameters):** Numeric values that vary per session via `{{var_name}}` placeholders in all prompt files, substituted at session start by the existing `interviewer/randomization.py` system.
   - **Item 14 (Treatments):** Structural condition labels for multi-condition experiments, requiring separate game folders per treatment.
   - Three new cross-checks (8–10): variable coverage, variable consistency across files, and variable sanity (no impossible games).
   - Smoke test now uses `--seed` for deterministic variable draws.

2. **Updated templates** (`TEMPLATE_CONFIG.md`, `TEMPLATE_MANAGER.md`, `TEMPLATE_PLAYER.md`). All three templates now document `{{placeholder}}` patterns — where they go, where they don't, and how to write parameterized strategies and payoff formulas.

3. **No code changes.** The existing `randomization.py` module (draw_conditions, substitute_template, apply_conditions_to_game_config) and CLI flags (`--seed`, `--design factorial`) handled everything. No library code was modified.

### Game: `bargain_1s_notalk`

Condition 1 of the cheap talk x information asymmetry experiment (2x2 factorial). This is the **one-sided information, no communication** baseline.

- **Roles:** Human = buyer, AI = seller
- **Info structure:** Seller sees both Vb and Cs; buyer sees only Vb (knows Cs in {30, 40, 50})
- **Communication:** None — offers only
- **Rounds:** 6 alternating offers (AI first)
- **Payoffs:** Deal at P: buyer earns Vb - P, seller earns P - Cs. No deal: both $0.
- **Parameterized variables:**
  - `buyer_value`: choice from {60, 70, 80}
  - `seller_cost`: choice from {30, 40, 50}
  - Ranges restricted from the design memo's {40–80} x {30–70} to guarantee ZOPA > 0 (min $10)
- **AI strategy:** "Informed Anchored Concession" — open at Cs + 0.7 x (60 - Cs), concede 12%/round, accept >= Cs + 5
- **Sim human strategy:** "Cautious Anchoring Buyer" — open at Vb x 0.4, raise 15%/round, accept if ask <= Vb - 5

---

## Full factorial results

| Sim | Vb | Cs | ZOPA | Price | Buyer $ | Seller $ | Efficiency | Rounds |
|-----|----|----|------|-------|---------|----------|------------|--------|
| 1   | 60 | 40 | $20  | $55   | $5.00   | $15.00   | 100%       | 1      |
| 2   | 80 | 40 | $40  | $55   | $25.00  | $15.00   | 100%       | 1      |
| 3   | 70 | 50 | $20  | $60   | $10.00  | $10.00   | 100%       | 3      |
| 4   | 70 | 30 | $40  | $55   | $15.00  | $25.00   | 100%       | 1      |
| 5   | 60 | 30 | $30  | $55   | $5.00   | $25.00   | 100%       | 1      |
| 6   | 80 | 50 | $30  | $55   | $25.00  | $5.00    | 100%       | 1      |
| 7   | 70 | 40 | $30  | $55   | $15.00  | $15.00   | 100%       | 3      |
| 8   | 80 | 30 | $50  | $52   | $28.00  | $22.00   | 100%       | 3      |
| 9   | 60 | 50 | $10  | $55   | $5.00   | $5.00    | 100%       | 1      |

**Averages:** Price = $55.2 | Buyer = $14.78 | Seller = $15.22 | Efficiency = 100% | Rounds = 1.7

**Checker:** 9/9 passed all 9 criteria (arithmetic, totals, input validation, rules, AI strategy, info leakage, manipulation resistance, termination, instructions delivered).

---

## Key findings

### 1. 100% deal rate

All 9 sessions reached a deal. This is expected for the no-talk, one-sided baseline — the AI's fixed concession strategy always produces prices within the ZOPA, and the sim human's acceptance threshold (Vb - 5) is generous enough to accept early.

**Implication for the experiment:** The baseline deal rate is very high. The hypothesis predicts cheap talk will *maintain or increase* this rate under one-sided info (Condition 2), while *decreasing* it under two-sided info (Condition 4). A 100% baseline means we're looking for deal *failures* introduced by the chat phase under two-sided asymmetry.

### 2. AI opening ask does not vary with seller_cost

The AI opened at **$55 in all 9 sessions**, despite the strategy formula predicting different openings per Cs:

| Cs | Expected opening (Cs + 0.7 x (60 - Cs)) | Actual opening | Deviation |
|----|------------------------------------------|----------------|-----------|
| 30 | $51                                      | $55            | +$4       |
| 40 | $54                                      | $55            | +$1       |
| 50 | $57                                      | $55            | -$2       |

The LLM is either using the manager's default fallback ($55) or approximating the formula to a round number. This is a **strategy compliance bug** — the parameterized strategy formula is being ignored in favor of a fixed anchor.

**Impact:** The deal price is nearly constant (~$55) regardless of ZOPA, so surplus division shifts entirely based on Vb and Cs. The AI earns more when Cs is low (more margin) and less when Cs is high, but the price itself doesn't adapt.

**Fix needed:** Either (a) precompute the opening ask in the prompt for each Cs value ("If your cost is $30, open at $51. If $40, open at $54. If $50, open at $57.") or (b) simplify to a single formula the LLM can execute (e.g., "Open at ${{seller_cost}} + 20").

### 3. Most games end in Round 1

6 of 9 sessions (67%) ended with the sim human accepting the AI's opening ask immediately. This happens because the sim human's acceptance threshold (Vb - 5) is almost always above $55:
- Vb=60: threshold $55 — borderline accept at $55
- Vb=70: threshold $65 — $55 well below, instant accept
- Vb=80: threshold $75 — $55 well below, instant accept

The 3 multi-round sessions (sims 3, 7, 8) went to Round 3, suggesting the sim human occasionally opens with a counteroffer instead of accepting. This may be stochastic LLM behavior rather than strategic.

**Implication:** The sim human strategy may be too accepting for pilot purposes. For the real experiment with human participants, we expect more bargaining (humans will counteroffer even when they could accept, to extract more surplus).

### 4. Buyer captures ~48% of surplus

Buyer share of total surplus averages 47.9%. The split is roughly even, slightly favoring the seller — consistent with the seller having the first-mover advantage (sets the anchor) and one-sided information (sees Vb).

### 5. Variable substitution works correctly

The `{{buyer_value}}` and `{{seller_cost}}` placeholders were correctly substituted in all prompt files:
- Opening messages showed the correct Vb to the buyer
- Seller's exact cost was never leaked (info_leakage criterion passed 9/9)
- Payoffs were computed using the drawn values (arithmetic_correctness passed 9/9)
- The `conditions` dict in each transcript JSON records the drawn values

---

## What's next

| Step | Status |
|------|--------|
| Fix AI opening ask invariance (precomputed lookup or simpler formula) | Needed before production |
| Generate Condition 2: `bargain_1s_talk` (one-sided + 3-msg chat) | Not started |
| Generate Condition 3: `bargain_2s_notalk` (two-sided, no chat) | Not started |
| Generate Condition 4: `bargain_2s_talk` (two-sided + chat) | Not started |
| Run full factorial for all 4 conditions | Blocked on game generation |
| Cross-condition analysis (deal rates, surplus division, round counts) | Blocked on all 4 conditions |

---

## Reproduction

```bash
source venv/bin/activate
interview simulate bargain_1s_notalk --design factorial --seed 1022 -n 9
```

Transcripts saved to: `transcripts/bargain_1s_notalk/2026-02-12_11-24-02_sim*.json`
