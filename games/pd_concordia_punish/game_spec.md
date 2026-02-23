# Repeated Prisoner's Dilemma with Costly Punishment

## Game Rules
- 2 symmetric players (Player A and Player B), 10 rounds
- Each round has two stages:
  1. **PD stage:** Both players simultaneously choose COOPERATE or DEFECT
  2. **Punishment stage:** After seeing the PD outcome, both players simultaneously choose PUNISH or NO_PUNISH
- Act order is randomized each round within each stage to prevent positional bias
- All observations are role-relative ("You" / "the other player")

## Payoff Formulas

### PD Stage (per round)
| | Other cooperates | Other defects |
|---|---|---|
| You cooperate | $3 | $0 |
| You defect | $5 | $1 |

### Punishment Stage (per round)
- PUNISH: Costs you $1, reduces the other player's round earnings by $3
- NO_PUNISH: No cost, no effect
- Both players decide simultaneously after seeing the PD outcome

### Combined Round Payoff
Round payoff = PD payoff - (punishment cost if you punished) - (punishment received if other punished you)

### Worked Examples
1. Both cooperate, no punishment: A=$3, B=$3
2. Both cooperate, A punishes B: A=$3-$1=$2, B=$3-$3=$0
3. A defects, B cooperates, B punishes A: A=$5-$3=$2, B=$0-$1=-$1
4. Both defect, both punish: A=$1-$1-$3=-$3, B=$1-$1-$3=-$3
5. A cooperates, B defects, A punishes B, B no punish: A=$0-$1=-$1, B=$5-$3=$2

Note: Round earnings can go negative.

## Agent Goals

### Player A
- Objective: Maximize total earnings over 10 rounds
- Guardrails: None (punishment is optional, negative earnings are possible)

### Player B
- Objective: Maximize total earnings over 10 rounds
- Guardrails: None

## Parameters
All values hardcoded. No per-session randomization.

## Treatment
Treatment condition of the pd_concordia experiment. Compared against pd_concordia (baseline without punishment).
