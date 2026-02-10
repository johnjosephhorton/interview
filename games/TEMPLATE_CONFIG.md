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
opening_max_tokens = 600
```

## Fields

### name
Display name shown in the CLI and API.

### description
Short description shown when listing games.

### [canned]

**opening_instruction** — Injected as the first user message to kick off the game. The checker's `instructions_delivered` criterion verifies the opening message against this text, so be specific about which mechanics to explain. Must include:
- Instruction to explain the rules clearly for someone with no prior knowledge
- What specific information to cover (actions, payoffs, roles, round count)
- Any special mechanics that must be explained (e.g., "both players lose their investment", "choices are simultaneous", "contributions are multiplied by 1.5x")
- The exact prompt for Round 1 (including any game-specific values like the AI's opening offer)
- `Do NOT ask if the human is ready. Do NOT add any preamble before the game. Your first message IS the game start.`

**Example (good):**
```toml
opening_instruction = """Explain the game rules clearly so someone with no prior knowledge could understand. Include: what the game is, how all-pay contests work (both players spend their effort regardless of who wins), the prize amount, the number of rounds, and how the winner is determined.
Starting scoreboard (Human: $0 | AI: $0).
"Round 1 of 3: The prize is $10.00. How much do you want to invest? (Enter any amount from $0.00 to $10.00.)"

Do NOT ask if the human is ready. Do NOT add any preamble before the game. Your first message IS the game start."""
```

**WARNING:** Vague instructions like "Explain the rules briefly (5-6 sentences)" do not tell the LLM which mechanics to cover, and the checker will flag missing details. Always list the specific items to explain.

**LESSON LEARNED:** If the opening instruction is too vague ("explain the rules and start"), the LLM will ask "Are you ready?" or add unnecessary preamble. Be explicit about what the first message should contain and end with.

**last_question** — Canned text for the final round prompt (used by the `last_question` message type).

**end_of_session** — Canned text returned after the game ends (used by the `end_of_interview` message type).

### [settings]

**opening_max_tokens** — Token limit for the opening message. Should be generous enough for a full rules explanation + Round 1 prompt. Typical range: 500–800. The default for subsequent messages is 200 (set in AgentConfig).
