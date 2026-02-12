---
name: research-loop
description: Run the full automated research pipeline — from hypothesis through experiment to results — and iterate until we learn something interesting
argument-hint: "[hypothesis or research question] [--max-iterations 3]"
---

# /research-loop — Automated Research Pipeline with Iteration

**Meta-goal:** Run the complete hypothesis → design → build → simulate → analyze loop, and then iterate. Each iteration refines the hypothesis based on what was learned, designs a sharper experiment, runs it, and evaluates whether we've found something interesting. Stop when we have a compelling finding or exhaust the iteration budget.

This is a **thin orchestrator**. It invokes the individual skills (`/hypothesize`, `/design-experiment`, `/create-2-player-game`, `/run-experiment`, `/analyze-results`, `/improve`) in sequence and makes the routing decisions between them. It does NOT duplicate their internal logic.

## Usage

- `/research-loop does cheap talk help or hurt in bargaining under asymmetric information?` — Start from a hypothesis
- `/research-loop --from-design cheap_talk_info_asymmetry` — Resume from an existing design memo
- `/research-loop --from-game bargain_1s_notalk` — Resume from an existing game (skip hypothesis + design)
- `/research-loop --from-results bargain_1s_notalk` — Resume from existing transcripts (skip to analysis + iterate)
- `/research-loop` — Pick up from context or find the most recent unanalyzed experiment

---

## Pipeline overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ITERATION N                              │
│                                                             │
│  ┌──────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐  │
│  │hypothesize├──►│ design  ├──►│ create  ├──►│   run    │  │
│  └──────────┘   └─────────┘   └────┬────┘   └────┬─────┘  │
│                                    │              │         │
│                                    │   ┌──────┐   │         │
│                                    └──►│improve◄──┘         │
│                                        └──────┘  (if fail)  │
│                                           │                 │
│                              ┌────────────┘                 │
│                              ▼                              │
│                        ┌──────────┐                         │
│                        │ analyze  │                         │
│                        └────┬─────┘                         │
│                             │                               │
└─────────────────────────────┼───────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Decision gate:   │
                    │  interesting?     │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         YES: stop      PARTIALLY:       NO: diagnose
         & report       iterate           & pivot/stop
```

---

## Stage 0: Parse entry point

Determine where to enter the pipeline based on the argument:

| Argument pattern | Entry point | What to skip |
|-----------------|-------------|--------------|
| A research question or hypothesis | Stage 1 (hypothesize) | Nothing — full pipeline |
| `--from-design <name>` | Stage 3 (create game) | Stages 1–2 |
| `--from-game <name>` | Stage 4 (run experiment) | Stages 1–3 |
| `--from-results <name>` | Stage 5 (analyze) | Stages 1–4 |
| No argument, prior context | Infer from context | Depends |

Also parse:
- `--max-iterations N` (default: 3) — maximum hypothesis→results cycles
- `--pilot-only` — run pilots only, don't scale to production
- Any flags are stripped from the argument before passing to sub-skills

---

## Stage 1: Hypothesize

**Invoke:** `/hypothesize <research question>`

On iteration 2+, invoke with iteration context:
`/hypothesize iterate <experiment-name>`

This reads the machine-readable block from the prior results memo (`experiments/<name>/results.tex`) and refines the hypothesis based on what was learned.

**Gate:** Check the triviality score from the hypothesis memo.
- Score ≥ 15 → proceed to Stage 2
- Score < 15 → the hypothesis is too trivial even after sharpening. Report: "Hypothesis too trivial to pursue. Consider a different research question." **Stop the loop.**

**Output:** `experiments/<name>/hypothesis.tex` + `.pdf`

---

## Stage 2: Design experiment

**Invoke:** `/design-experiment`

The hypothesis memo is in context from Stage 1, so `/design-experiment` will pick it up automatically.

**Gate:** Check that the design memo contains:
- At least 1 condition with a 12-item spec
- A clear primary outcome measure
- An analysis plan

If the design memo is missing any of these, something went wrong. Report and stop.

**Output:** `experiments/<name>/design.tex` + `.pdf`, 12-item specs ready for game creation

---

## Stage 3: Create game(s)

**Invoke:** `/create-2-player-game` for each condition specified in the design memo.

For multi-condition experiments, invoke once per condition. The design memo's Game Implementations table lists all conditions and their game folder names.

**Gate:** After each game is created, verify:
- All 4 files exist (`config.toml`, `manager.md`, `player.md`, `sim_human.md`)
- The smoke test passed (the skill runs one internally)

If any game fails its smoke test, the skill already handles retries. If it still fails after the skill's internal retries, route to `/improve` and retry once more. If still failing, report and stop.

**Output:** `games/<name>/` folders with all 4 files per condition

---

## Stage 4: Run experiment

**Invoke:** `/run-experiment <experiment-name>`

First run is always a **pilot** (1× factorial cells per condition). This validates game quality before committing to a full run.

**Gate:** Check the pilot results:

| Pilot checker pass rate | Action |
|------------------------|--------|
| **100%** | Scale to production: re-invoke `/run-experiment <name> --production` |
| **70–99%** | `/run-experiment` handles auto-fix internally. If it succeeds, proceed. |
| **<70%** | Invoke `/improve <game>` for each failing game. Then re-pilot. |

**Fix budget:** At most 2 improve→re-pilot cycles per iteration. If still below 70% after 2 fixes, report the issue and **stop the loop** — the game design needs manual attention.

After pilot passes, run production:
- `/run-experiment <name> --production` (5× factorial cells or N=30 per condition)

**Output:** Transcripts in `transcripts/<game>/`, checker results alongside

---

## Stage 5: Analyze results

**Invoke:** `/analyze-results <experiment-name>`

This extracts data, runs statistics, generates figures, and writes the results memo PDF.

**Gate:** Read the Evaluation section and the machine-readable context block from the results memo. Parse the verdict:

| Verdict | Action |
|---------|--------|
| `YES_INTERESTING` | **Stop the loop.** We found something. Report the finding. |
| `PARTIALLY` | **Iterate** if iterations remain. The results memo's `proposed_changes` field tells us what to refine. |
| `NO_NULL` | **Iterate with refinement** if iterations remain. Diagnosis guides the change: POWER→replicate with more N, DESIGN→redesign, HYPOTHESIS→pivot. |
| `NO_UNINFORMATIVE` | **Iterate with pivot** if iterations remain. The current hypothesis/design isn't generating useful signal. |

---

## Stage 6: Iterate or stop

### If iterating (PARTIALLY, NO_NULL, NO_UNINFORMATIVE):

1. Check iteration budget: if `current_iteration >= max_iterations`, stop and report.
2. Read the `next_archetype` from the results memo:

| Archetype | Pipeline re-entry |
|-----------|------------------|
| `REPLICATE` | Stage 4 (same games, more N) |
| `REFINE` | Stage 3 (same hypothesis, modified game design) |
| `EXTEND` | Stage 2 (same hypothesis, add conditions) |
| `DEEPEN` | Stage 1 (refined hypothesis, new mechanism/moderator) |
| `PIVOT` | Stage 1 (different hypothesis entirely) |
| `HUMAN-TEST` | Stop — report that in-silico results are ready for human testing |

3. Re-enter the pipeline at the appropriate stage with the refined inputs.

### If stopping (YES_INTERESTING or budget exhausted):

Print a final summary:

```
═══ Research Loop Complete ═══

Iterations: 2 of 3
Final verdict: YES_INTERESTING

Hypothesis: Cheap talk increases deal rates under one-sided asymmetry
            but decreases them under two-sided asymmetry.

Key finding: Deal rate crossover interaction (β₃ = -0.34, p = 0.02).
             One-sided+talk: 85% vs one-sided+no-talk: 72% (+13pp).
             Two-sided+talk: 48% vs two-sided+no-talk: 65% (-17pp).

Artifacts:
  Hypothesis memo:  experiments/cheap_talk_info_asymmetry/hypothesis.pdf
  Design memo:      experiments/cheap_talk_info_asymmetry/design.pdf
  Results memo:     experiments/cheap_talk_info_asymmetry/results.pdf
  Data:             experiments/cheap_talk_info_asymmetry/data/data.csv
  Figures:          experiments/cheap_talk_info_asymmetry/plots/results_*.pdf
  Transcripts:      transcripts/bargain_*s_*talk/

Next step: Run with human subjects to validate the LLM-derived finding.
```

---

## Iteration state tracking

The **experiment manifest** (`experiments/<name>/manifest.toml`) is the persistent state across iterations. It is:
- **Created** by `/design-experiment` (Stage 2) with hypothesis, conditions, predictions
- **Read** by `/run-experiment` (Stage 4) for condition discovery and prediction-aware quick peek
- **Updated** by `/analyze-results` (Stage 5) with results artifact paths
- **Read** by `/research-loop` to determine iteration state and next action

On iteration 2+, the manifest from the PRIOR iteration persists. The new iteration creates a NEW manifest (e.g., `cheap_talk_info_asymmetry_v2.manifest.toml`). The prior manifest's `[artifacts].results_memo` points to the results that informed the new iteration.

Print the iteration state at the start of each iteration so the user can follow progress:

```
Iteration 1 of 3:
  Hypothesis: [from manifest or freshly generated]
  Prior result: [none — first iteration]
  Entry point: Stage 1 (hypothesize)
  Manifest: experiments/cheap_talk_info_asymmetry/manifest.toml

Iteration 2 of 3:
  Hypothesis: [refined — from machine-readable block in prior results memo]
  Prior result: PARTIALLY — deal rates didn't vary, but surplus division did
  Diagnosis: DESIGN — game too short for bargaining dynamics to emerge
  Change: REFINE — increase to 10 rounds, adjust AI concession rate
  Entry point: Stage 3 (create game with modified design)
  Prior manifest: experiments/cheap_talk_info_asymmetry/manifest.toml
  New manifest: experiments/cheap_talk_info_asymmetry_v2/manifest.toml
```

---

## Rules

1. **Invoke skills, don't replicate them.** This skill's job is routing and decisions. The individual skills handle execution. Invoke them via the Skill tool.

2. **One stage at a time.** Complete each stage fully before moving to the next. Read the output artifacts (memos, transcripts) before deciding the next action.

3. **Respect the gates.** Every stage has a quality gate. Do not skip gates — they prevent wasting tokens on broken experiments.

4. **Budget is hard.** `max_iterations` is a hard cap, not a suggestion. When budget is exhausted, stop and report what was learned (even if the answer is "nothing conclusive").

5. **Iteration > repetition.** Each iteration should change something substantive (hypothesis, design, game mechanics). Running the same experiment twice with the same design is only justified by `REPLICATE` archetype (underpowered).

6. **Context management.** Each skill generates substantial output. After each stage, summarize what was produced and what matters for the next stage. Do not carry raw transcripts or full LaTeX source in working memory — reference file paths.

7. **Fail loudly.** If any stage fails in a way that can't be auto-fixed, stop the loop immediately and explain what went wrong. Do not silently skip stages.

8. **Record the journey.** The sequence of iterations IS the research contribution. The final results memo should reference prior iterations (e.g., "Iteration 1 found X, which led us to test Y in Iteration 2"). The machine-readable context block enables this automatically.

9. **Prefer depth over breadth.** If the first experiment yields a partially interesting result, deepen it (test the mechanism, find the boundary) rather than pivoting to a completely different question. Pivot only when the current line is a dead end.

10. **Stop when interesting.** The goal is to find ONE interesting, credible finding — not to run as many experiments as possible. Stop as soon as the verdict is `YES_INTERESTING`.
