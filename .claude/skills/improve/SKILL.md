---
name: improve
description: Diagnose and fix game failures found by the checker, extract lessons into global templates, and scan other games for the same gaps
argument-hint: "[game-name]"
---

# /improve — Diagnose, fix, generalize, propagate

**Meta-goal:** Every game should work perfectly out of the box. When a bug is found in one game, the fix must flow back into the templates so that *new games created from the templates never have this bug*. The cycle is: detect → diagnose → fix game → update template → scan all games → fix at-risk games. The templates are the source of truth — if a new game can be built from the templates and pass all checker criteria on the first run, the system is working.

Fix game failures found by the checker, extract lessons into global templates, and scan other games for the same gaps.

## Usage

- `/improve contest` — Fix a specific game based on its checker failures
- `/improve` — Scan all games, build a cross-game failure matrix, fix systemic issues

---

## Workflow: Single game (`/improve <game>`)

### Step 1: Read checker failures

1. Glob `transcripts/<game>/*_check.json` to find all checker results
2. Read the **most recent** `_check.json` file (sorted by filename = timestamp)
3. Extract every criterion where `"passed": false` — note the criterion name and explanation
4. If all criteria passed, report "All checks passing for <game>" and stop

### Step 2: Read game files

Read all three game files:
- `games/<game>/manager.md`
- `games/<game>/player.md`
- `games/<game>/config.toml`

### Step 3: Read global references

Read in parallel:
- `games/TEMPLATE_MANAGER.md`
- `games/TEMPLATE_PLAYER.md`
- `games/TEMPLATE_CONFIG.md`
- `games/DESIGN_NOTES.md`

### Step 4: Diagnose root causes

For each failing criterion, determine the root cause by mapping it to a specific section of the game files:

| Criterion | Likely location |
|-----------|----------------|
| `arithmetic_correctness` | Payout Logic in manager.md and/or player.md |
| `running_total_consistency` | State Tracking in manager.md |
| `input_validation` | Input Validation in manager.md |
| `rule_adherence` | Game Parameters in manager.md, Game Rules in player.md |
| `ai_decision_quality` | Goal in player.md |
| `information_leakage` | Message Flow in manager.md, simultaneous-choice handling |
| `manipulation_resistance` | Manipulation Resistance sections (usually boilerplate) |
| `proper_termination` | End of Game in manager.md, `opening_max_tokens` in config.toml |
| `instructions_delivered` | `opening_instruction` in config.toml, Message Flow first-message section in manager.md |

Present the diagnosis to the user as a table:

```
Failing criterion       | Root cause                              | File to fix
------------------------|----------------------------------------|------------------
proper_termination      | End-of-game box truncated by max_tokens | manager.md / config.toml
```

### Step 5: Fix the game

Edit the game files to address each root cause. Follow these rules:
- **Minimal edits** — only change what's needed to fix the failure
- **Match existing style** — follow the patterns already in the file
- **Preserve boilerplate** — never modify [BOILERPLATE] sections
- **Show diffs** — use the Edit tool so the user sees exactly what changed

Common fixes by criterion:
- `proper_termination`: Check `max_tokens` in config.toml (should be ≥400 for the final round result + GAME OVER box). Check that Message Flow has explicit FINAL ROUND instructions to skip the scoreboard and stay compact. Check if the End of Game section in manager.md matches the boilerplate exactly.
- `instructions_delivered`: Ensure `opening_instruction` in config.toml lists every mechanic explicitly. Check that Message Flow's "YOUR VERY FIRST MESSAGE" section references the opening instruction.
- `arithmetic_correctness`: Add/fix worked examples in Payout Logic. Ensure manager.md and player.md use identical formulas.
- `ai_decision_quality`: Check that Goal in player.md has a clear earnings-maximization objective, payoff formula reminder, reasoning instruction, and hard guardrails (logical bounds, not strategy thresholds).
- `input_validation`: Ensure every valid input type has an explicit handler in Message Flow.

### Step 6: Check templates for gaps

For each root cause identified in Step 4, ask:
> "Does the template already warn about this? Would a developer following the template have avoided this bug?"

If the template is **missing guidance** that would have prevented the issue:
1. Add a warning, lesson, or checklist item to the relevant `TEMPLATE_*.md`
2. Add a new entry to `games/DESIGN_NOTES.md` following the existing format:

```markdown
### <Short title>
**Game:** <game_name>
**Symptom:** <what went wrong>
**Root cause:** <why>
**Fix:** <what was changed>
**Rule:** <general rule for all games>
```

If the template **already covers it**, note: "Template already warns about this — the game just didn't follow it."

### Step 7: Scan other games

For each root cause, scan the other 7 games for the same vulnerability:
1. Read the relevant section of each game's files
2. Flag any game that has the same gap
3. Present a summary:

```
Vulnerability: End-of-game box may be truncated
  contest     — FIXED (this session)
  auction     — OK (opening_max_tokens = 600)
  bargainer   — AT RISK (opening_max_tokens = 400, box needs ~300)
  ...
```

Ask the user: "Want me to fix the at-risk games too?"

---

## Workflow: All games (`/improve` with no argument)

### Step 1: Scan all checker results

1. Glob `transcripts/*/` to find all game directories with transcripts
2. For each directory, find the most recent `*_check.json`
3. Build a cross-game matrix:

```
                 arith  totals  input  rules  decision  leakage  manip  termination  instructions
bargainer        PASS   PASS    PASS   PASS   PASS      PASS     PASS   PASS         PASS
pd_rep           PASS   PASS    PASS   PASS   PASS      PASS     PASS   PASS         --
contest          PASS   PASS    PASS   PASS   PASS      PASS     PASS   FAIL         --
auction          --     --      --     --     --        --       --     --           --
...
```

Legend: PASS = passed, FAIL = failed, -- = not tested

### Step 2: Identify patterns

Categorize failures:
- **Systemic** — same criterion failing in 2+ games (template gap)
- **Game-specific** — criterion failing in only 1 game (that game's prompt issue)
- **Untested** — games with no transcripts at all (flag for the user)

### Step 3: Fix systemic issues first

For systemic failures (same criterion failing across multiple games):
1. Diagnose the common root cause
2. Update the relevant `TEMPLATE_*.md` with new guidance
3. Add a `DESIGN_NOTES.md` entry
4. Fix each affected game

### Step 4: Fix game-specific issues

For each game-specific failure, run the single-game workflow (Steps 4-5 from above).

### Step 5: Report

Present a final summary:

```
## /improve summary

Games fixed: contest (proper_termination), ...
Template updates: TEMPLATE_MANAGER.md (added token budget guidance)
Design notes added: 1 new entry
Untested games: auction, trust, public_goods
At-risk games: bargainer (same pattern as contest fix)

Next steps:
- Run checker on untested games: interview simulate --game auction && interview check auction
- Review at-risk games flagged above
```

---

## Important rules

- **Prefer prompt/config fixes.** Most issues are fixable in game prompts (`.md`), configs (`.toml`), templates, and design notes. Only modify Python code when a structural limitation (e.g., missing config plumbing) blocks the fix — and ask the user first.
- **Always show the user what you're about to change** before editing. Present the diagnosis and proposed fix, then edit.
- **One fix at a time.** Don't batch multiple unrelated fixes into a single edit — the user should see each change clearly.
- **Preserve the DESIGN_NOTES.md format.** New entries go under the most relevant existing section header, or create a new `##` section if none fits.
- **Template updates are conservative.** Only add guidance to templates when the lesson is general enough to apply to future games. A one-off bug in a single game's payout formula doesn't need a template change.
