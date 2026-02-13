---
name: analyze-results
description: Analyze experimental results from simulation transcripts, write up findings as a full research memo PDF (hypothesis through next steps), and evaluate what was learned
argument-hint: "<game-name> [or experiment name if multi-condition]"
---

# /analyze-results — Transcripts + Checker → Data Extraction → Analysis → Research Writeup PDF

**Meta-goal:** Close the loop. Take the raw simulation transcripts and checker results from one or more game conditions, extract structured data, perform statistical analysis, write up the full story — from the original hypothesis through experimental design, results, evaluation, and what to do next — as a publication-quality research memo PDF. The output should be a self-contained document that a collaborator can read and understand whether we learned something interesting and what the next experiment should be.

**Run to completion. Never stop to ask the user.** If information is missing (e.g., no hypothesis memo exists), reconstruct the hypothesis from the game design files. If results are ambiguous, say so — the writeup should be honest about what was and wasn't learned.

This skill handles the **"what did we learn"** — from transcripts to insights to next steps. It sits at the end of the chain: `/hypothesize` → `/design-experiment` → `/create-2-player-game` → simulate → **`/analyze-results`**.

## Usage

- `/analyze-results bargain_1s_notalk` — Analyze results for a single game condition
- `/analyze-results cheap_talk_info_asymmetry` — Analyze results across all conditions of a multi-condition experiment (looks for all related game folders)
- `/analyze-results` — Infer the experiment from context or the most recent transcripts

---

## Phase 1: Gather all inputs

Collect everything needed for the writeup. Read files in parallel where possible.

### 1a. Identify the experiment scope and load hypothesis context

From the argument or context, determine the experiment scope. **Always check for the experiment manifest first** — it's the structured source of truth.

**Resolution order:**

1. **Experiment manifest** — Check if `experiments/<arg>/manifest.toml` exists. If yes, read it — it contains everything: hypothesis, predictions, condition list, primary outcome, variable definitions, and links to upstream artifacts. This is the **preferred** path.
2. **Single condition** (one game folder, e.g., `bargain_1s_notalk`) — analyze that game alone. Check if any manifest in `experiments/*/manifest.toml` lists this game in its `[conditions]` to get the broader experiment context.
3. **Multi-condition experiment** (e.g., `cheap_talk_info_asymmetry`) — find all related game folders via manifest, design memo, or prefix matching.

### 1b. Read the upstream materials

**If manifest exists**, read it first, then use its `[artifacts]` links to find memos:

```toml
[artifacts]
hypothesis_memo = "experiments/<name>/hypothesis.md"
design_memo = "experiments/<name>/design.md"
```

From the manifest, extract and carry forward:
- `hypothesis` — the one-sentence hypothesis (goes directly into the Research Question section)
- `research_question` — the one-sentence question
- `triviality_score` — from the hypothesis scorecard
- `[variables]` — treatment (X), outcome (Y), mechanism (M), control (Z)
- `[design]` — primary outcome, primary test, design type
- `[conditions]` — all game folders with labels and treatment values
- `[predictions]` — named predictions to evaluate against results

**If no manifest exists**, fall back to searching:
- **Hypothesis memo:** `experiments/*/hypothesis.md` matching the experiment (fall back to `.tex` for legacy experiments)
- **Design memo:** `experiments/*/design.md` matching the experiment (fall back to `.tex` for legacy experiments)
- **Game files:** For each condition, read `games/<name>/config.toml`, `games/<name>/manager.md`, `games/<name>/player.md`

If no hypothesis or design memo exists AND no manifest exists, reconstruct the hypothesis and design from the game files alone. The writeup still needs a hypothesis section — infer it from the game structure, treatment variation, and parameterization.

### 1c. Read all transcripts and checker results

For each game condition:
1. Glob `transcripts/<game>/*.json` (excluding `*_check.json`) — these are the simulation transcripts
2. Glob `transcripts/<game>/*_check.json` — these are the checker results
3. Parse each transcript JSON: extract `messages`, `conditions` (the drawn variable values), `total_input_tokens`, `total_output_tokens`
4. Parse each checker JSON: extract `criteria` (list of {criterion, passed, explanation}), `overall_passed`

### 1d. Read the checker prompt for criterion definitions

Read `prompts/checker.md` to understand the 9 checker criteria and their definitions.

---

## Phase 2: Extract structured data from transcripts

For each transcript, extract game outcomes by reading the message history. The extraction logic depends on the game type — infer from the game config and manager prompt.

### Common extractions (adapt per game type):

**Bargaining games:**
- Deal reached (boolean)
- Deal price (if deal)
- Rounds to deal
- Human earnings, AI earnings
- Efficiency (surplus captured / ZOPA)
- First offer (AI or human depending on structure)
- Each round's offer and offerer

**Public goods games:**
- Per-round contributions (human, AI)
- Per-round earnings (human, AI)
- Total contributions, total earnings
- Cooperation rate (contribution / endowment)
- Free-riding incidence

**Ultimatum/dictator games:**
- Proposed split
- Acceptance/rejection
- Earnings

**Trust/investment games:**
- Amount sent, amount returned
- Return ratio
- Earnings

**General (all games):**
- Number of rounds played
- Whether game terminated properly (from checker)
- Condition variables (from `conditions` dict)
- Token usage

### Output format

Build a Python list of dicts (one per transcript) with all extracted fields. Use this as the data table for analysis.

**IMPORTANT:** Write the extraction as a Python script and execute it. Do NOT try to manually read and parse dozens of transcripts. Use the `json` module to load each file, regex or string matching to extract outcomes from the message text, and produce a clean CSV.

Save the extracted data as `experiments/<experiment_name>/data/data.csv`.

---

## Phase 3: Statistical analysis

Analyze the extracted data. The analysis plan depends on the experimental design.

### 3a. Descriptive statistics

For each condition (or overall if single-condition):
- N (number of sessions)
- Key outcome means and SDs (deal rate, price, earnings, contributions, etc.)
- Checker pass rate per criterion

Present as a summary table.

### 3b. Inferential analysis (if multi-condition)

Match the analysis to the experimental design. **If a manifest exists**, use its `[design]` section to drive the analysis:
- `primary_outcome` → the dependent variable
- `primary_outcome_type` → `binary` (use logistic regression) or `continuous` (use linear regression)
- `primary_test` → the specific test to run (e.g., "interaction term β₃")
- `[predictions]` → named predictions to formally evaluate (for each, report CONFIRMED / REFUTED / UNCLEAR with the supporting statistic)

**Between-conditions comparison (factorial design):**
- Use the analysis plan from the manifest or design memo
- For binary outcomes (deal rate): proportions + chi-squared or Fisher's exact test, logistic regression with treatment indicators
- For continuous outcomes (price, earnings): t-tests or ANOVA, linear regression with treatment indicators
- For factorial designs: include interaction terms
- Report effect sizes, confidence intervals, p-values

**Within-condition variation (parameterized game):**
- Regression of outcomes on condition variables (e.g., price ~ buyer_value + seller_cost)
- Test whether the AI strategy responds appropriately to parameter changes
- Identify anomalies (e.g., constant behavior despite varying parameters)

**Use Python with scipy.stats or statsmodels.** Keep it simple — the goal is to determine whether the hypothesis was supported, not to publish a methods paper. Write and execute the analysis as a Python script.

### 3c. Checker analysis

Aggregate checker results across all transcripts:
- Overall pass rate
- Per-criterion pass rate
- If any criterion fails systematically, flag it as a game design issue (not a research finding)

### 3d. Key findings

Synthesize 3-5 key findings from the data. For each finding:
1. State the finding as a clear sentence
2. Cite the supporting evidence (statistic, table, figure)
3. Relate it to the original hypothesis — does it support, refute, or complicate?

---

## Phase 4: Generate figures

Create publication-quality figures using matplotlib. Save as PDF to `experiments/<experiment_name>/plots/`. Generate figures using venv Python.

### Required figures (adapt per game type):

**Figure 1: Main outcome by condition** — The central result.
- Bargaining: bar chart of deal rate by condition, or box plot of deal price by condition
- Public goods: line plot of mean contribution across rounds, by multiplier condition
- General: bar chart of primary outcome by condition with error bars (95% CI or SEM)

**Figure 2: Outcome distribution or trajectory**
- Bargaining: scatter plot of (ZOPA, price) or surplus efficiency by condition
- Public goods: contribution trajectories (individual or mean per condition)
- General: histogram or density plot of key outcome

**Figure 3: Condition variable effects** (if parameterized)
- Regression scatter with fit line: outcome ~ key condition variable
- Or heatmap of outcomes across factorial cells

### Figure conventions (match existing project style):
- Use PDF output format
- Save to `experiments/<experiment_name>/plots/results_<figure_name>.pdf`
- Clean, minimal style (no chartjunk)
- Label axes clearly with units
- Include figure captions in the LaTeX document
- Use colorblind-friendly palettes
- Generate each figure with a standalone Python script

---

## Phase 5: Write the research memo PDF

Produce a LaTeX document at `experiments/<experiment_name>/results.tex` and compile to PDF. This is the main deliverable.

### Document structure

Follow this section structure exactly:

```latex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{graphicx, booktabs, hyperref, enumitem, xcolor, titlesec, parskip, amsmath}

\begin{document}

\begin{center}
{\Large \textbf{Experiment Results:\\<Experiment Title>}}\\[0.5em]
{\large \today \quad $\cdot$ \quad Status: Post-analysis}
\end{center}

%% --- 1. RESEARCH QUESTION ---
\section*{Research Question}
% Restate the hypothesis. If a hypothesis memo exists, summarize it.
% If not, reconstruct from the game design.
% 1-2 paragraphs. Include the triviality score if available.

%% --- 2. EXPERIMENTAL DESIGN ---
\section*{Experimental Design}
% Summarize the game structure, conditions, treatment manipulations.
% Include the design matrix figure if multi-condition.
% Reference the design memo if it exists.
% Keep concise — this is recap, not the full design memo.

%% --- 3. DATA OVERVIEW ---
\section*{Data Overview}
% Sample: N sessions total, N per condition
% Checker results: pass rate, any systematic issues
% Data quality notes: any exclusions, anomalies
% Summary statistics table

%% --- 4. RESULTS ---
\section*{Results}

\subsection*{Primary Outcome}
% The main finding. Include Figure 1.
% State clearly: "The hypothesis predicted X. We observed Y."
% Include the key test statistic and p-value.

\subsection*{Secondary Outcomes}
% Additional analyses. Include Figure 2 if relevant.
% Mechanism checks, heterogeneity, etc.

\subsection*{Parameter Effects}
% If parameterized: how did outcomes vary with condition variables?
% Include Figure 3 if relevant.

%% --- 5. EVALUATION ---
\section*{Evaluation}

\subsection*{Did We Learn Something Interesting?}
% This is the most important section. Be honest.
% Score the findings on the same triviality dimensions used in /hypothesize:
%   - Was the result surprising?
%   - Does it fill a literature gap?
%   - Did we learn about mechanisms?
%   - Did we find boundary conditions or interactions?
%   - How clean/credible is the evidence?
%
% Explicitly state one of:
%   (a) "Yes — we found [specific interesting thing]"
%   (b) "Partially — we found [X] but [Y] is unclear"
%   (c) "No — the result is null/expected/uninformative because [reason]"
%
% If (b) or (c), diagnose WHY:
%   - Design problem (game doesn't isolate the mechanism)
%   - Power problem (not enough sessions, effect too small)
%   - Implementation problem (game bugs, checker failures, LLM behavior)
%   - Hypothesis problem (the hypothesis was wrong or trivial)

\subsection*{Limitations}
% Specific to these results (not generic disclaimers).
% What could explain the findings besides the hypothesis?
% What would change if we used human subjects instead of sim_human?

%% --- 6. NEXT EXPERIMENT ---
\section*{Next Experiment}

% This is the second most important section.
% Propose the single most valuable next experiment. Be specific:
%   - What hypothesis does it test?
%   - What game structure?
%   - How does it build on what we just learned?
%   - What would we expect to find?
%
% Choose from these archetypes:
%   (a) REPLICATE: Same experiment, more sessions (if underpowered)
%   (b) EXTEND: Add a new condition to the current design
%   (c) DEEPEN: Keep the same game, but test a mechanism/moderator
%   (d) PIVOT: Different game/hypothesis entirely (if current one is a dead end)
%   (e) HUMAN-TEST: Run the same game with real human subjects
%   (f) REFINE: Same hypothesis, better game design
%
% State which archetype and why.
% End with a concrete next step: "Run /hypothesize iterate <experiment>" or
% "Run /create-2-player-game [game-name]" or "Run interview simulate ..."

%% --- MACHINE-READABLE CONTEXT (for /hypothesize iterate) ---
% This block is parsed by /hypothesize Phase 0 to enable automated iteration.
% It MUST be included in every results memo.

\subsection*{Prior Experiment Context (Machine-Readable)}
\begin{verbatim}
prior_hypothesis: <the hypothesis that was tested>
verdict: <YES_INTERESTING / PARTIALLY / NO_NULL / NO_UNINFORMATIVE>
diagnosis: <DESIGN / POWER / IMPLEMENTATION / HYPOTHESIS / NA>
key_finding: <one-sentence summary>
key_statistic: <the single most important number, e.g., "deal rate = 100% across all conditions">
dag_variables: <X=treatment, M=mechanism, Y=outcome, Z=control>
testable_implications_results: <prediction1=CONFIRMED/REFUTED, prediction2=CONFIRMED/REFUTED, ...>
next_archetype: <EXTEND / DEEPEN / REPLICATE / REFINE / PIVOT / HUMAN-TEST>
proposed_changes: <specific changes for the next experiment>
next_hypothesis_sketch: <rough hypothesis for the next iteration>
\end{verbatim}

\end{document}
```

### Writing guidelines

- **Be honest, not promotional.** Null results are results. Ambiguous findings should be stated as ambiguous. Do not oversell.
- **Be specific.** "The deal rate was 78% vs 45% (p = 0.03)" not "we found significant differences."
- **Connect findings to the hypothesis.** Every result should explicitly reference what the hypothesis predicted.
- **The Evaluation section is the core.** Spend the most effort here. A collaborator reading only this section should understand whether the experiment was worth running and why.
- **The Next Experiment section must be actionable.** It should contain enough detail to immediately run `/hypothesize` or `/design-experiment` on the follow-up.
- **Tables > prose** for presenting data. Use booktabs-style tables.
- **Figures in the document** — reference them inline, don't just append them.
- **Machine-readable block is mandatory.** Every results memo must include the "Prior Experiment Context (Machine-Readable)" `\begin{verbatim}` block in the Next Experiment section. This is the interface that `/hypothesize iterate` parses to enable automated iteration. Fill in every field — use `NA` for fields that don't apply.

### Compilation

```bash
cd experiments/<name> && pdflatex results.tex && pdflatex results.tex
```

Clean up aux files (`.aux`, `.log`, `.out`) after successful compilation. Open the PDF for the user:

```bash
open experiments/<name>/results.pdf
```

---

## Phase 6: Report to user

After the PDF is generated, print a concise summary to the terminal:

1. **One-line verdict:** "Interesting finding: [X]" or "Null result: [X]" or "Mixed: [X]"
2. **Key number:** The single most important statistic
3. **Next step:** The recommended follow-up experiment (from Section 6 of the memo)
4. **File locations:** Path to the PDF, data CSV, and any figures

---

## Data pipeline details

### Directory structure

```
experiments/<experiment>/
  results.tex                         # LaTeX source
  results.pdf                         # Compiled PDF
  data/data.csv                       # Extracted structured data
  plots/results_*.pdf                 # Figures
```

Create directories if needed: `mkdir -p experiments/<name>/{plots,data}`

### Python execution environment

Use the project's venv for all Python scripts:

```bash
source venv/bin/activate
python3 script.py
```

For statistics, prefer `scipy.stats` (already available) or `statsmodels` if needed. For plots, use `matplotlib`. Install missing packages into the venv if needed.

### Transcript parsing patterns

**Extracting deal price from bargaining transcripts:**
Look for "GAME OVER" box → parse "Final Earnings:" lines. Also look for "Deal at $X" or "agreed price" in the message history.

**Extracting contributions from public goods transcripts:**
Look for round result blocks (━━━ delimited) → parse "You contributed: $X | AI contributed: $Y" lines.

**Extracting conditions:**
Always use the `conditions` dict from the transcript JSON — never parse conditions from the message text.

**Handling broken transcripts:**
If a transcript has `overall_passed: false` in its checker result, flag it but still include it in the data (with an `excluded` column). Report the exclusion rate. If >30% of transcripts fail the checker, flag this as a game design issue that needs `/improve` before re-running.

---

## Phase 6b: Update the experiment manifest

If a manifest exists (`experiments/<experiment>/manifest.toml`), append the results artifact path to the `[artifacts]` section:

```toml
[artifacts]
hypothesis_memo = "experiments/<name>/hypothesis.md"
design_memo = "experiments/<name>/design.md"
results_memo = "experiments/<name>/results.pdf"    # ← added by /analyze-results
data_csv = "experiments/<name>/data/data.csv"      # ← added by /analyze-results
```

This keeps the manifest as a single index of all experiment artifacts for `/research-loop` and future iterations.

---

## Rules

1. **Run to completion.** Never ask the user to choose between analysis approaches. Pick the most appropriate one and execute it.
2. **Data first.** Always extract and save the CSV before writing the memo. The memo should reference the data, not the other way around.
3. **Figures are required.** At minimum, generate Figure 1 (main outcome by condition). Skip Figure 2/3 only if genuinely not applicable.
4. **Honest evaluation.** The Evaluation section must explicitly state whether the finding is interesting. Do not hedge with "further research is needed" without saying what specifically.
5. **Actionable next steps.** The Next Experiment section must name a specific hypothesis, game, or command to run. Not "we could explore..." but "Run `/hypothesize [X]`."
6. **Match existing style.** Follow the LaTeX conventions from existing memos in `experiments/` (same packages, same section styling, same figure caption format).
7. **No fake data.** Never fabricate statistics. If the sample is too small for inference, say so. Report descriptive statistics even if N is too small for p-values.
8. **Clean up.** Remove LaTeX aux files after compilation. Remove temporary Python scripts after they've run successfully.
9. **Manifest is source of truth.** If a manifest exists, use it for hypothesis, predictions, conditions, and primary outcome. Do not reconstruct these from LaTeX memos when the manifest is available.
