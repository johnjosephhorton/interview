# Plan: General-Purpose Two-Agent Game Framework

## Context

The user has been building structured economic games (bargaining, ultimatum, prisoner's dilemma) using single mega-prompts that combine game management and AI strategy into one LLM call. This fails because: (1) the LLM leaks private info between roles, (2) one context can't be both a neutral referee and a strategic player, (3) state tracking and math are unreliable in a single prompt.

The fix: separate **Manager** (game flow, display, validation) from **Player** (AI strategy) into two LLM agents with isolated contexts. The framework routes messages between human, manager, and player — game-specific logic lives entirely in the two prompts.

## Architecture

```
Human input → Manager LLM (full game rules, both valuations, display formatting)
                  ↕  [PLAYER_TURN] / [PLAYER_DECISION] protocol
              Player LLM (only its own strategy + offer history — isolated context)
```

Per human turn:
1. Human sends input → Manager processes (validate, update state)
2. If Manager outputs `[PLAYER_TURN]...[/PLAYER_TURN]` → framework extracts, calls Player
3. Player decision fed back as `[PLAYER_DECISION]...[/PLAYER_DECISION]`
4. Manager formats final display → shown to human

## Files to Create (10 new)

### 1. `interviewer/game_models.py` — Pydantic models
- `GameMessage(role: Literal["manager", "human", "player"], text: str, visible: bool = True)`
- `GameTranscript(messages, manager_config, player_config, started_at, ended_at, token counts, llm_calls)`
- Mirrors existing `Message`/`Transcript` but with game roles and visibility flag
- Reuses existing `AgentConfig`, `LLMCallInfo`, `AgentResponse` unchanged

### 2. `interviewer/game_defaults.py` — Constants
- `DEFAULT_GAME_MANAGER_SYSTEM_PROMPT` — generic manager with `[PLAYER_TURN]` protocol instructions
- `DEFAULT_GAME_PLAYER_SYSTEM_PROMPT` — generic strategic player
- `DEFAULT_GAME_MAX_TOKENS = 500` (managers need more space for state display)
- `DEFAULT_GAME_PLAYER_MAX_TOKENS = 100` (player decisions are terse)
- `DEFAULT_GAME_OPENING_INSTRUCTION` — tells manager to start the game immediately

### 3. `interviewer/game.py` — Core framework (3 classes)

**`GameManager`** — mirrors `Interviewer` in `core.py`:
- `__init__(api_key)` — same API key pattern
- `_format_messages(messages: list[GameMessage], config)` — manager→assistant, human+player→user
- `generate_response(messages, config, message_type)` — same async OpenAI call pattern

**`PlayerAgent`** — similar to `SimulatedRespondent`:
- `generate_response(player_messages: list[dict], new_context: str, config)` — accumulates history across turns
- Each call: appends `new_context` as user message, gets response, appends as assistant message
- Player builds strategic memory over the game (e.g., remembers past offers it made)
- Still isolated: only sees what the Manager explicitly passes via `[PLAYER_TURN]` blocks — never the full human-facing conversation

**`GameOrchestrator`** — the new routing layer:
- `__init__(api_key)` — creates GameManager + PlayerAgent internally
- Maintains `player_messages: list[dict]` — the player's accumulated conversation history (system prompt + past PLAYER_TURN/response pairs)
- `process_opening(manager_config, player_config) → (new_messages, llm_calls)`
- `process_human_input(text, existing_messages, manager_config, player_config) → (new_messages, llm_calls)`
- Parses `[PLAYER_TURN]...[/PLAYER_TURN]` via regex
- Feeds player decision back to manager for final formatting
- Internal messages stored with `visible=False` (kept in history for context, hidden from UI)
- Caller owns game message list; orchestrator owns player history (orchestrator is stateful per-session)

### 4. `interviewer/game_logging.py` — Transcript saving
- `save_game_transcript(transcript, path, format)` — mirrors `save_transcript()` in `logging.py`
- JSON and CSV support; CSV adds `visible` column

### 5. `cli/main.py` — Add `game` command
- New `@app.command() def game(...)` following exact `chat` command pattern
- Flags: `--manager-prompt/-M`, `--player-prompt/-P`, `--model/-m`, `--temperature/-t`, `--manager-max-tokens`, `--player-max-tokens`, `--save`
- Async `_game()` function: opening → loop (read input → process_human_input → display visible messages) → save

### 6. `server/game_session.py` — In-memory game sessions
- `GameSession(id, manager_config, player_config, messages: list[GameMessage], status)`
- CRUD functions: `create_game_session`, `get_game_session`, `delete_game_session`
- Stores a `GameOrchestrator` instance per session (holds player's accumulated history)
- Module-level dict `_game_orchestrators: dict[str, GameOrchestrator]` alongside `_game_sessions`
- Mirrors `session.py` pattern

### 7. `server/game_routes.py` — API endpoints under `/api/games/`
- `POST /games/sessions` — create game session
- `GET /games/sessions/{id}` — get session
- `DELETE /games/sessions/{id}` — delete session
- `PATCH /games/sessions/{id}/config` — update manager/player configs
- `POST /games/sessions/{id}/start` — generate opening (may involve player turn)
- `POST /games/sessions/{id}/move` — process human move through manager→player pipeline
- `GET /games/sessions/{id}/transcript` — download JSON or CSV
- `GET /games/config/defaults` — default configs
- Returns only `visible` messages to frontend

### 8. `frontend/src/components/GameChatMessage.tsx` — Game message component
- Manager messages: cyan, left-aligned, labeled "Game"
- Human messages: gray, right-aligned, labeled "You"
- Only renders `visible` messages

### 9. `prompts/games/` — Example prompt pairs
- `ultimatum_manager.md` + `ultimatum_player.md` (split from user's mega-prompt)
- `bargaining_manager.md` + `bargaining_player.md` (split from user's mega-prompt)

### 10. `tests/test_game.py` + `tests/test_game_logging.py`
- Model creation tests (GameMessage, GameTranscript)
- `[PLAYER_TURN]` regex parsing tests (match, no-match, multiline)
- `_strip_protocol_tags()` tests
- `GameManager._format_messages()` role mapping tests
- API key validation tests (dummy key `"sk-test-dummy"`)
- Transcript save/load tests (JSON + CSV)

## Files to Modify (5)

1. **`interviewer/__init__.py`** — add game exports (GameManager, PlayerAgent, GameOrchestrator, GameMessage, GameTranscript, save_game_transcript, game defaults)
2. **`server/app.py`** — add `app.include_router(game_router)` (1 line)
3. **`frontend/src/types.ts`** — add `GameMessage`, `GameSession`, `GameDefaults` interfaces
4. **`frontend/src/api.ts`** — add game API wrappers (createGameSession, startGame, sendGameMove, getGameDefaults, getGameTranscript)
5. **`frontend/src/App.tsx`** — add mode toggle (Interview/Game) and game-specific state management

## Implementation Order

1. `interviewer/game_models.py` (no deps)
2. `interviewer/game_defaults.py` (no deps)
3. `interviewer/game.py` (deps: 1, 2)
4. `interviewer/game_logging.py` (deps: 1)
5. `interviewer/__init__.py` (add exports)
6. `tests/test_game.py` + `tests/test_game_logging.py` → run pytest
7. `prompts/games/*.md` (example prompts)
8. `cli/main.py` (add game command)
9. `server/game_session.py` (deps: 1, 2)
10. `server/game_routes.py` (deps: 3, 9)
11. `server/app.py` (register router)
12. Frontend: types.ts → api.ts → GameChatMessage.tsx → App.tsx

## Verification

1. **Unit tests**: `pytest tests/test_game.py tests/test_game_logging.py` — protocol parsing, message formatting, model creation, transcript saving (no real API calls)
2. **CLI smoke test**: `interview game -M prompts/games/ultimatum_manager.md -P prompts/games/ultimatum_player.md` — play a few rounds manually
3. **API test**: Start backend, `curl -X POST localhost:8000/api/games/sessions`, then start + send moves
4. **Frontend test**: Start both servers, toggle to Game mode, play through a game in the browser

## Usage Examples

```bash
# Play ultimatum game via CLI
interview game -M prompts/games/ultimatum_manager.md -P prompts/games/ultimatum_player.md

# Play bargaining game via CLI
interview game -M prompts/games/bargaining_manager.md -P prompts/games/bargaining_player.md

# Any new game — just write two .md files
interview game -M prompts/games/prisoners_dilemma_manager.md -P prompts/games/prisoners_dilemma_player.md

# Save transcript
interview game -M prompts/games/ultimatum_manager.md -P prompts/games/ultimatum_player.md --save results.json
```
