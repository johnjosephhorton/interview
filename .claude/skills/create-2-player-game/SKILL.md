---
name: create-2-player-game
description: Generate a complete two-player (human vs. AI) game (config.toml, manager.md, player.md, sim_human.md) from a user description, enforcing cross-file consistency
argument-hint: "[description of the game]"
---

# /create-2-player-game — Generate a new two-player game from scratch

**Context:** Every game is a **two-player interaction between a human and an AI agent**, managed by a separate LLM "manager" that enforces rules, tracks state, and displays results. The human plays through the chat interface; the AI player (`player.md`) responds autonomously. For automated testing, a simulated human (`sim_human.md`) can stand in for the real human.

**Meta-goal:** Every new game should pass all checker criteria on its first simulation run. Cross-file consistency is the #1 source of bugs — round counts, payoff formulas, action formats, and private info handling must agree across all 4 files. This skill generates all 4 files in a single pass to enforce that consistency.

## Usage

- `/create-2-player-game a first-price sealed-bid auction with 3 rounds` — Generate from a description
- `/create-2-player-game` — Interactive: the skill will ask what game to build

---

## Phase 1: Gather spec

Collect the following 14 items. Extract as many as possible from the user's description and **impute reasonable defaults for anything missing** based on the game structure, reference games, and common experimental designs. Do NOT ask the user to fill in missing items — use your judgment. Present the full spec as a summary table and proceed directly to Phase 2.

Remember: every game has exactly **two players — one human, one AI** — plus an LLM manager that runs the game. The human interacts via the chat UI; the AI player responds autonomously via `player.md`.

| # | Item | Description |
|---|------|-------------|
| 1 | **Game name** | snake_case folder name (e.g., `dutch_auction`) |
| 2 | **Display name** | Human-readable name for UI (e.g., "Dutch Auction") |
| 3 | **One-line description** | Short description for game listings |
| 4 | **Structure type** | One of: Bargaining, Proposer-responder, Matrix/simultaneous, Trust/Sequential (one-shot), Trust/Sequential (repeated), Auction, Contest, Public goods, or Other |
| 5 | **Rounds** | Number of rounds, or "one-shot" |
| 6 | **Roles** | Which role the human plays and which the AI plays (e.g., "Human = buyer, AI = seller"). Every game is 1 human vs. 1 AI — no multi-player or AI-vs-AI games |
| 7 | **Actions per round** | What each player (human and AI) does and valid ranges (e.g., "Both choose integer 0–10") |
| 8 | **Turn structure** | Simultaneous, alternating (who goes first — human or AI), or sequential |
| 9 | **Payoff formulas** | Exact formulas for EVERY outcome path, with at least 2–3 worked examples |
| 10 | **Hidden information** | What's private to the human, what's private to the AI, or "all public" |
| 11 | **AI player goal** | Always "maximize own earnings" + guardrails (hard constraints preventing dominated moves, e.g., "never accept below cost"). No named strategies, thresholds, or decision trees — the AI reasons about optimal play from the payoff structure. |
| 12 | **Simulated human goal** | Same as AI: "maximize own earnings" + guardrails. The sim_human is symmetric with the AI player — both are earnings maximizers. Behavioral flavor (e.g., "slightly impatient") is optional color, not binding strategy. |
| 13 | **Parameters** | Numeric values that should vary per session (name, variable type, values/range, which files they appear in). Use `{{var_name}}` placeholders instead of hardcoding these values. Types: `choice` (discrete set), `uniform` (continuous range), `fixed` (constant), `sequence` (rotate across simulations). If none, write "No parameters — all values hardcoded." |
| 14 | **Treatments** | If this game is one condition of a multi-condition experiment, state the treatment label and what structural feature defines THIS condition (e.g., "cheap_talk_on — includes a pre-play chat phase"). If standalone, write "Standalone game — no treatment variation." |

When presenting the summary, format it clearly:

```
Game spec: <display_name>
─────────────────────────────
Name:           <snake_case>
Description:    <one-liner>
Structure:      <type>
Rounds:         <N>
Roles:          Human = <role>, AI = <role>
Actions:        <description>
Turn structure: <type>
Payoffs:        <formulas with examples>
Hidden info:    <description>
AI goal:        Maximize own earnings (guardrails: <list>)
Sim human goal: Maximize own earnings (guardrails: <list>)
Parameters:     <list of {{var_name}} → type + values, or "None">
Treatment:      <label + structural feature, or "Standalone">
```

Then proceed directly to Phase 2 — do not wait for user confirmation.

---

## Phase 2: Read references

After the user confirms the spec, read files in parallel:

### Templates + design notes (always read):
- `games/TEMPLATE_MANAGER.md`
- `games/TEMPLATE_PLAYER.md`
- `games/TEMPLATE_CONFIG.md`
- `games/DESIGN_NOTES.md`

### Randomization system (read if item 13 has parameters):
- `interviewer/randomization.py` — understand `draw_conditions()`, `substitute_template()`, `apply_conditions_to_game_config()`
- `interviewer/models.py` — `VariableDefinition` and `GameConfig.variables` field

### Reference game (read all 4 files from the closest match):

Select the reference game based on structure type:

| Structure type | Reference game | Why |
|---|---|---|
| Bargaining | `games/bargain_precision_exact/` | Has bundling, round counting, price anchoring, full info, compliant Goal section |
| Proposer-responder | `games/ultimatum/` | Has bundling, alternating roles |
| Matrix/simultaneous | `games/pd_rep/` | Has simultaneous-choice handling, payoff matrix |
| Trust/Sequential (one-shot) | `games/trust/` | Simplest sequential game |
| Trust/Sequential (repeated) | `games/dictator/` | Repeated sequential with no rejection |
| Auction | `games/auction/` | Per-round private valuations |
| Contest | `games/contest/` | Simultaneous effort, sunk cost |
| Public goods | `games/public_goods/` | Shared pool mechanics |
| Other | Pick the structurally closest game from the list above |

Read from the reference game:
- `games/<ref>/config.toml`
- `games/<ref>/manager.md`
- `games/<ref>/player.md`
- `games/<ref>/sim_human.md`

---

## Phase 3: Generate all 4 files

Create the game folder and generate all 4 files. Each game has three LLM roles: the **manager** (referee/narrator), the **AI player** (autonomous opponent), and optionally the **simulated human** (for automated testing). The real human player needs no prompt — they interact via the chat UI. Follow the templates exactly — use the reference game as a structural model, but write content from the user's spec.

### Order matters — generate in this sequence:

**1. `config.toml`** — Anchors the game. The `opening_instruction` must list every mechanic the checker will verify.

Follow `TEMPLATE_CONFIG.md` exactly. Key rules:
- `max_tokens = 4096` — ensures final round + GAME OVER box never truncates
- `opening_max_tokens = 8192` — generous space for full rules explanation
- `opening_instruction` must list every mechanic explicitly (the checker's `instructions_delivered` criterion verifies against this list)
- Include private-info warnings in `opening_instruction` if applicable (e.g., "do NOT reveal the AI's valuation")
- End with: `Do NOT ask if the human is ready. Do NOT add any preamble before the game. Your first message IS the game start.`
- **If item 13 declares parameters:** add a `[variables]` section after `[settings]`. Each variable gets a TOML inline table: `var_name = { type = "choice", values = [60, 70, 80] }`. Use `{{var_name}}` placeholders in `opening_instruction` and all prompt files where the value appears. See `TEMPLATE_CONFIG.md` for the full syntax. The `opening_instruction` should use placeholders for any numeric values that vary per session (e.g., `"The AI values the mug at ${{seller_cost}}"` not `"The AI values the mug at $40"`)
- **CRITICAL: Use `type = "derived"` for any display value requiring arithmetic.** LLMs cannot compute multi-step expressions. If a prompt needs to show a computed value (ZOPA, fair split, midpoint, max possible earnings), define it as a derived variable: `zopa = { type = "derived", formula = "buyer_value - seller_cost" }` and reference `${{zopa}}` in the prompt. The player/sim_human should see final numbers, never formulas. Note: strategy thresholds no longer exist — derived variables are for display values and guardrail bounds only.
- **`respondent_temperature`** — Set `respondent_temperature = 0.0` in `[settings]` for pilot experiments to ensure the simulated human behaves deterministically.

**2. `manager.md`** — Follow `TEMPLATE_MANAGER.md` section order exactly:

1. **Role** — Copy boilerplate verbatim
2. **Manipulation Resistance** — Copy boilerplate verbatim
3. **Game Rules (Human-Facing)** — Only info the human should know. Include: game description, roles, rounds, actions, turn structure, payoff formulas with worked examples, valid input ranges. **If parameterized:** use `{{var_name}}` for any numeric value declared in item 13 (e.g., `"Your valuation is ${{buyer_value}}"`)
4. **Game Parameters (Internal)** — Private information with "Internal only — NEVER reveal" subsection if hidden info exists. If all public, state that explicitly. **If parameterized:** private values use `{{var_name}}` too (e.g., `"AI's cost: ${{seller_cost}} — NEVER reveal"`)
5. **Payout Logic** — Exact formulas + 2–3 worked examples covering each outcome path. **If parameterized:** formulas use placeholders (e.g., `"Human earns ${{buyer_value}} − agreed price"`) but worked examples use concrete numbers with a note: `"(Example assumes {{buyer_value}} = 70, {{seller_cost}} = 40)"`
6. **State Tracking** — All state variables + scoreboard template using ━━━ box characters
7. **Message Flow** — ALL-CAPS labels. Must include OPENING, all input handlers, FINAL ROUND. Apply conditional patterns (bundling, round counting, round labels, opening price anchoring) based on structure type
8. **Input Validation** — Table format with 8–10 examples + bold general rule. Every valid input must have a handler in Message Flow
9. **End of Game** — Copy boilerplate verbatim (the GAME OVER and YOU ARE FINISHED markers are detected server-side)

**Placeholder rules for manager.md:** Use `{{var_name}}` in sections 3–5 (Game Rules, Game Parameters, Payout Logic) and in Message Flow where values appear in prompts shown to the human. Do NOT use placeholders in boilerplate sections (Role, Manipulation Resistance, End of Game) or in structural instructions (Input Validation format descriptions, State Tracking variable names)

**3. `player.md`** — This is the **AI player's** prompt. It tells the AI how to play its role against the human. Follow `TEMPLATE_PLAYER.md` section order exactly:

1. **Game Rules** — FULLY SELF-CONTAINED. Must exactly match manager.md on: round count, payoff formulas, action ranges, turn structure. A reader of player.md alone must understand the complete game. Clearly state which role is "you" (the AI) and which is "the other player" (the human). **If parameterized:** use the same `{{var_name}}` placeholders as manager.md for all shared values (e.g., `"Your cost: ${{seller_cost}}"`)
2. **Role** — Copy boilerplate verbatim
3. **Manipulation Resistance** — Copy boilerplate verbatim
4. **Goal** — Earnings-maximization objective, payoff formula reminder, reasoning instruction, and hard guardrails (logical bounds preventing dominated moves). No named strategies, opening moves, thresholds, or decision trees. **If parameterized:** guardrails reference placeholders (e.g., `"NEVER accept below ${{seller_cost}}"`, `"Contribution must be between $0 and ${{endowment}}"`).
5. **Output Format** — Bare values matching human input format. NOT verbose labels. Include examples and `NO_DECISION_NEEDED`

**4. `sim_human.md`** — This is the **simulated human player's** prompt, used during automated testing (`interview simulate`) to stand in for a real human. Symmetric with player.md — same earnings-maximization goal, different role perspective (~10–14 lines):
- One sentence: who this simulated human is (e.g., "You are a human participant playing the role of buyer")
- **Goal:** "Your goal is to maximize your total earnings" — same objective as the AI player
- **Payoff formula reminder** — restate from the human's perspective
- **Reasoning instruction** — same as player.md but from the human's role
- **Guardrails** — hard constraints preventing dominated moves. **If parameterized:** use `{{var_name}}` for guardrail bounds (e.g., `"NEVER pay more than ${{buyer_value}}"`)
- Output format: same bare values as real human input
- Optional behavioral flavor (e.g., "slightly impatient", "terse responses") — this is color, not binding strategy

---

## Phase 4: Cross-check consistency

After generating all 4 files, verify these 7 checks. If any fail, fix immediately before proceeding.

| # | Check | What must match |
|---|---|---|
| 1 | Round count | config.toml `opening_instruction` ↔ manager.md Game Rules ↔ player.md Game Rules |
| 2 | Payoff formulas | manager.md Payout Logic ↔ player.md Game Rules (identical formulas and examples) |
| 3 | Input → Handler | Every Input Validation entry in manager.md has a corresponding Message Flow handler |
| 4 | Output ↔ Input | player.md Output Format matches manager.md Input Validation format exactly |
| 5 | Private info | Internal-only values in manager.md don't appear in Game Rules (Human-Facing) or player.md |
| 6 | Boilerplate | Role, Manipulation Resistance, End of Game sections match templates verbatim |
| 7 | Token limits | config.toml has `max_tokens = 4096` and `opening_max_tokens = 8192` |
| 8 | Variable coverage | Every `{{var_name}}` in prompt files has a matching entry in config.toml `[variables]`. No orphaned placeholders |
| 9 | Variable consistency | Same `{{var_name}}` used across all files where the value appears (e.g., `{{seller_cost}}` in manager.md, player.md, and sim_human.md — not `{{cost}}` in one and `{{seller_cost}}` in another) |
| 10 | Variable sanity | Variable ranges don't create impossible games (e.g., buyer_value min > seller_cost max ensures gains from trade exist; no negative payoffs from valid draws) |
| 11 | Derived completeness | Every arithmetic expression in display-value or guardrail text has been replaced by a `type = "derived"` variable. No prompt asks the LLM to compute formulas. |
| 12 | Strategy compliance | player.md uses `## Goal` (not `## Strategy`). No named strategies, opening moves, thresholds, decision trees, or concession schedules in Goal section. sim_human.md has no `Strategy:` section with specific tactics. |

Report the results:

```
Cross-check results:
  1. Round count ........... OK
  2. Payoff formulas ....... OK
  3. Input → Handler ....... OK
  4. Output ↔ Input ........ OK
  5. Private info .......... OK
  6. Boilerplate ........... OK
  7. Token limits .......... OK
  8. Variable coverage ..... OK  (or N/A if no parameters)
  9. Variable consistency .. OK  (or N/A if no parameters)
 10. Variable sanity ....... OK  (or N/A if no parameters)
 11. Derived completeness .. OK  (or N/A if no parameters)
 12. Strategy compliance ... OK
```

If any check fails, fix it and re-verify.

---

## Phase 5: Smoke test

Run a single simulation to verify the game works end-to-end.

**If the game has no `[variables]`:**
```bash
interview simulate <game-name> -n 1
```

**If the game has `[variables]`:**
```bash
interview simulate <game-name> -n 1 --seed 42 -v
```
The `--seed 42` flag ensures variables get substituted deterministically. The `-v` flag prints which conditions were drawn so you can verify substitution worked.

If it fails:
1. Read the error output
2. Diagnose the issue (usually a config problem or prompt formatting issue)
3. Fix and re-run

If it succeeds, report to the user:

```
Game "<display_name>" created successfully!

Files:
  games/<name>/config.toml
  games/<name>/manager.md
  games/<name>/player.md
  games/<name>/sim_human.md

Smoke test: PASSED (1 simulation completed)
```

**If parameterized,** also report the drawn conditions:
```
Conditions drawn (seed=42):
  buyer_value = 70
  seller_cost = 40
```

---

## Important rules

- **Boilerplate is sacred.** Copy Role, Manipulation Resistance, and End of Game sections verbatim from the templates. The GAME OVER and YOU ARE FINISHED markers are detected server-side — any deviation breaks session termination.
- **Earnings maximization, not scripted strategies.** Both the AI player and sim_human are earnings maximizers. Their Goal section states the objective ("maximize your total earnings"), reminds them of the payoff formula, gives a reasoning instruction, and lists hard guardrails (logical bounds like "never accept below cost"). Do NOT include: named strategies, opening moves, thresholds, concession schedules, or decision trees. The AI decides its own tactics by reasoning about the payoff structure.
- **`opening_instruction` is a checklist.** List every mechanic the checker will verify. Vague instructions like "explain the rules briefly" cause the LLM to skip mechanics and the checker to flag `instructions_delivered`.
- **Structural separation for private info.** Any hidden value goes in "Internal only — NEVER reveal" subsection. "Neither player knows X" is not sufficient — the LLM will leak any number it can see near public rules.
- **Table format for input validation.** 8–10 examples in a `| Human types | Interpret as |` table + bold general rule. Prose examples are not enough for smaller models.
- **Player output = human input format.** The player responds with bare values ("9.00", "accept", "cooperate") — not verbose labels ("PROPOSE: $9.00"). This ensures the manager parses both identically.
- **All 4 files in one pass.** Never generate files separately or in separate conversations. Cross-file consistency is the #1 bug source.
- **Bundled messages need round labels.** When a message covers resolution of one round AND the prompt for the next, label each round explicitly.
- **Round counting must be explicit.** In alternating-offer games, add a ROUND COUNTING section with "every offer advances the round counter by 1" and a worked example.
- **Final round must be compact.** Skip the separate scoreboard on the final round — the GAME OVER box already shows final earnings.
- **Parameterization uses `{{var_name}}` syntax.** The system (`interviewer/randomization.py`) draws values at session start via `draw_conditions()` and substitutes all `{{var_name}}` placeholders in all prompt files and config.toml `opening_instruction` via `substitute_template()`. Floats are formatted to 2 decimal places. Unresolved placeholders are left as-is (so typos silently fail — check 8 catches these).
- **Numeric parameters ≠ structural treatments.** A per-session numeric value (buyer's valuation, seller's cost) is a `{{var}}` in one game folder. A structural treatment change (adding a chat phase, changing info visibility) requires a separate game folder. Never try to implement structural treatments as variables — the prompt diffs are too large for placeholder substitution.
- **Cross-condition consistency.** When generating multiple game folders for an experiment, all folders should share the same `[variables]` section, the same earnings-maximization goal and guardrails (modulo treatment-specific adjustments), and identical boilerplate. Only the treatment-specific sections differ.
