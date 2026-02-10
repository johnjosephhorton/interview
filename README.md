# Interviewer

A platform for running economic games between a human participant and an AI player, powered by OpenAI LLM agents. The AI game manager controls the flow, validates input, and tracks scores, while a separate AI player makes strategic decisions.

## Setup

Requires Python 3.10+.

```bash
pip install -e ".[cli,server,dev]"
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."
```

Or add it to a `.env` file in the project root.

## Available Games

| Game | Folder | Description | Rounds |
|------|--------|-------------|--------|
| **Bargainer** | `bargainer` | Negotiate the price of a mug. Both sides make counteroffers until someone accepts or rounds run out. | 6 |
| **Bargainer (Imperfect Info)** | `bargain_imperfect` | Same as Bargainer, but the human is told the AI's value range ($4–$8). | 6 |
| **Ultimatum** | `ultimatum` | Split $100 each round. One player proposes, the other accepts or rejects. | 4 |
| **Prisoner's Dilemma** | `pd_rep` | Classic repeated PD — COOPERATE or DEFECT each round. | 5 |
| **Trust Game** | `trust` | One-shot: human sends money, it triples, AI decides how much to return. | 1 |
| **Sealed-Bid Auction** | `auction` | First-price sealed-bid auction with private valuations. Both bid simultaneously. | 3 |
| **Contest (All-Pay)** | `contest` | Both invest effort for a $10 prize. Higher investor wins, but both pay. | 3 |
| **Public Goods** | `public_goods` | Both receive $10 and choose how much to contribute to a shared pool (doubled and split). | 5 |

## Playing a Game (CLI)

Use `interview chat` with the `-s` flag pointing to a game's manager prompt:

```bash
interview chat -s games/bargainer/manager.md
```

This starts an interactive session where the AI manager explains the game and you play against the AI player. The game ends automatically when all rounds are complete.

### Examples

```bash
# Bargaining over a mug
interview chat -s games/bargainer/manager.md

# Bargaining with imperfect information (you know the AI's range)
interview chat -s games/bargain_imperfect/manager.md

# Ultimatum game — split $100
interview chat -s games/ultimatum/manager.md

# Repeated Prisoner's Dilemma
interview chat -s games/pd_rep/manager.md

# Trust game — one shot
interview chat -s games/trust/manager.md

# Sealed-bid auction
interview chat -s games/auction/manager.md

# All-pay contest
interview chat -s games/contest/manager.md

# Public goods game
interview chat -s games/public_goods/manager.md
```

### CLI Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--system-prompt` | `-s` | built-in default | Manager system prompt (path to `.md` file or inline text) |
| `--model` | `-m` | `gpt-4o-mini` | OpenAI model |
| `--temperature` | `-t` | `0.7` | Sampling temperature |
| `--max-tokens` | | `200` | Max tokens per response |
| `--save` | | | Save transcript to file (`.json` or `.csv`) |

## Running Simulations (AI vs AI)

Run fully automated games where a simulated human plays against the AI:

```bash
interview simulate \
  -i games/bargainer/manager.md \
  -r games/bargainer/sim_human.md \
  -n 10 --save results.csv -v
```

This runs 10 parallel simulations of the bargaining game and saves results to CSV.

### Simulation Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--interviewer-prompt` | `-i` | built-in default | Manager system prompt |
| `--respondent-prompt` | `-r` | built-in default | Simulated human prompt |
| `--model` | `-m` | `gpt-4o-mini` | OpenAI model |
| `--max-turns` | | `5` | Max conversation turns |
| `--num-simulations` | `-n` | `1` | Number of parallel simulations |
| `--save` | `-o` | **(required)** | Output CSV file |
| `--verbose` | `-v` | `false` | Print conversations to terminal |

## Other CLI Commands

```bash
# Browse simulation results interactively
interview show results.csv

# Preview a resolved prompt
interview preview -s games/bargainer/manager.md
```

## Game Structure

Each game is a folder under `games/` with four files:

| File | Purpose |
|------|---------|
| `config.toml` | Game metadata — name, description, rounds, model settings |
| `manager.md` | Prompt for the game manager (controls flow, validates input, tracks scores) |
| `player.md` | Prompt for the AI player (strategy and self-contained game rules) |
| `sim_human.md` | Prompt for a simulated human participant (used in `simulate` mode) |

### Creating a New Game

1. Copy an existing game folder as a starting point
2. Follow the templates in `games/TEMPLATE_MANAGER.md`, `games/TEMPLATE_PLAYER.md`, and `games/TEMPLATE_CONFIG.md`
3. See `games/DESIGN_NOTES.md` for common pitfalls and lessons learned

## REST API

Start the backend server:

```bash
cd server && uvicorn app:create_app --factory --reload --port 8000
```

See `CLAUDE.md` for full endpoint documentation.

## Development

```bash
make install    # pip install -e ".[cli,server,dev]"
make test       # pytest
make backend    # start FastAPI server
```
