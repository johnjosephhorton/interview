---
name: run-experiment
description: Execute a simulation experiment — run all conditions, check transcripts, report readiness for analysis
argument-hint: "<game-name or experiment-name> [--n-per-cell 5] [--seed 42]"
---

# /run-experiment — Game Files → Simulations → Checker → Ready for Analysis

**Meta-goal:** Bridge the gap between game creation and analysis. Take one or more game folders (produced by `/create-2-player-game`), run the right number of simulations with the right randomization design, verify transcript quality via the checker, and either hand off to `/analyze-results` or loop back to `/improve` if the games are broken.

**Run to completion. Never stop to ask the user.** Make reasonable defaults for sample size and design. If games fail the checker at high rates, diagnose and fix before burning more tokens on broken games.

This skill handles the **"execute"** step. The full chain is: `/hypothesize` → `/design-experiment` → `/create-2-player-game` → **`/run-experiment`** → `/analyze-results`.

## Usage

- `/run-experiment bargain_1s_notalk` — Run a single game condition
- `/run-experiment cheap_talk_info_asymmetry` — Run all conditions of a multi-condition experiment
- `/run-experiment public_goods_mpcr --n-per-cell 10 --seed 42` — Override defaults
- `/run-experiment` — Infer the experiment from context (e.g., if `/create-2-player-game` just ran)

---

## Phase 1: Identify experiment scope

Determine what to run and how many conditions are involved.

### 1a. Resolve the target

From the argument or conversation context:

1. **Experiment manifest** — Check if `experiments/<arg>/manifest.toml` exists. If yes, read it — it contains the full experiment context: all condition game folders, hypothesis, predictions, primary outcome. This is the **preferred** resolution path.
2. **Direct game name** — Check if `games/<arg>/config.toml` exists. If yes, single-condition experiment. Look for a manifest that lists this game in its `[conditions]` (search `experiments/*/manifest.toml`) to get the broader experiment context.
3. **Experiment name** — Search for a design memo in `experiments/` matching the argument. If found, read the Game Implementations table to get all condition game folders.
4. **Related game folders** — If no manifest or design memo, look for game folders sharing a common prefix. Example: argument `bargain_1s` matches `bargain_1s_notalk`, `bargain_1s_talk`. Confirm by reading their configs.
5. **Context inference** — If no argument, check if `/create-2-player-game` just produced game files. Use those.

### 1b. Validate all game folders exist

For each condition:
- Verify `games/<name>/config.toml` exists
- Verify `games/<name>/manager.md`, `player.md`, `sim_human.md` exist
- Load the config to check for variables

If any game folder is missing, report which ones and stop — the user needs to run `/create-2-player-game` first.

### 1c. Determine the experimental design

For each condition, read `config.toml` and classify:

| Has variables? | Design | Behavior |
|---------------|--------|----------|
| No | None | Run N simulations with identical parameters |
| Yes (choice/sequence only) | Factorial | Use `--design factorial` to cross all levels |
| Yes (includes uniform) | Random | Use `--design random` with seed |

If **multi-condition** (multiple game folders), each condition is run separately. The conditions dict within each game handles within-game variation; between-game variation is the treatment.

---

## Phase 2: Determine sample size

Choose N intelligently based on the experimental design.

### Default sample sizes

| Scenario | Default N | Rationale |
|----------|-----------|-----------|
| **Pilot** (first run of a new game) | 1× factorial cells | Debug game logic, verify checker passes |
| **Pilot with replication** | 3× factorial cells | Enough to spot systematic issues |
| **Production single-condition** | 30 sessions | Minimum for CLT-based inference |
| **Production multi-condition** | 30 per condition | Standard between-subjects minimum |
| **Production factorial within-condition** | 5× factorial cells | 5 replications per cell, enough for cell means |

### Decision logic

1. **Check for existing transcripts.** Glob `transcripts/<game>/*.json` (excluding `*_check.json`).
   - **No prior transcripts** → This is a pilot. Use **1× factorial cells** (or N=1 if no variables). Goal: verify the game works.
   - **Prior transcripts exist but checker failures >30%** → This is a re-pilot after fixes. Use **1× factorial cells** again.
   - **Prior transcripts exist with >70% pass rate** → This is production. Use **5× factorial cells** (or N=30 if no variables).

2. **User override.** If the user specifies `--n-per-cell K`, use K replications per factorial cell (total = K × num_cells). If `--n N` is specified directly, use N total.

3. **Cap at 50 simulations per condition per run** to avoid runaway costs. If more are needed, the user can re-run. Print the estimated cost: `N_sims × ~4K tokens/sim ≈ X tokens`.

### Compute total simulations

For each condition:
```
if factorial:
    num_cells = product(len(var.values) for choice/sequence vars)
    total = n_per_cell × num_cells
else:
    total = n
```

Print the execution plan before running:
```
Execution plan:
  bargain_1s_notalk: 9 cells × 1 rep = 9 sims (factorial, seed=42)
  bargain_1s_talk:   9 cells × 1 rep = 9 sims (factorial, seed=42)
  Total: 18 simulations
```

---

## Phase 3: Execute simulations

Run simulations using the `interview simulate` CLI command. This reuses all existing infrastructure (randomization, auto-save, auto-check).

### 3a. Choose seed

- If user provides `--seed`, use it for all conditions (same seed = same variable draws per condition, enabling paired comparisons)
- If no seed and this is a pilot, pick a memorable seed (e.g., `42`, `1022`, `2024`)
- If no seed and this is production, omit seed (let each simulation draw independently)
- **Record the seed used** — it goes in the writeup for reproducibility

### 3b. Run each condition

For each game condition, execute:

```bash
source venv/bin/activate
interview simulate <game-name> \
  --design <factorial|random> \
  --seed <seed> \
  -n <total_sims> \
  --max-turns <turns>
```

**Run conditions sequentially, not in parallel.** Each `interview simulate` already parallelizes its N simulations internally via `asyncio.gather`. Running multiple conditions simultaneously would overload the API.

**Capture output.** Parse the CLI output for:
- Number of simulations completed
- Token usage
- Checker pass/fail counts per simulation
- Saved file paths

### 3c. Handle max-turns

Read `config.toml` settings:
- If the game has a `max_rounds` or similar setting, set `--max-turns` to `max_rounds + 2` (buffer for opening + closing)
- Default: `--max-turns 15` for multi-round games, `--max-turns 5` for one-shot games
- The goal is to give enough turns for the game to complete naturally (GAME OVER detection handles early termination)

---

## Phase 4: Check results and decide

After all conditions have run, evaluate transcript quality to decide whether to proceed or fix.

### 4a. Aggregate checker results

For each condition:
1. Glob `transcripts/<game>/*_check.json` from this run (match by timestamp)
2. Compute per-criterion pass rates
3. Compute overall pass rate

Build a summary table:

```
Checker Results:
                        arithmetic  totals  input_val  rules  ai_strat  info_leak  manip_resist  termination  instructions
bargain_1s_notalk  (9)    9/9       9/9      9/9       9/9     9/9       9/9        9/9          9/9          9/9
bargain_1s_talk    (9)    9/9       8/9      9/9       9/9     7/9       9/9        9/9          9/9          9/9
```

### 4b. Decision gate

| Overall pass rate | Action |
|------------------|--------|
| **100%** | Proceed to analysis. Print: "All transcripts passed. Ready for /analyze-results." |
| **70–99%** | Proceed with warnings. Print: "N transcripts failed. Excluding failures, proceeding to analysis. Consider /improve to fix recurring issues." |
| **30–69%** | Pause. Print the failure pattern. Run `/improve` diagnostics (read failures, identify root cause, suggest fix). Do NOT proceed to analysis — the game is broken. |
| **<30%** | Stop. Print: "Game is fundamentally broken. Run /improve <game> to diagnose." List the most common failure criteria. |

### 4c. Auto-fix loop (if 30–69% pass rate)

If the pass rate is in the fixable range:

1. Read the failing checker results to identify the most common failing criterion
2. Read the relevant game file section (using the criterion→location mapping from `/improve`)
3. Apply a minimal fix (same approach as `/improve` single-game workflow)
4. Re-run the **pilot** (1× factorial cells) to verify the fix
5. If pass rate improves to ≥70%, proceed. If not, report the issue and stop.

**Limit:** At most 2 auto-fix iterations. If still broken after 2 fixes, stop and tell the user to investigate manually.

---

## Phase 5: Report and hand off

### 5a. Execution summary

Print a concise summary:

```
Experiment: cheap_talk_info_asymmetry
Conditions: 4 (bargain_1s_notalk, bargain_1s_talk, bargain_2s_notalk, bargain_2s_talk)
Total simulations: 36
Total tokens: 142,380 input / 38,291 output
Checker: 34/36 passed (94%)
Seed: 1022
Design: factorial

Transcripts saved to:
  transcripts/bargain_1s_notalk/2026-02-12_14-30-00_sim*.json
  transcripts/bargain_1s_talk/2026-02-12_14-32-15_sim*.json
  transcripts/bargain_2s_notalk/2026-02-12_14-34-22_sim*.json
  transcripts/bargain_2s_talk/2026-02-12_14-36-41_sim*.json
```

### 5b. Quick data peek

Before handing off, print a 1-table preview of the data so the user sees results immediately. Extract the primary outcome for each condition.

**If a manifest exists** (`experiments/<experiment>/manifest.toml`), use it to:
- Know what the **primary outcome** is (e.g., `deal_rate`, `contribution`, `acceptance_rate`)
- Label conditions with their human-readable labels from `[conditions.*.label]`
- Compare results against **predictions** from `[predictions]` — mark each prediction as CONFIRMED, REFUTED, or UNCLEAR

```
Quick peek: deal_rate (primary outcome)
Hypothesis: Cheap talk helps under one-sided but hurts under two-sided asymmetry

  Condition                  Label                  Deal Rate   Prediction    Result
  bargain_1s_notalk          One-sided / No talk    100% (9/9)  baseline      —
  bargain_1s_talk            One-sided / Cheap talk  89% (8/9)  higher        UNCLEAR (↓11pp)
  bargain_2s_notalk          Two-sided / No talk     78% (7/9)  baseline      —
  bargain_2s_talk            Two-sided / Cheap talk   56% (5/9)  lower         CONFIRMED (↓22pp)

  Interaction prediction (crossover): PARTIALLY CONFIRMED
```

**If no manifest exists**, fall back to generic extraction — look for GAME OVER boxes and extract final earnings, or detect "no deal" outcomes:

```
Quick peek (primary outcome):
  bargain_1s_notalk:  deal rate = 100% (9/9),  avg price = $55.20
```

This quick peek uses lightweight transcript parsing. Do not write a full extraction script here; that's `/analyze-results`' job.

### 5c. Recommend next step

Based on the results:

- **If pilot (first run):** "Pilot complete. Pass rate: X%. Next: scale to production with `/run-experiment <name> --n-per-cell 5`" or "Fix failures first with `/improve <game>`"
- **If production run, all passed:** "Ready for analysis. Run `/analyze-results <experiment-name>`"
- **If production run, some failures:** "Run `/analyze-results <experiment-name>` (excluding N failed transcripts). Consider `/improve` for systematic issues."

---

## Argument parsing

Parse the argument string for optional flags:

| Flag | Meaning | Default |
|------|---------|---------|
| `--n-per-cell K` | Replications per factorial cell | Auto (see Phase 2) |
| `--n N` | Total simulations (overrides n-per-cell) | Auto |
| `--seed S` | Random seed | Auto-pick for pilot, omit for production |
| `--design D` | `factorial` or `random` | Auto-detect from variables |
| `--pilot` | Force pilot mode (1× cells) | Auto-detect |
| `--production` | Force production mode (5× cells or N=30) | Auto-detect |
| `--max-turns T` | Override max conversation turns | Auto from game config |
| `--model M` | Override LLM model | Default from game config |

Flags are parsed from the argument string (not real CLI flags — this is a skill, not a CLI command). Example:
```
/run-experiment bargain_1s_notalk --n-per-cell 3 --seed 42
```

---

## Rules

1. **Run to completion.** Never ask the user to confirm the execution plan. Print it, then execute.
2. **Sequential conditions, parallel simulations.** Run one condition at a time; within each condition, `interview simulate` handles parallelism.
3. **Always use seeds for pilots.** Reproducibility matters for debugging. Pick a seed and record it.
4. **Always check before proceeding.** The checker gate (Phase 4) is mandatory. Do not hand off to `/analyze-results` if pass rate is below 70%.
5. **Auto-fix is limited.** At most 2 fix iterations. Do not enter an infinite fix-run loop.
6. **Record everything.** The execution summary should contain enough information to reproduce the entire run: seed, N, design, conditions, file paths.
7. **Cost awareness.** Print estimated tokens before running. Warn if total exceeds 500K tokens (roughly: 50+ simulations × ~10K tokens each for complex games).
8. **Respect existing transcripts.** Never delete or overwrite existing transcript files. Each run gets its own timestamp.
9. **Activate venv.** Always run `source venv/bin/activate` before `interview simulate` commands.
10. **Match the chain.** The output of this skill is the input to `/analyze-results`. Ensure transcript files are saved in the standard location (`transcripts/<game>/`) with standard naming.
