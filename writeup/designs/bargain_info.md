# Research Design Memo: Information Structure in Bargaining

**Date:** 2026-02-11
**Status:** Pre-registration draft

## 1. Research Question

How does the structure of private information — specifically whether one or both parties hold private valuations — affect deal rates and allocative efficiency in alternating-offer bargaining? Classic theory (Myerson & Satterthwaite, 1983) predicts that two-sided private information makes efficient trade generically impossible, while one-sided asymmetry creates surplus extraction opportunities for the informed party. This experiment tests whether these predictions hold when one counterpart is an LLM agent following a fixed strategy, isolating the effect of information structure on human bargaining behavior.

## 2. Causal Model

![Causal DAG](../plots/dag_bargain_info.pdf)

### Variable Definitions

| Variable | Type | Operationalization | Game captures via |
|----------|------|-------------------|-------------------|
| Info structure (X) | Treatment | One-sided vs. two-sided vs. full private info | Separate game variants with different visibility rules |
| Strategic posturing (M1) | Mediator | Aggressiveness of offers relative to ZOPA | Offer sequences in transcript |
| First-offer anchoring (M2) | Mediator | Distance of first offer from efficient midpoint | Round 1 offer value |
| Deal rate (Y1) | Primary outcome | Whether agreement is reached before round limit | Presence of "accept" in transcript |
| Efficiency (Y2) | Primary outcome | Joint surplus captured / maximum possible ($2.00) | Computed from final price and known valuations |
| Deal price (Y3) | Secondary outcome | Final agreed price | Extracted from acceptance round |
| Payoff structure (Z1) | Control | Human values at $8, AI at $6, ZOPA = [$6, $8] | Identical across all conditions |
| AI strategy (Z2) | Control | Concession Ladder with fixed thresholds | Identical `player.md` across all conditions |
| Round count (Z3) | Control | 6 rounds per session | Identical `config.toml` setting |

### Testable Implications

1. If two-sided info increases strategic posturing, deal rates should be **lower** in the two-sided condition than in the one-sided or full-info conditions.
2. If one-sided info enables surplus extraction, deal prices in the one-sided condition should be **closer to the uninformed party's reservation value** (human's $8.00).
3. If information structure affects anchoring, first offers should differ systematically — more extreme first offers under greater uncertainty.
4. Conditional on reaching a deal, efficiency should be relatively stable across conditions (surplus is either captured or not), but the probability of capturing it should vary.

### Identification Strategy

- **Randomized:** Participants are assigned to one of three game variants; the only difference is the information structure.
- **Held constant:** Underlying valuations ($8.00 / $6.00), AI strategy (Concession Ladder: open at $9.50, concede $0.50/round, accept ≥ $6.50, final round accept ≥ $6.00), round count (6), payoff formulas, turn structure (AI offers first).
- **Ruled out:** Payoff-driven differences (same ZOPA across all conditions), AI behavioral confounds (identical strategy file).
- **Limitations:** LLM counterparts may not respond to information asymmetry the way human counterparts would; within-session learning may confound early vs. late round comparisons; fixed AI strategy means we test human response to info structure, not bilateral strategic interaction.

## 3. Experimental Design

### Conditions

![Design Matrix](../plots/design_matrix_bargain_info.pdf)

**Full Info (Control):** Both valuations are public knowledge. Human knows AI values the mug at $6.00; AI knows human values it at $8.00. Both know the ZOPA is [$6.00, $8.00]. This is the efficiency benchmark — the only barrier to trade is splitting the surplus.

**One-Sided (Treatment 1):** Human's valuation ($8.00) is public. AI's valuation ($6.00) is private — the human only knows it falls in [$4.00, $8.00]. The AI has an information advantage; the human must infer the AI's reservation price from its bargaining behavior.

**Two-Sided (Treatment 2):** Both valuations are private. Human knows their own value ($8.00) and that AI's value is in [$4.00, $8.00]. AI knows its own value ($6.00) and that human's value is in [$6.00, $10.00]. Neither party knows the exact ZOPA. This is the "hardest" information environment.

### Outcome Measures

| Measure | Type | Operationalization | Source |
|---------|------|-------------------|--------|
| Deal rate | Primary | Binary: agreement reached before round 6 exhausted | Transcript: "accept" event |
| Efficiency | Primary | Joint surplus / $2.00 (max possible) | Computed: ($8 − P) + (P − $6) if deal; $0 if no deal |
| Deal price | Secondary | Final agreed price, conditional on deal | Transcript: price at acceptance |
| Rounds to agreement | Secondary | Number of rounds before acceptance | Transcript: round counter at acceptance |
| First-offer distance | Mechanism | |Opening offer − $7.00| (midpoint of ZOPA) | Transcript: Round 1 human counteroffer |
| Concession rate | Mechanism | Average price change per round | Computed from offer sequence |

## 4. Analysis Plan

### Primary Analysis

Compare deal rates across three conditions using a chi-squared test (or logistic regression with condition as a categorical predictor). With 30+ sessions per condition, we have reasonable power to detect a 20+ percentage point difference in deal rates.

### Secondary Analyses

- **Deal price | deal:** OLS regression of final price on condition indicators, conditional on reaching a deal. Tests whether information structure shifts bargaining power.
- **Mechanism check:** Compare first-offer distances and concession rates across conditions. If posturing mediates the info→outcome relationship, first offers should be more extreme under greater uncertainty.
- **Rounds to agreement:** Poisson regression (or survival analysis) of agreement timing on condition.

### Power Considerations

- 6 rounds per session provides moderate within-session variation but the primary outcome (deal rate) is session-level.
- Recommend **30–50 sessions per condition** (90–150 total). Binary outcomes require more observations than continuous ones.
- Expected effect sizes are uncertain (exploratory), but Myerson-Satterthwaite predicts a meaningful gap between full-info and two-sided conditions.

![Prediction Space](../plots/predictions_bargain_info.pdf)

## 5. Game Implementations

| Condition | Game folder | Key difference |
|-----------|------------|----------------|
| Full Info (Control) | `games/bargain_full_info/` | Both valuations public |
| One-Sided (Treatment 1) | `games/bargain_one_sided/` | AI valuation private, human valuation public |
| Two-Sided (Treatment 2) | `games/bargain_two_sided/` | Both valuations private |

To generate each game:
```
/create-2-player-game <paste spec from /create-game output>
```

## 6. Limitations

- **LLM counterpart, not human:** The AI follows a fixed concession schedule regardless of information structure. This means we're testing how humans respond to information asymmetry against a mechanical opponent, not bilateral strategic interaction. Findings may not generalize to human-human bargaining.
- **Fixed AI strategy across conditions:** By design (for identification), the AI doesn't adapt to what it "knows." In real bargaining, an informed party would exploit their advantage — our design measures only the human side of this.
- **Within-session learning:** With 6 rounds per session, behavior in later rounds may reflect learned beliefs about the AI, not just the information treatment. Consider analyzing Round 1 separately as a "clean" measure.
- **LLM behavioral consistency:** The AI's natural language may subtly vary across runs, even with the same strategy. Token-level randomness could introduce noise, though the fixed strategy and temperature settings mitigate this.
- **Single ZOPA:** Results are for one specific valuation pair ($8/$6, ZOPA = $2). Different surplus sizes or asymmetric ZOPAs could yield different patterns.
