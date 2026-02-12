# Config Template

Every `config.toml` MUST contain the following fields.

---

```toml
name = "Game Name"
description = "One-line description of the game"

[canned]
opening_instruction = """..."""
last_question = "..."
end_of_session = "..."

[settings]
max_tokens = 400
opening_max_tokens = 600
```

## Fields

### name
Display name shown in the CLI and API.

### description
Short description shown when listing games.

### [canned]

**opening_instruction** — Injected as the first user message to kick off the game. The Game Rules (Human-Facing) section in `manager.md` is the single source of truth for rules; this instruction tells the manager to present those rules and lists the specific items the checker will verify. Must include:
- `Explain the game rules from the Game Rules section` (references the authoritative source)
- A checklist of specific items to cover (the checker's `instructions_delivered` criterion verifies against this list, so be explicit — e.g., "how all-pay contests work (both players spend their effort regardless of who wins)")
- Any private-info warnings (e.g., "do NOT reveal the AI's valuation")
- The exact prompt for Round 1 (including any game-specific values like the AI's opening offer)
- `Do NOT ask if the human is ready. Do NOT add any preamble before the game. Your first message IS the game start.`

**Example (good):**
```toml
opening_instruction = """Explain the game rules from the Game Rules section clearly so someone with no prior knowledge could understand. Include: what the game is, how all-pay contests work (both players spend their effort regardless of who wins), the prize amount ($10.00), the number of rounds (3), how the winner is determined, and how earnings are computed.
Starting scoreboard (Human: $0 | AI: $0).
"Round 1 of 3: The prize is $10.00. How much do you want to invest? (Enter any amount from $0.00 to $10.00.)"

Do NOT ask if the human is ready. Do NOT add any preamble before the game. Your first message IS the game start."""
```

**WARNING:** Vague instructions like "Explain the rules briefly (5-6 sentences)" do not tell the LLM which mechanics to cover, and the checker will flag missing details. Always list the specific items to explain.

**LESSON LEARNED:** If the opening instruction is too vague ("explain the rules and start"), the LLM will ask "Are you ready?" or add unnecessary preamble. Be explicit about what the first message should contain and end with.

**last_question** — Canned text for the final round prompt (used by the `last_question` message type).

**end_of_session** — Canned text returned after the game ends (used by the `end_of_interview` message type).

### [settings]

**max_tokens** — Token limit for non-opening messages (round results, game-over, etc.). Default is 200, but games should set this to 400 to ensure the final round result + GAME OVER box fits without truncation. The GAME OVER box alone is ~130 tokens; add round result overhead and 200 is too tight.

**opening_max_tokens** — Token limit for the opening message. Should be generous enough for a full rules explanation + Round 1 prompt. Typical range: 500–800.

### [variables] (optional)

Numeric parameters that vary per session. Each variable is an inline TOML table. The system draws values at session start (`draw_conditions()`) and substitutes all `{{var_name}}` placeholders in prompt files and `opening_instruction` before the game begins.

**Variable types:**

| Type | Syntax | Behavior |
|------|--------|----------|
| `choice` | `{ type = "choice", values = [60, 70, 80] }` | Randomly pick one value per session |
| `uniform` | `{ type = "uniform", min = 30.0, max = 50.0 }` | Draw from continuous range (formatted to 2 decimal places) |
| `fixed` | `{ type = "fixed", value = 100 }` | Same value every session (useful for constants that might change across experiment conditions) |
| `sequence` | `{ type = "sequence", values = ["A", "B", "C"] }` | Rotate through values across simulations (sim 0→A, sim 1→B, sim 2→C, sim 3→A, ...) |
| `derived` | `{ type = "derived", formula = "cost + 0.7 * (value - cost)", round_to = 1.0 }` | Python expression evaluated after all base variables are drawn. Can reference any base or earlier-derived variable. `round_to` is optional (rounds to nearest multiple). |

**Why `derived`?** LLMs cannot reliably compute multi-step arithmetic. If a prompt needs to display a computed value (ZOPA, fair split, midpoint, maximum possible earnings), the LLM will get the math wrong. Pre-compute the result as a derived variable and inject the final number via `{{var_name}}`. Derived variables are for display values and guardrail bounds — not strategy thresholds (agents are earnings maximizers and choose their own tactics).

**Example:**

```toml
[variables]
buyer_value = { type = "choice", values = [60, 70, 80] }
seller_cost = { type = "choice", values = [30, 40, 50] }
zopa = { type = "derived", formula = "buyer_value - seller_cost" }
fair_split = { type = "derived", formula = "seller_cost + (buyer_value - seller_cost) / 2", round_to = 1.0 }
endowment = { type = "fixed", value = 100 }
```

Then use `{{buyer_value}}`, `{{seller_cost}}`, `{{zopa}}`, `{{fair_split}}`, and `{{endowment}}` in manager.md, player.md, sim_human.md, and `opening_instruction`.

**Note:** Strategy variables (e.g., `opening_price`, `accept_threshold`, `concession_step`) are no longer needed. Agents are earnings maximizers — they choose their own tactics. Only define variables for game parameters (valuations, costs, endowments) and display values (ZOPA, fair split) that appear in prompts.

### [settings] — respondent_temperature (optional)

**respondent_temperature** — Override the sampling temperature for the simulated human (sim_human.md) during `interview simulate`. If set, this overrides the CLI `--temperature` flag for the respondent only (the manager still uses the CLI temperature). Set to `0.0` for deterministic sim_human behavior in pilot experiments.

```toml
[settings]
max_tokens = 4096
opening_max_tokens = 8192
respondent_temperature = 0.0
```

**Rules:**
- Every `{{var_name}}` in any prompt file must have a matching entry here
- Variable names should be descriptive: `buyer_value` not `v1`, `seller_cost` not `c`
- Ensure variable ranges don't create impossible games (e.g., if buyer_value and seller_cost can overlap, some sessions may have no gains from trade — decide if that's intentional)
- Floats are formatted to 2 decimal places during substitution; integers stay as integers
- Unresolved placeholders (typos) are left as-is in the output — the cross-check in Phase 4 catches these

**Running with variables:**
```bash
# Random draw each session
interview simulate <game> -n 50

# Reproducible draws with a seed
interview simulate <game> -n 50 --seed 42

# Full factorial crossing of all choice/sequence variables
interview simulate <game> --design factorial
```
