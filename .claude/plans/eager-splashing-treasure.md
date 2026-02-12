# Plan: `/hypothesize` Skill

## Context

The user is an academic researcher running behavioral economics games (bargaining, auctions, trust, etc.) with LLM agents. They want a skill that generates causal hypotheses formalized as **Pearlean DAGs** — testable exclusively through the game system. Currently, going from "I wonder about X" to a concrete experimental design requires manually reasoning about what games exist, what parameters can be varied, and what outcomes are measurable. This skill automates that.

## Design Decisions

### One skill, 3 input modes (like `/improve`)
- `/hypothesize` — open exploration, survey full game taxonomy for novel comparisons
- `/hypothesize fairness` — topic-guided, narrow to relevant games/variables
- `/hypothesize "Does cheap talk reduce anchoring?"` — formalize a specific question as a DAG

### 1 deep hypothesis per invocation
Go deep on one hypothesis (DAG + operationalization + full test plan) rather than generating a shallow list. The user can re-invoke for alternatives.

### Read game landscape at runtime
Glob `games/*/config.toml` + read `games/DESIGN_NOTES.md` taxonomy. This keeps the skill current as new games are added via `/create-2-player-game`.

### DOT/Graphviz output, inline
Output the DAG as a fenced `dot` code block. No file writes — it's a communication artifact, not a functional one. User can copy and render.

## File to Create

**`.claude/skills/hypothesize/SKILL.md`** (~200 lines)

Follows the same pattern as existing skills:
- YAML frontmatter: `name`, `description`, `argument-hint`
- 6-phase workflow
- "Important rules" section
- Runtime reads, no embedded content

## Workflow (6 phases)

### Phase 1 — Read the game landscape
Read in parallel:
1. All `games/*/config.toml` — discover available games and parameters
2. `games/DESIGN_NOTES.md` — game structure taxonomy + known interaction effects
3. For each game: skim `manager.md` (Game Rules, Payout Logic) and `player.md` (Strategy) to understand what's currently configured

Build a mental inventory of: what structures exist, what parameters vary across same-type games, what's held constant (and could be varied).

### Phase 2 — Determine mode and scope

| Argument | Mode | Scope |
|----------|------|-------|
| (none) | Open exploration | Full taxonomy; use novelty heuristics |
| Word/phrase (no `?`) | Topic-guided | Filter to relevant games/variables via topic map |
| Contains `?` or quotes | Question formalization | Parse the causal claim, map to DAG nodes |

**Topic-to-variable mapping** (embedded in skill):

| Topic | Relevant games | Key variables |
|---|---|---|
| fairness, equity | ultimatum, dictator, bargainer | offer size, rejection rate, equal-split deviation |
| information, asymmetry | bargain_imperfect, bargain_cheap_talk, auction | info structure, valuation spread, deal price |
| cooperation, trust | pd_rep, trust, public_goods | cooperation rate, contribution, reciprocity |
| competition, contests | contest, auction | investment/bid level, overbidding, efficiency |
| communication, cheap talk | bargain_cheap_talk vs bargainer | communication condition, deal price, agreement rate |
| anchoring, first-mover | bargainer, bargain_imperfect, ultimatum | first offer, concession rate, deal price |
| repeated, learning | pd_rep, dictator, public_goods, ultimatum | round number, strategy shift, cooperation trend |

### Phase 3 — Generate the hypothesis

**Novelty heuristics** (priority order, for open exploration):

1. **Cross-structure comparison** — Compare across game types (e.g., does the trust multiplier serve the same function as cheap talk?). Most novel.
2. **Missing factorial cell** — Parameter combinations that exist for one game but not another. E.g., trust game exists without cheap talk; the gap suggests a hypothesis.
3. **Mechanism isolation** — Two variants differing on exactly one parameter → propose a mediating mechanism, not just a direct effect.
4. **Behavioral anomaly** — When will LLM agents deviate from Nash predictions? Fairness norms, anchoring biases, reciprocity in LLMs.
5. **Interaction effects** — Effect of X depends on Y (moderation).

**Quality checks** before finalizing:
- Falsifiable? (DAG implies testable conditional independencies)
- Non-trivial? (Not a textbook result restatement)
- Estimable with reasonable N? (Flag if >1000 sims needed)
- Every node measurable? (Game parameter or transcript metric — no external data)

Output: one sentence in the form "[Treatment] causes [Outcome] through [Mechanism], and this effect is [moderated by X]."

### Phase 4 — Construct the Pearlean DAG

DOT/Graphviz with typed nodes:

| Node type | Shape | Color | Meaning |
|-----------|-------|-------|---------|
| Treatment | box | `#4A90D9` blue | Manipulated via game design |
| Mediator | ellipse | `#F5A623` orange | Intermediate mechanism from transcripts |
| Moderator | diamond | `#7ED321` green | Conditions path strength |
| Outcome | box (double border) | `#D0021B` red | Primary DV |

**Structural rules:** 4–8 nodes, at least 1 treatment + 1 mediator + 1 outcome, no cycles, at least one indirect path (T → M → O).

Edge conventions: solid = direct causal, dashed = moderation. Edge labels = brief mechanism description.

### Phase 5 — Operationalization table

Markdown table, one row per DAG node:

| DAG Node | Variable | Game Parameter / Transcript Metric | How to Measure | Values/Units |
|----------|----------|-----------------------------------|----------------|-------------|

Rules: every DAG node gets a row. "How to Measure" must be concrete enough for a script. Flag nodes requiring new game variants.

### Phase 6 — Full test plan

1. **Treatment arms table** — each condition, which game, key parameters, exists/needs-creation status
2. **Outcome measures** — primary, secondary, mediator variables with extraction methods
3. **Sample size** — per-arm N (15 large / 30 medium / 50 small effect)
4. **CLI commands** — exact `interview simulate <game> -n <N>` commands
5. **Analysis sketch** — statistical test for each DAG path (t-test for direct, Baron-Kenny for mediation, interaction regression for moderation)

## Important Rules (embedded in skill)

- **Every DAG node must be measurable.** No node without a concrete extraction method from game files or transcripts.
- **Prefer existing games over new games.** Only propose new variants when the parameter variation is genuinely absent. Reference existing games by folder name.
- **One hypothesis per invocation.** Deep > wide.
- **DAG output is inline.** Fenced `dot` code block. No file writes.
- **The test plan must be executable today.** No Python codebase changes, no new CLI commands. Work within `interview simulate`.
- **Acknowledge LLM agent limitations.** Note model/temperature sensitivity. Specify what's held constant.

## Verification

1. Create `.claude/skills/hypothesize/SKILL.md`
2. Test all 3 input modes:
   - `/hypothesize` (open exploration)
   - `/hypothesize fairness` (topic-guided)
   - `/hypothesize "Does cheap talk reduce anchoring?"` (question formalization)
3. Verify each produces: hypothesis statement, DOT DAG, operationalization table, test plan with CLI commands
4. Spot-check that referenced games exist and variable extraction methods are valid
