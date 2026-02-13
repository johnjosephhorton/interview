---
name: design-experiment
description: Take a hypothesis and causal DAG, map it to a game design with 12-item specs, produce a full research memo markdown, and hand off to /create-2-player-game
argument-hint: "[hypothesis name or description]"
---

# /design-experiment — Hypothesis + DAG → Game Design → Specs → Research Memo

**Meta-goal:** Take a formalized hypothesis and causal DAG (from `/hypothesize` or provided directly) and turn it into a concrete game design: select the right game structure, design the treatment manipulation, produce 12-item specs for each condition, and generate a complete research memo in markdown. The output memo is the full "why + how" document — a collaborator should be able to read it and understand both the hypothesis and the experimental design.

This skill handles the **"how"** — from causal model to game design. It expects the "why" (hypothesis, DAG, variables) to already exist. The full chain is: `/hypothesize` → `/design-experiment` → `/create-2-player-game`.

## Usage

- `/design-experiment` — After running `/hypothesize`, picks up the hypothesis from conversation context
- `/design-experiment cheap talk bargaining` — Looks for a hypothesis memo or works from a description

---

## Phase 1: Ingest hypothesis

Pull the hypothesis, causal DAG, and variable definitions from one of these sources (in priority order):

1. **Conversation context** — If `/hypothesize` was just run, extract the research question, core claim, key variables (X/Y/M/Z), DAG, testable implications, and identification strategy from the conversation
2. **Hypothesis memo** — If the user points to a hypothesis memo file, read `hypothesis.md` (or fall back to `.tex` for legacy experiments) and extract the same elements
3. **User description** — If neither exists, ask the user to provide the hypothesis elements (or suggest running `/hypothesize` first)

### Validation checklist

Flag anything missing and ask the user before proceeding:

```
Hypothesis intake:
  Research question .... [found / MISSING]
  Core claim ........... [found / MISSING]
  Treatment (X) ........ [found / MISSING]
  Outcome (Y) .......... [found / MISSING]
  Mechanism (M) ........ [found / MISSING]
  Controls (Z) ......... [found / MISSING]
  Causal DAG ........... [found / MISSING]
  Testable implications  [found / MISSING]
```

If everything is present, summarize the hypothesis in 2–3 sentences and ask: "I'll design a game to test this. Proceed?"

---

## Phase 2: Map DAG to game design

Translate the causal model into a concrete game. This is the core design step.

### 2a. Select game structure

Map the hypothesis to the closest existing game structure:

| If the hypothesis involves... | Structure type | Reference game |
|-------------------------------|---------------|----------------|
| Price negotiation, offers/counteroffers | Bargaining | `bargain_imperfect/` |
| Accept/reject splits, fairness norms | Proposer-responder | `ultimatum/` |
| Simultaneous choices, cooperation/defection | Matrix/simultaneous | `pd_rep/` |
| Sequential trust, reciprocity | Trust/Sequential | `trust/` or `dictator/` |
| Competitive bidding, winner determination | Auction | `auction/` |
| Effort/investment with sunk costs | Contest | `contest/` |
| Voluntary contributions, free-riding | Public goods | `public_goods/` |

If no existing structure fits, compose from primitives (simultaneous choice + communication phase, sequential with hidden info, etc.).

### 2b. Design the treatment

The treatment (X) must be operationalized as a **difference in game rules or parameters** between conditions. Examples:

| Treatment | Operationalization |
|-----------|-------------------|
| Cheap talk | Condition A: message phase before action. Condition B: no message phase |
| Information asymmetry | Condition A: private valuations. Condition B: public valuations |
| Repeated vs one-shot | Condition A: 6 rounds. Condition B: 1 round |
| Punishment option | Condition A: can reduce other's payoff. Condition B: no punishment |

Each condition becomes a **separate game** (separate folder under `games/`). The spec should define the **base game** and the **treatment variation(s)**.

### 2c. Design outcome measurement

Map each outcome variable to something observable in the game transcript:

| Outcome | Measured as |
|---------|------------|
| Cooperation rate | # cooperate choices / total rounds |
| Deal price | Final agreed price (or no-deal indicator) |
| Total surplus | Sum of both players' earnings |
| Trust level | Amount sent in trust game |
| Reciprocity | Return ratio in trust game |
| Efficiency | Actual joint payoff / maximum possible joint payoff |

---

## Phase 3: Produce the 12-item spec(s)

Fill in the spec that `/create-2-player-game` expects. Produce **one spec per condition**.

```
Game spec: <display_name>
─────────────────────────────
1.  Name:           <snake_case>
2.  Display name:   <human-readable>
3.  Description:    <one-liner mentioning the hypothesis>
4.  Structure:      <type from 2a>
5.  Rounds:         <N, justified by statistical power needs>
6.  Roles:          Human = <role>, AI = <role>
7.  Actions:        <from the game structure + treatment>
8.  Turn structure: <simultaneous/alternating/sequential>
9.  Payoffs:        <exact formulas with worked examples>
10. Hidden info:    <what's private, tied to identification strategy>
11. AI goal:        Maximize own earnings (guardrails: <hard constraints preventing dominated moves> — must be IDENTICAL across treatment conditions for clean identification)
12. Sim human goal: Maximize own earnings (guardrails: <hard constraints> — symmetric with AI goal). Do NOT include named strategies, specific opening moves, numeric thresholds for accepting/rejecting, or step-by-step tactical instructions. Behavioral flavor (e.g., "slightly impatient") is optional color, not binding strategy.
```

If the hypothesis requires **multiple game variants** (treatment vs. control), produce a spec for each, noting explicitly what differs and what's held constant.

Present the spec(s) and ask: "Ready to generate the research memo?"

---

## Phase 4: Write research memo (markdown)

Turn the full design (hypothesis + DAG + game specs + experimental design) into a single markdown memo. This is the **superset** memo — it covers both "why" (hypothesis) and "how" (design).

### 4a. Extract the design elements

Gather from the work in Phases 1–3:

1. **Research question** — one sentence
2. **Causal DAG** — variables, edges, types (treatment/mediator/outcome/control)
3. **Conditions** — each game variant with what differs and what's constant
4. **Variable definitions** — operationalization + how the game captures each
5. **Testable implications** — predictions that follow from the DAG
6. **Identification strategy** — what's randomized, held constant, limitations
7. **Outcome measurement** — what's measured and how (from transcripts)
8. **Analysis plan** — primary/secondary comparisons
9. **Power considerations** — rounds, sessions, effect size expectations

### 4b. Write the markdown memo

Write a markdown document at `experiments/<name>/design.md`.

**Create the experiment directory if needed:** `mkdir -p experiments/<name>`

#### Required sections (in order):

1. **Title** — `# Research Design Memo: <title>` with date and status on the next line
2. **Research Question** — one paragraph: question, motivation, why it matters
3. **Causal Model** — Text DAG in a fenced code block, then variable definitions as a markdown table, testable implications (numbered list), identification strategy (bulleted list)
4. **Experimental Design** — Design matrix as a markdown table (**bold** cell text for elements that DIFFER across conditions, plain for held constant), then condition descriptions (bold names + paragraph each), outcome measures as a markdown table
5. **Analysis Plan** — primary analysis, secondary analyses, power considerations, then predictions as a markdown table (columns: prediction, expected direction, test)
6. **Game Implementations** — small markdown table mapping conditions to game folders
7. **Limitations** — bulleted list of threats to validity

### 4c. Open and report

```bash
open experiments/<name>/design.md
```

Report:

```
Research memo generated:
  experiments/<name>/design.md

Next: run /create-2-player-game for each condition.
```

---

## Phase 5: Generate experiment manifest

After the design memo PDF is complete, write a structured TOML manifest at `experiments/<name>/manifest.toml`. This file carries the core research context through the rest of the pipeline — `/run-experiment` and `/analyze-results` read it instead of parsing LaTeX.

```toml
# Experiment manifest — generated by /design-experiment
# Machine-readable context for downstream skills

[experiment]
name = "<experiment_name>"                    # e.g., "cheap_talk_info_asymmetry"
title = "<human-readable title>"              # e.g., "Cheap Talk x Info Asymmetry in Bargaining"
hypothesis = "<one-sentence hypothesis>"      # directional causal claim
research_question = "<one-sentence question>" # the question being tested
triviality_score = 22                         # from /hypothesize scorecard (0-25), or 0 if unknown
experiment_dir = "experiments/<experiment_name>"

[variables]
treatment = "<X description>"                 # e.g., "Information structure (one-sided vs two-sided)"
outcome = "<Y description>"                   # e.g., "Deal rate (binary per game)"
mechanism = "<M description>"                 # e.g., "Strategic misrepresentation vs credible signaling"
control = "<Z description>"                   # e.g., "ZOPA size (held constant)"

[design]
type = "<between | within | factorial>"       # e.g., "factorial"
factors = ["<factor1>", "<factor2>"]          # e.g., ["info_structure", "communication"]
primary_outcome = "<outcome_name>"            # e.g., "deal_rate"
primary_outcome_type = "<binary | continuous>" # determines statistical test
primary_test = "<test description>"           # e.g., "interaction term β₃ in logistic regression"

[conditions.<game_folder_name>]
label = "<human-readable label>"              # e.g., "One-sided / No talk"
treatment_values = { info = "one-sided", talk = "none" }

[conditions.<game_folder_name_2>]
label = "<human-readable label>"
treatment_values = { info = "one-sided", talk = "chat" }
# ... one [conditions.*] block per game folder

[predictions]
# Named predictions that /analyze-results will evaluate
# Format: comparison = "direction"  (higher, lower, equal, interaction)
# e.g.:
# deal_rate_1s_talk_vs_1s_notalk = "higher"
# deal_rate_2s_talk_vs_2s_notalk = "lower"
# deal_rate_interaction = "crossover"

[artifacts]
hypothesis_memo = "experiments/<name>/hypothesis.md"
design_memo = "experiments/<name>/design.md"
# results_memo is added by /analyze-results after analysis
```

**Every field is required.** Use `"unknown"` or `0` for fields where information is unavailable (e.g., no triviality score if `/hypothesize` wasn't run).

---

## Phase 6: Hand off to /create-2-player-game

For each game variant, the user can invoke `/create-2-player-game` with the spec. Report the specs ready for building:

```
Game specs ready for /create-2-player-game:
  1. <game_name_control> — <one-line description>
  2. <game_name_treatment> — <one-line description>

Experiment manifest written to: experiments/<name>/manifest.toml

Run /create-2-player-game for each condition. The specs above contain all 12 items needed.
```

---

## Important rules

### Design rules
- **AI goal and guardrails must be identical across conditions.** The treatment is the game rules/parameters, not the AI's behavior. Both agents are earnings maximizers — their goal section (objective, payoff reminder, reasoning instruction, guardrails) must be the same across conditions for clean identification.
- **One treatment at a time.** Each pair of game variants should differ on exactly one dimension. If the user wants to test multiple treatments, design them as separate experiments (separate game pairs).
- **Payoffs must create the right incentive structure.** The game's payoff formulas must make the hypothesized behavior individually rational (or tempting) — otherwise you're testing whether people follow instructions, not testing the hypothesis.
- **Statistical power matters for round count.** One-shot games need many sessions for power. Repeated games get multiple observations per session but introduce learning/reputation effects. Flag this tradeoff.
- **Name games by condition.** Use descriptive names that make the comparison obvious: `pd_cheap_talk` vs `pd_no_talk`, `trust_public` vs `trust_private`.

### Memo rules
- **One markdown file output.** The deliverable is `experiments/<name>/design.md` — no figures, no LaTeX, no compilation.
- **The text DAG is the centerpiece.** The fenced code block DAG is the visual anchor. Make it clean and readable.
- **Bold highlights in the design matrix.** Use **bold** for elements that differ across conditions, plain text for held constant — this makes the treatment manipulation visually obvious.
- **No fake data in predictions table.** Pre-data only — show directional hypotheses, not simulated results.
- **Create directories if needed:** `mkdir -p experiments/<name>`
