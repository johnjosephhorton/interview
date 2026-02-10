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

**opening_instruction** — Injected as the first user message to kick off the game. Must include:
- Instruction to explain the rules clearly for someone with no prior knowledge
- What specific information to cover (actions, payoffs, roles, round count)
- The exact prompt for Round 1 (including any game-specific values like the AI's opening offer)
- `Do NOT ask if the human is ready. Do NOT add any preamble before the game. Your first message IS the game start.`

**LESSON LEARNED:** If the opening instruction is too vague ("explain the rules and start"), the LLM will ask "Are you ready?" or add unnecessary preamble. Be explicit about what the first message should contain and end with.

**last_question** — Canned text for the final round prompt (used by the `last_question` message type).

**end_of_session** — Canned text returned after the game ends (used by the `end_of_interview` message type).

### [settings]

**opening_max_tokens** — Token limit for the opening message. Should be generous enough for a full rules explanation + Round 1 prompt. Typical range: 500–800. The default for subsequent messages is 200 (set in AgentConfig).
