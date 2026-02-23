# Repeated Prisoner's Dilemma

## Game Rules
- **Structure:** Matrix/simultaneous, 2 players, 10 rounds
- **Roles:** Player A and Player B (symmetric)
- **Actions:** Each round, both players simultaneously choose COOPERATE or DEFECT
- **Turn structure:** Simultaneous — both choose before seeing the other's choice
- **Information:** All public — both players see all prior choices after each round

## Payoff Formulas

Per-round payoff matrix:

|                  | B Cooperates | B Defects |
|------------------|-------------|-----------|
| A Cooperates     | 3 / 3       | 0 / 5     |
| A Defects        | 5 / 0       | 1 / 1     |

(Format: A payout / B payout)

- Both COOPERATE: each earns $3
- Both DEFECT: each earns $1
- One cooperates, other defects: defector earns $5, cooperator earns $0

Total earnings = sum of per-round earnings across all 10 rounds.

### Worked examples
1. Both cooperate all 10 rounds: A=$30, B=$30
2. A always defects, B always cooperates: A=$50, B=$0
3. Both defect all 10 rounds: A=$10, B=$10
4. A cooperates 7 rounds then defects 3 (B always cooperates): A = 7*3 + 3*5 = $36, B = 7*3 + 3*0 = $21

## Agent Goals

### Player A
- Objective: Maximize total earnings over 10 rounds
- Guardrails: Must choose exactly "cooperate" or "defect" each round

### Player B
- Objective: Maximize total earnings over 10 rounds (symmetric)
- Guardrails: Must choose exactly "cooperate" or "defect" each round

## Parameters
No parameters — all values hardcoded.

## Treatment
Standalone game — no treatment variation.
