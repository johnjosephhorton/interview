# CLAUDE.md

## Research Vision

This project is building toward a fully automated social science pipeline for two-player economic games, extending the approach in *Automated Social Science: Language Models as Scientist and Subjects* (Manning, 2024 NBER). The pipeline is an explicit loop — each experiment's results feed the next hypothesis:

```
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    ▼                                                             │
1. Hypothesize  ──→  2. Design  ──→  3. Create  ──→  4. Simulate │
   /hypothesize      /design-exp     /create-game    interview    │
                                                     simulate    │
                                                         │        │
                                                         ▼        │
                                            5. Analyze ──→ 6. Iterate
                                               /analyze-results   │
                                                         │        │
                                                         └────────┘
                                                    /hypothesize iterate
```

### Pipeline steps

1. **Hypothesize** — Generate a testable hypothesis about strategic behavior, formalize as a Pearlean causal DAG, score for triviality (`/hypothesize`). Output: `experiments/<name>/hypothesis.md`
2. **Design** — Map the hypothesis to a two-player economic game with treatment conditions and analysis plan (`/design-experiment`). Output: `experiments/<name>/design.md` + `manifest.toml`
3. **Create** — Generate the 4-file game implementation: config.toml, manager.md, player.md, sim_human.md (`/create-2-player-game`)
4. **Simulate** — Run N in-silico games with experimental randomization (`interview simulate --seed --design factorial`)
5. **Analyze** — Extract structured data, run statistical tests, produce a results memo with verdict and diagnosis (`/analyze-results`). Output: `experiments/<name>/results.pdf` + `data/data.csv`
6. **Iterate** — Feed results back into `/hypothesize iterate` to refine the hypothesis and run the next experiment

### Key design principles

- **Both agents are earnings maximizers.** The AI player and simulated human both receive an earnings-maximization objective, payoff formula, and hard guardrails — not scripted strategies. This produces naturalistic behavior sensitive to game parameters and treatment conditions. The `respondent_temperature` setting in config.toml controls sim_human variance (0.0 for deterministic pilots, higher for behavioral realism).
- **The meta-goal is autonomous iteration.** The pipeline should be able to run `/hypothesize` → `/analyze-results` → `/hypothesize iterate` with minimal human intervention. Human involvement is for steering (choosing which hypothesis to pursue) and validation (reviewing results memos), not for mechanical steps.
- **Two-player economic games only.** Bargaining, auctions, public goods, trust, etc. Every game supports human-in-the-loop mode (`interview chat`) so hypotheses validated in silico can be tested with human subjects.

All micro-level decisions — prompt wording, game mechanics, data formats, CLI flags — should serve this macro goal of a credible, reproducible, automated research pipeline.

## Project Overview

**Interviewer** is a standalone AI interviewer for qualitative research. It uses symmetric LLM agents — one plays the interviewer, one plays the respondent — both powered by OpenAI chat completions. The project has two interfaces: a CLI (Typer) and a REST API (FastAPI).

## Repository Layout

```
interviewer/          # Core library (Python package)
  __init__.py         # Public API re-exports
  models.py           # Pydantic models: Message, AgentConfig, Transcript, LLMCallInfo, AgentResponse, load_prompt()
  core.py             # Interviewer class — generates interviewer responses via OpenAI
  respondent.py       # SimulatedRespondent class — generates respondent responses via OpenAI
  simulation.py       # Simulation class — orchestrates multi-turn automated interviews
  defaults.py         # All default constants: prompts, model, temperature, token limits, canned responses
  logging.py          # save_transcript() — writes Transcript to JSON or CSV

cli/                  # CLI layer (Typer app)
  main.py             # `interview` command with subcommands: chat, simulate, show, preview

server/               # REST API layer (FastAPI)
  app.py              # create_app() factory
  routes.py           # All API endpoints under /api prefix
  session.py          # In-memory session store (Session model + CRUD functions)

games/                # Game definitions (one folder per game)
  bargainer/          # Multi-round price negotiation
  bargain_imperfect/  # Bargainer variant with asymmetric information
  ultimatum/          # Repeated ultimatum game
  pd_rep/             # Repeated prisoner's dilemma
  trust/              # One-shot trust/investment game
  auction/            # First-price sealed-bid auction
  contest/            # All-pay contest
  public_goods/       # Public goods contribution game
  TEMPLATE_MANAGER.md # Template for new manager prompts
  TEMPLATE_PLAYER.md  # Template for new player prompts
  TEMPLATE_CONFIG.md  # Template for new config files
  DESIGN_NOTES.md     # Running log of bugs and lessons learned

experiments/          # Per-experiment output directories
  <name>/             # One directory per experiment
    manifest.toml     # Machine-readable experiment metadata
    hypothesis.md     # Hypothesis memo (markdown)
    design.md         # Design memo (markdown)
    results.tex       # Results memo (LaTeX source)
    results.pdf       # Results memo (compiled)
    plots/            # All figures (PDF) + generator scripts (Python)
    data/             # Extracted data (CSV) + extraction/analysis scripts
  _archive/           # Abandoned or superseded experiments

prompts/              # Prompt files (.md)
  interviewer_default.md
  respondent_default.md
  examples/           # Example custom prompts (open_source_interviewer.md, open_source_respondent.md)

tests/                # Pytest test suite
  test_models.py      # Tests for Pydantic models, defaults, load_prompt()
  test_core.py        # Tests for Interviewer (hardcoded responses, message formatting, API key handling)
  test_logging.py     # Tests for save_transcript() in JSON and CSV formats
```

## Architecture

### Symmetric Agent Design

Both `Interviewer` and `SimulatedRespondent` follow the same pattern:
1. Accept a list of `Message` objects and an `AgentConfig`
2. Format messages into OpenAI API format, swapping roles based on perspective:
   - `Interviewer._format_messages()`: interviewer messages become `assistant`, respondent messages become `user`
   - `SimulatedRespondent._format_messages()`: respondent messages become `assistant`, interviewer messages become `user`
3. Call `AsyncOpenAI.chat.completions.create()` and return an `AgentResponse` with text + `LLMCallInfo`

### Message Types (Interviewer only)

The `Interviewer.generate_response()` method accepts a `message_type` parameter:
- `"opening_message"` — uses a special system prompt + `OPENING_INSTRUCTION` with a reduced token limit (`DEFAULT_OPENING_MAX_TOKENS = 150`)
- `"next_message"` — standard follow-up using full conversation history
- `"last_question"` — returns a hardcoded string (`LAST_QUESTION_RESPONSE`), no LLM call
- `"end_of_interview"` — returns a hardcoded string (`END_OF_INTERVIEW_RESPONSE`), no LLM call

### Simulation Flow

`Simulation.run()` orchestrates a full automated interview:
1. Interviewer generates opening message
2. Loop for `max_turns` iterations: respondent replies, then interviewer follows up
3. Interviewer sends last question (hardcoded)
4. Respondent answers the last question
5. Interviewer sends end-of-interview message (hardcoded)
6. Returns a `Transcript` with all messages and token usage

### Prompt Resolution

`load_prompt(value)` in `models.py`: if the value ends with `.md` and is an existing file path, it reads and returns the file contents (stripped). Otherwise it returns the string as-is. This is used throughout the CLI and library so prompts can be specified as either inline text or file paths.

### Server Session Model

The server uses an in-memory session store (`server/session.py`). Sessions have a lifecycle: `created` -> `active` -> `ended`. Sessions hold their own `interviewer_config`, `respondent_config`, `messages` list, and `status`. No persistence — all state is lost on restart.

### Game Structure

Each game lives in `games/<name>/` with four files:
- `config.toml` — game metadata (name, description, rounds, model settings)
- `manager.md` — prompt for the game manager LLM (controls flow, validates input, displays state)
- `player.md` — prompt for the AI player LLM (strategy, fully self-contained game rules)
- `sim_human.md` — prompt for a simulated human player

Games are loaded via `load_game()` in `interviewer/models.py`.

### End-of-Game Detection

The manager prompt instructs the LLM to output `══════════ GAME OVER ══════════` and a `YOU ARE FINISHED` box at the end. Both `routes.py` and `cli/main.py` detect these markers and terminate the session automatically.

## Key Models (interviewer/models.py)

- `Message(role: "interviewer" | "respondent", text: str)`
- `AgentConfig(system_prompt: str, model: str = "gpt-5", temperature: float = 1, max_tokens: int = 200)`
- `LLMCallInfo(model, messages, params, input_tokens, output_tokens)`
- `AgentResponse(text: str, llm_call_info: LLMCallInfo | None)`
- `Transcript(messages, interviewer_config, respondent_config, started_at, ended_at, total_input_tokens, total_output_tokens, llm_calls)`

## API Endpoints (server/routes.py)

All routes are prefixed with `/api`.

| Method | Path | Description |
|--------|------|-------------|
| POST | /sessions | Create a new session (optional configs in body) |
| GET | /sessions/{id} | Get session state |
| DELETE | /sessions/{id} | Delete session |
| PATCH | /sessions/{id}/config | Update interviewer/respondent configs |
| POST | /sessions/{id}/start | Generate opening message, set status to active |
| POST | /sessions/{id}/messages | Send respondent text, get interviewer reply |
| POST | /sessions/{id}/simulate-turn | AI respondent replies + interviewer follows up |
| POST | /sessions/{id}/simulate-all | Run interview to completion (query param: max_turns) |
| GET | /sessions/{id}/transcript | Download transcript (query param: format=json\|csv) |
| GET | /config/defaults | Get default config values |

## CLI Commands

Entry point: `interview` (defined in `pyproject.toml` as `cli.main:app`).

- `interview chat` — Interactive mode: you are the respondent. Supports `/last_question` and `/end` in-session commands.
- `interview simulate` — Fully automated. Both sides AI. Runs `--num-simulations` in parallel via `asyncio.gather()`. Output is CSV with columns `simulation_id, transcript` (JSON blob).
- `interview show <csv_file>` — Browse simulation results interactively.
- `interview preview` — Print resolved system prompt to stdout.

## Development Commands

```bash
# Install everything (editable mode)
pip install -e ".[cli,server,dev]"

# Run tests
pytest

# Start backend (FastAPI with auto-reload)
cd server && uvicorn app:create_app --factory --reload --port 8000

# Or use Makefile shortcuts
make install       # pip install -e ".[cli,server,dev]"
make test          # pytest
make backend       # backend only
```

## Environment

- Requires `OPENAI_API_KEY` — set as env var or in a `.env` file (loaded via python-dotenv)
- Python 3.10+

## Testing Conventions

- Tests are in `tests/` and use `pytest` + `pytest-asyncio`
- Async test mode is set to `auto` in `pyproject.toml` (`asyncio_mode = "auto"`)
- Tests avoid making real API calls — they test hardcoded responses, message formatting, model construction, and transcript serialization
- Use `Interviewer(api_key="sk-test-dummy")` to construct test instances without needing a real key
- The `test_api_key_missing_raises` test temporarily clears the env var; it restores it in a finally block

## Code Style

- Linter: `ruff` with `line-length = 100`
- Type annotations: `from __future__ import annotations` used throughout for modern union syntax (`str | None`)
- All models are Pydantic v2 `BaseModel` subclasses
- Async throughout: all LLM calls use `AsyncOpenAI` and `async/await`
- No classes where functions suffice — the session store is plain functions + a module-level dict

## Common Patterns

### Adding a new field to transcripts
1. Add the field to `Transcript` in `interviewer/models.py`
2. Populate it in `Simulation.run()` (`interviewer/simulation.py`) and `_chat()` / `_simulate()` in `cli/main.py`
3. Handle it in `save_transcript()` (`interviewer/logging.py`) if it needs special CSV formatting
4. Add to `Session` or route responses in `server/routes.py` if it should be exposed via the API

### Adding a new CLI command
1. Add a new `@app.command()` function in `cli/main.py`
2. It will be available as `interview <command-name>`

### Adding a new API endpoint
1. Add the route function in `server/routes.py` on the `router` object

### Adding a new game
1. Create a new folder under `games/` with `config.toml`, `manager.md`, `player.md`, `sim_human.md`
2. Follow the templates in `games/TEMPLATE_*.md` and `games/TEMPLATE_CONFIG.md`
3. See `games/DESIGN_NOTES.md` for common pitfalls

### Custom prompts
Create a `.md` file and pass it via CLI flags (`-s`, `-i`, `-r`) or set it in `AgentConfig.system_prompt`. The `load_prompt()` function handles resolution. Example prompts are in `prompts/examples/`.
