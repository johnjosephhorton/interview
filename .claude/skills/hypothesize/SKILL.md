---
name: hypothesize
description: Formalize a research hypothesis into a Pearlean causal DAG, evaluate its interestingness, and produce a self-contained hypothesis memo PDF. Supports iteration — can ingest prior experiment results and refine the hypothesis.
argument-hint: "[hypothesis or question] OR iterate <experiment-name>"
---

# /hypothesize — Hypothesis → Causal Model → Triviality Test → Hypothesis Memo PDF

**Meta-goal:** Turn a research hypothesis — vague or specific — into a formal causal model (Pearlean DAG), rigorously evaluate whether it's trivial, auto-sharpen if needed, and produce a self-contained hypothesis memo PDF. A collaborator should be able to read the output PDF and understand the causal claim, why it matters, and what an experiment would need to identify.

**Supports iteration:** When given prior experiment results, this skill ingests the findings, determines an iteration strategy, and produces a refined hypothesis that builds on what was learned. The pipeline is a loop:

```
/hypothesize → /design-experiment → /create-2-player-game → simulate → /analyze-results
      ↑                                                                        │
      └────────────────────── /hypothesize iterate ←───────────────────────────┘
```

**Run to completion. Never stop to ask the user. If input is vague, extrapolate the most interesting version. If specific, follow it closely.**

This skill handles the **"why"** — from hypothesis to causal model. It does **not** design the game or produce specs. To continue to game design, run `/design-experiment` after this skill.

## Usage

- `/hypothesize does cheap talk improve outcomes in bargaining under asymmetric information?` — From a hypothesis
- `/hypothesize` — Extrapolate the most interesting hypothesis from context; if no context, pick a novel hypothesis in behavioral game theory
- `/hypothesize iterate info_source_bargaining` — Ingest prior results from the named experiment and produce a refined v2 hypothesis

---

## Phase 0: Ingest prior results (iteration mode only)

**Skip this phase** if the user provides a fresh hypothesis (not `iterate`). **Execute this phase** if the argument starts with `iterate` followed by an experiment name.

### 0a. Locate and read the results memo

Search for the prior experiment's results memo:
- `experiments/<experiment_name>/results.tex`
- If not found, try `experiments/<experiment_name>/*results*.tex`
- If still not found, report "No results memo found for <experiment_name>" and fall back to fresh hypothesis mode

Read the full `.tex` file.

### 0b. Extract structured data

Look for the machine-readable `\begin{verbatim}` block in the "Next Experiment" section (added by `/analyze-results`). Extract these fields:

```
prior_hypothesis: <the hypothesis that was tested>
verdict: <YES_INTERESTING / PARTIALLY / NO_NULL / NO_UNINFORMATIVE>
diagnosis: <DESIGN / POWER / IMPLEMENTATION / HYPOTHESIS>
key_finding: <one-sentence summary of what was found>
key_statistic: <the single most important number>
dag_variables: <X, M, Y, Z from the prior DAG>
testable_implications_results: <which predictions were confirmed/refuted>
next_archetype: <EXTEND / DEEPEN / REPLICATE / REFINE / PIVOT>
proposed_changes: <specific changes recommended>
next_hypothesis_sketch: <the rough next hypothesis>
```

If the verbatim block is missing, extract these fields manually from the prose in the Evaluation and Next Experiment sections.

### 0c. Determine iteration strategy

Map verdict × diagnosis to an iteration strategy:

| Verdict | Diagnosis | Strategy | What changes |
|---------|-----------|----------|-------------|
| YES_INTERESTING | — | **EXTEND** | Add a new condition or moderator to the existing design |
| PARTIALLY | DESIGN | **REFINE** | Same hypothesis, better game design that isolates the mechanism |
| PARTIALLY | HYPOTHESIS | **DEEPEN** | Narrow the hypothesis to the part that worked |
| NO_NULL | POWER | **REPLICATE** | Same design, more sessions or tighter ZOPA |
| NO_NULL | DESIGN | **REFINE** | Same hypothesis, different game that creates more variance |
| NO_NULL | HYPOTHESIS | **PIVOT** | Different hypothesis entirely, informed by what didn't work |
| NO_UNINFORMATIVE | IMPLEMENTATION | **REFINE** | Fix game bugs first, then re-run |
| NO_UNINFORMATIVE | DESIGN | **PIVOT** | The game structure can't test this; try a different approach |

If the results memo specifies `next_archetype`, use that. Otherwise, infer from the verdict and diagnosis.

### 0d. Produce structured handoff for Phase 1

Create an internal note (not shown to user) with:
- **Prior experiment:** name, hypothesis, verdict, diagnosis
- **Iteration strategy:** EXTEND/DEEPEN/REPLICATE/REFINE/PIVOT
- **What to preserve:** elements from the prior design that worked
- **What to change:** the specific adjustment the iteration strategy implies
- **Next hypothesis sketch:** starting point for Phase 1 formalization

Proceed to Phase 1 with this context.

---

## Phase 1: Formalize the hypothesis

Take whatever the user provides — a vague intuition, a research question, a formal hypothesis, or Phase 0 handoff from iteration — and produce:

1. **Research question** — One clear sentence. **If iterating:** must reference the prior finding (e.g., "Given that information source had no effect on deal rates in bargaining with a wide ZOPA, does tightening the ZOPA reveal a hidden treatment effect?")
2. **Core claim** — The directional causal claim being tested. **If iterating:** must address the diagnosis from Phase 0 (e.g., if diagnosis was DESIGN, the claim should target the design flaw; if HYPOTHESIS, the claim should be a new direction)
3. **Building on** (iteration only) — One sentence: "Building on [prior experiment name], which found [key finding]."
4. **What changed and why** (iteration only) — One sentence: "This hypothesis [extends/deepens/refines/pivots from] the prior by [specific change], because [diagnosis reason]."
5. **Key variables:**
   - **Treatment** (X) — The experimental manipulation (what changes between conditions)
   - **Outcome** (Y) — What we measure (cooperation rate, deal price, total surplus, etc.)
   - **Mechanism** (M) — How X is hypothesized to cause Y (the mediating pathway)
   - **Controls/Moderators** (Z) — Factors held constant or that may interact with the treatment
   - **Potential confounds** — What could explain Y besides X

If the user's input is vague, extrapolate the most interesting and novel interpretation autonomously. Favor interaction effects and boundary conditions over main effects. If the input is specific, follow it closely. Never stop to ask clarifying questions — commit to the strongest version and proceed.

---

## Phase 2: Triviality test

Before building the DAG, rigorously evaluate whether this hypothesis is trivial. **The triviality scorecard is not optional. Every hypothesis gets scored. Sharpening is automatic — present the result, not the options.**

### Triviality Scorecard

Score the hypothesis on 5 dimensions (1–5 each):

| Dimension | 1 (Trivial) | 3 (Moderate) | 5 (Novel) |
|-----------|-------------|--------------|-----------|
| **Prediction surprise** | Any undergrad predicts the direction | Experts would disagree on direction | Experts would predict the opposite |
| **Literature gap** | In textbooks | Studied but not in this exact setting | No direct experimental evidence |
| **Mechanism specificity** | "X causes Y" (no mechanism) | Mechanism named but not isolated | Competing mechanisms identified, design distinguishes them |
| **Boundary conditions** | Universal main effect claimed | One moderator identified | Interaction effect: "X causes Y only when Z" |
| **Testability in games** | Outcome not observable in transcripts | Observable but noisy | Cleanly observable action = outcome |

### Scoring thresholds

- **Score >= 18:** Proceed as-is (strong hypothesis).
- **Score 12–17:** Auto-sharpen — pick the single sharpening move that increases the score the most, apply it, update the formalization from Phase 1, re-score, and proceed.
- **Score < 12:** Auto-sharpen aggressively — apply 2+ sharpening moves, update the formalization, re-score, and proceed.

### Sharpening moves (pick the best one automatically)

- **Add an interaction effect:** "Trust increases cooperation" → "Trust increases cooperation *only when punishment is credible*"
- **Specify a boundary condition:** "Communication helps" → "Communication helps *only when interests are partially aligned; it backfires under pure competition*"
- **Test a mechanism:** "Reputation matters" → "Reputation increases cooperation *via the threat channel (fear of retaliation), not the reward channel (expectation of reciprocity)*"
- **Flip the obvious prediction:** "More information improves outcomes" → "More information about the opponent's weakness *reduces* joint surplus because it enables exploitation"
- **Add a surprising moderator:** "Cheap talk is effective" → "Cheap talk is effective *only when players can't verify claims — verifiable communication crowds out trust*"

### Output format (included in PDF, not shown as a checkpoint)

The scorecard, dimension-by-dimension reasoning, total score, any sharpening applied, and final score all appear in the PDF memo under the "Interestingness Argument" section. Do not present these to the user as a checkpoint — just proceed.

---

## Phase 3: Build the causal DAG

Construct a Pearlean DAG that represents the causal model. Build it and proceed directly to PDF generation.

### Text DAG (always)

```
Treatment (X) ──→ Mechanism (M) ──→ Outcome (Y)
     │                                    ↑
     └──────────────────────────────────→ │  (direct effect)
                                          │
Control (Z) ─────────────────────────→ Outcome (Y)
```

### Variable definitions table

| Variable | Type | Operationalization | How a game could capture it |
|----------|------|-------------------|--------------------------|
| X | Treatment | e.g., "Cheap talk allowed vs. not" | Game variant: one version has chat phase, one doesn't |
| M | Mediator | e.g., "Stated intentions" | Message content before action |
| Y | Outcome | e.g., "Cooperation rate" | Fraction of rounds where both cooperate |
| Z | Control | e.g., "Payoff structure" | Identical payoff matrix across conditions |

### Testable implications

List 2–4 testable predictions that follow from the DAG:
- "If the DAG is correct, cooperation rate should be higher in the cheap-talk condition"
- "If mechanism M is the pathway, blocking M should eliminate the treatment effect"
- "The effect should be larger when Z = [value]" (if moderation is hypothesized)

### Identification strategy

Explain how a game design could identify the causal effect:
- What would need to be randomized (the treatment assignment via game variant)
- What would need to be held constant (same payoffs, same number of rounds, same AI strategy across conditions)
- What potential confounds would be ruled out by the design
- What remains unidentified (limitations)

Proceed directly to PDF generation after building the DAG.

---

## Phase 4: Generate hypothesis memo PDF

Turn the hypothesis formalization, triviality scorecard, and causal DAG into a single polished PDF.

### 4a. Generate the DAG figure

Generate **one** publication-quality figure using Python (matplotlib). Save as PDF to `experiments/<name>/plots/`. Use the venv Python (`venv/bin/python`).

#### Figure: Causal DAG (`dag_<name>.pdf`)

Use matplotlib to draw the DAG (no networkx layout — use manual positions for clean results):
- **Node styling by type:**
  - Treatment (X): blue rounded box, bold white label
  - Mediator (M): gray rounded box
  - Outcome (Y): green rounded box, bold white label
  - Control (Z): white rounded box, dashed border
- **Edge styling:**
  - Causal paths: solid black arrows
  - Direct effects: dashed arrows
  - Control paths: thin gray arrows
- Layout: left-to-right (treatment on left, outcome on right)
- Clean white background, no grid, no axis
- Title: the research question
- Font: serif, 11pt for labels
- Legend in bottom-right corner

### 4b. Write the LaTeX memo

**Filename convention:**
- Fresh hypothesis: `experiments/<name>/hypothesis.tex`
- Iteration creates a new experiment directory: `experiments/<name>_v2/hypothesis.tex`
- General rule: each iteration gets its own directory (`<name>_v2/`, `<name>_v3/`, etc.)

Write the LaTeX document that embeds the DAG figure inline. The memo should compile to ~2–3 pages.

#### Document setup

```latex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{graphicx, booktabs, hyperref, enumitem, xcolor, titlesec, parskip}
```

#### Required sections (in order):

1. **Title** — "Hypothesis Memo: <title>" with date and status ("Pre-design"). **If iterating:** add version number and "Iteration of <prior experiment>"
2. **Prior Experiment Context** (iteration only) — Summary of what was tested, what was found, the verdict and diagnosis, and what this iteration changes. Include the key statistic from the prior results. This section is skipped for fresh hypotheses.
3. **Research Question** — one paragraph: question, motivation, why it matters. **If iterating:** must reference the prior finding and explain why this follow-up is needed.
4. **Interestingness Argument** — Contains the full triviality scorecard with all 5 dimension scores and reasoning, the total score, any sharpening moves applied, the final score after sharpening, and the argument for why this hypothesis is worth testing. Format the scorecard as a `booktabs` table in the PDF.
5. **Causal Model** — Figure (DAG) inline, then variable definitions table (`booktabs`), testable implications (numbered), identification strategy (bulleted)
6. **Next Steps** — brief note that this hypothesis is ready for `/design-experiment` to map to a game design

#### Figure placement

Use `[h!]` placement. The figure gets a `\caption{}` that is self-contained — readable without the surrounding text. Reference figure relative to plots dir: `\includegraphics[width=\textwidth]{plots/dag.pdf}`.

### 4c. Compile and open

```bash
cd experiments/<name> && pdflatex -interaction=nonstopmode hypothesis.tex
open hypothesis.pdf
```

Clean up auxiliary files:
```bash
rm -f hypothesis.aux hypothesis.log hypothesis.out
```

Report:

```
Hypothesis memo generated:
  experiments/<name>/hypothesis.pdf    (single PDF, DAG inline)

Source files:
  experiments/<name>/hypothesis.tex
  experiments/<name>/plots/dag.pdf

Next: run /design-experiment to map this hypothesis to a game design.
Or: run /hypothesize iterate <experiment> to iterate after results.
```

---

## Important rules

### Autonomy rules
- **Run to completion. Never stop to ask the user. If input is vague, extrapolate the most interesting version. If specific, follow it closely.**
- **The triviality scorecard is not optional. Every hypothesis gets scored. Sharpening is automatic — present the result, not the options.**
- **No checkpoints.** Do not present intermediate results and wait for feedback. Execute all four phases in a single uninterrupted run.

### DAG rules
- **The DAG drives everything.** Every variable must have a clear operationalization. Every edge must represent a claimed causal pathway. No decorative nodes.
- **Concrete operationalization.** "Information asymmetry" is not a treatment — "AI's valuation is hidden from the human (private) vs. shown to both (public)" is a treatment. Pin down exactly what changes.
- **Think about what the transcript reveals.** The outcome must be observable in a game transcript (choices, prices, accept/reject). Internal states (beliefs, intentions) are not directly measurable — only actions are. Flag any variable that would be hard to observe.

### Triviality rules
- **Push back on the obvious.** If the hypothesis is "X increases Y" and anyone in the field would say "of course," the scorecard will reflect that (low Prediction Surprise score) and auto-sharpening will fix it.
- **Interaction effects are usually more interesting than main effects.** "X causes Y" is less publishable than "X causes Y *only when Z*" or "X causes Y *through M, not through N*."
- **The scorecard goes in the PDF.** The reader should see exactly how the hypothesis scored, what sharpening was applied, and the final score.

### Iteration rules
- **Prior results are evidence, not constraints.** The prior experiment's findings inform the new hypothesis but do not limit it. If the prior result suggests pivoting to a completely different game, do it.
- **Always cite the prior experiment.** The new hypothesis memo must reference the prior experiment by name and summarize what was found. The reader should understand the lineage.
- **Version numbers are monotonic.** v1 → v2 → v3. Never overwrite a prior version's file.
- **The iteration strategy drives the formalization.** EXTEND adds conditions, DEEPEN adds mechanism tests, REPLICATE keeps the design, REFINE changes the game, PIVOT changes the hypothesis. Follow the strategy from Phase 0c.
- **Sharpening still applies.** Even iterated hypotheses go through the triviality scorecard. Prior results may make a hypothesis more interesting (confirmed mechanism) or less (expected result) — the score reflects this.

### Memo and figure rules
- **One PDF output.** The deliverable is a single compiled PDF with the DAG figure inline.
- **Use venv Python.** Run figure generation scripts with `venv/bin/python`.
- **Figure is PDF, saved to `experiments/<name>/plots/`.** LaTeX `\includegraphics` references it via relative path `plots/`.
- **The DAG is the centerpiece.** Spend the most effort making the figure clean and readable.
- **Figure caption must be self-contained.** The caption should be understandable without reading the body text.
- **Create directories if needed:** `mkdir -p experiments/<name>/plots`
- **Clean LaTeX aux files** after successful compilation.
