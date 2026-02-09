# Interviewer

A standalone AI interviewer with symmetric LLM agents for qualitative research. Conduct interactive interviews where you answer questions from an AI interviewer, or run fully automated simulations where both sides are AI.

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

## CLI Commands

The package installs an `interview` command with four subcommands:

### `interview chat` -- Interactive interview

You are the respondent. The AI interviewer asks questions and you type responses.

```bash
interview chat
```

Options:

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--system-prompt` | `-s` | built-in default | Interviewer system prompt (inline text or path to a `.md` file) |
| `--model` | `-m` | `gpt-4o-mini` | OpenAI model |
| `--temperature` | `-t` | `0.7` | Sampling temperature |
| `--max-tokens` | | `200` | Max tokens per response |
| `--save` | | | Save transcript to file (`.json` or `.csv`) |

In-session commands:
- `/last_question` -- ask the interviewer to pose a final question
- `/end` -- end the interview

Example with a custom prompt:

```bash
interview chat -s prompts/examples/open_source_interviewer.md --save transcript.json
```

### `interview simulate` -- Automated simulation

Both interviewer and respondent are AI. Runs one or more simulations and writes results to CSV.

```bash
interview simulate --save results.csv
```

Options:

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--interviewer-prompt` | `-i` | built-in default | Interviewer system prompt |
| `--respondent-prompt` | `-r` | built-in default | Respondent system prompt |
| `--model` | `-m` | `gpt-4o-mini` | OpenAI model |
| `--temperature` | `-t` | `0.7` | Sampling temperature |
| `--max-tokens` | | `200` | Max tokens per response |
| `--max-turns` | | `5` | Number of conversation turns |
| `--num-simulations` | `-n` | `1` | Number of simulations to run in parallel |
| `--save` | `-o` | **(required)** | Output CSV file path |
| `--verbose` | `-v` | `false` | Print conversation to terminal |

Example running 10 parallel simulations with custom prompts:

```bash
interview simulate \
  -i prompts/examples/open_source_interviewer.md \
  -r prompts/examples/open_source_respondent.md \
  -n 10 --max-turns 8 --save results.csv -v
```

### `interview show` -- Browse simulation results

Interactively browse transcripts from a simulation CSV file.

```bash
interview show results.csv
```

### `interview preview` -- Preview a resolved prompt

Print the resolved system prompt to stdout. Useful for verifying that a `.md` file loads correctly.

```bash
interview preview -s prompts/examples/open_source_interviewer.md
```

## Custom Prompts

System prompts can be provided as inline text or as a path to a `.md` file. Example prompt files are in `prompts/examples/`.

To write your own, create a `.md` file with the interviewer's persona and rules, then pass it with `-s` (chat) or `-i`/`-r` (simulate).

## Output Formats

- **JSON** (`--save transcript.json` in `chat`): Full transcript with messages, configs, token counts, and LLM call metadata.
- **CSV** (`--save results.csv` in `simulate`): One row per simulation with columns `simulation_id` and `transcript` (JSON blob).
