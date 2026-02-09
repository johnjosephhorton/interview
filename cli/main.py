from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from interviewer import (
    DEFAULT_MODEL,
    AgentConfig,
    Interviewer,
    Message,
    Simulation,
    Transcript,
    list_games,
    load_game,
    load_prompt,
    save_transcript,
)

app = typer.Typer(name="interview", help="AI Interviewer CLI")
console = Console()


@app.command()
def chat(
    game: str = typer.Argument(..., help="Game name (matches a folder in games/)"),
    system_prompt: Optional[str] = typer.Option(
        None,
        "--system-prompt",
        "-s",
        help="Override interviewer system prompt (inline text or path to .md file)",
    ),
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help="OpenAI model"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Sampling temperature"),
    max_tokens: int = typer.Option(200, "--max-tokens", help="Max tokens per response"),
    save: Optional[str] = typer.Option(None, "--save", help="Save transcript to file (json/csv)"),
):
    """Interactive CLI chat — you are the respondent."""
    asyncio.run(_chat(game, system_prompt, model, temperature, max_tokens, save))


async def _chat(
    game_name: str,
    system_prompt_override: str | None,
    model: str,
    temperature: float,
    max_tokens: int,
    save_path: str | None,
):
    from interviewer import Transcript

    game_config = load_game(game_name)

    # Use game prompt, but allow CLI override
    prompt = game_config.interviewer_system_prompt
    if system_prompt_override:
        prompt = load_prompt(system_prompt_override)

    config = AgentConfig(
        system_prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    interviewer = Interviewer()
    messages: list[Message] = []
    transcript = Transcript(interviewer_config=config)

    label = game_config.name

    console.print(
        Panel(
            f"[bold]{label}[/bold] — Type your responses.\n"
            "  /last_question — signal the final question\n"
            "  /end           — end the session"
        )
    )

    def _print_interviewer(text: str):
        console.print()
        console.print(Text(f"{label}: ", style="bold blue"), end="")
        console.print(text)

    def _track(resp):
        if resp.llm_call_info:
            transcript.llm_calls.append(resp.llm_call_info)
            transcript.total_input_tokens += resp.llm_call_info.input_tokens
            transcript.total_output_tokens += resp.llm_call_info.output_tokens

    # Opening message
    opening = await interviewer.generate_response(
        messages, config, message_type="opening_message", game_config=game_config
    )
    msg = Message(role="interviewer", text=opening.text)
    messages.append(msg)
    transcript.messages.append(msg)
    _track(opening)
    _print_interviewer(opening.text)

    while True:
        console.print()
        user_input = console.input("[bold green]You: [/bold green]").strip()

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "/last_question":
            last_q = await interviewer.generate_response(
                messages, config, message_type="last_question", game_config=game_config
            )
            msg = Message(role="interviewer", text=last_q.text)
            messages.append(msg)
            transcript.messages.append(msg)
            _track(last_q)
            _print_interviewer(last_q.text)
            continue

        if cmd == "/end":
            end = await interviewer.generate_response(
                messages, config, message_type="end_of_interview", game_config=game_config
            )
            msg = Message(role="interviewer", text=end.text)
            messages.append(msg)
            transcript.messages.append(msg)
            _track(end)
            _print_interviewer(end.text)
            break

        # Add respondent message
        msg = Message(role="respondent", text=user_input)
        messages.append(msg)
        transcript.messages.append(msg)

        # Get interviewer response
        response = await interviewer.generate_response(
            messages, config, message_type="next_message", game_config=game_config
        )
        msg = Message(role="interviewer", text=response.text)
        messages.append(msg)
        transcript.messages.append(msg)
        _track(response)
        _print_interviewer(response.text)

    if save_path:
        fmt = "csv" if save_path.endswith(".csv") else "json"
        save_transcript(transcript, save_path, format=fmt)
        console.print(f"\nTranscript saved to {save_path}")

    console.print(
        f"\nTokens used: {transcript.total_input_tokens} input, "
        f"{transcript.total_output_tokens} output"
    )


@app.command()
def simulate(
    game: str = typer.Argument(..., help="Game name (matches a folder in games/)"),
    interviewer_prompt: Optional[str] = typer.Option(
        None,
        "--interviewer-prompt",
        "-i",
        help="Override interviewer system prompt (inline text or path to .md file)",
    ),
    respondent_prompt: Optional[str] = typer.Option(
        None,
        "--respondent-prompt",
        "-r",
        help="Override respondent system prompt (inline text or path to .md file)",
    ),
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help="OpenAI model"),
    temperature: float = typer.Option(0.7, "--temperature", "-t"),
    max_tokens: int = typer.Option(200, "--max-tokens"),
    max_turns: int = typer.Option(5, "--max-turns", help="Number of conversation turns"),
    num_simulations: int = typer.Option(1, "--num-simulations", "-n", help="Number of simulations to run in parallel"),
    save: str = typer.Option(..., "--save", "-o", help="Output CSV file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print conversation to terminal"),
):
    """Fully automated simulation — both sides are AI."""
    asyncio.run(
        _simulate(
            game, interviewer_prompt, respondent_prompt, model, temperature, max_tokens,
            max_turns, num_simulations, save, verbose,
        )
    )


async def _run_one_simulation(
    sim_id: int,
    interviewer_config: AgentConfig,
    respondent_config: AgentConfig,
    max_turns: int,
    on_message: callable | None = None,
    game_config=None,
) -> Transcript:
    """Run a single simulation and return its transcript."""
    sim = Simulation()
    return await sim.run(
        interviewer_config, respondent_config, max_turns=max_turns,
        on_message=on_message, game_config=game_config,
    )


async def _simulate(
    game_name: str,
    interviewer_prompt_override: str | None,
    respondent_prompt_override: str | None,
    model: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    num_simulations: int,
    save_path: str,
    verbose: bool,
):
    game_config = load_game(game_name)

    # Use game prompts, allow CLI overrides
    int_prompt = game_config.interviewer_system_prompt
    if interviewer_prompt_override:
        int_prompt = load_prompt(interviewer_prompt_override)

    resp_prompt = game_config.respondent_system_prompt
    if respondent_prompt_override:
        resp_prompt = load_prompt(respondent_prompt_override)

    interviewer_config = AgentConfig(
        system_prompt=int_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    respondent_config = AgentConfig(
        system_prompt=resp_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    label = game_config.name
    on_message = None
    if verbose and num_simulations == 1:
        console.print(
            Panel(f"[bold]{label} Simulation[/bold] — {max_turns} turns, model: {model}")
        )

        def on_message(msg: Message):
            console.print()
            if msg.role == "interviewer":
                console.print(Text(f"{label}: ", style="bold blue"), end="")
            else:
                console.print(Text("Respondent: ", style="bold green"), end="")
            console.print(msg.text)

    # Run simulations in parallel
    tasks = [
        _run_one_simulation(
            i, interviewer_config, respondent_config, max_turns,
            on_message, game_config=game_config,
        )
        for i in range(num_simulations)
    ]
    transcripts = await asyncio.gather(*tasks)

    # Write results to CSV: each row is the JSON of one conversation
    path = Path(save_path)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["simulation_id", "transcript"])
        for i, transcript in enumerate(transcripts):
            transcript_json = transcript.model_dump_json(
                exclude={"llm_calls": {"__all__": {"messages"}}}
            )
            writer.writerow([i + 1, transcript_json])

    if verbose:
        total_input = sum(t.total_input_tokens for t in transcripts)
        total_output = sum(t.total_output_tokens for t in transcripts)
        console.print(f"\n{num_simulations} simulation(s) saved to {save_path}")
        console.print(f"Total tokens: {total_input} input, {total_output} output")


@app.command()
def show(
    csv_file: str = typer.Argument(..., help="Path to simulation results CSV file"),
):
    """Browse simulated interviews from a CSV results file."""
    import json as json_mod

    path = Path(csv_file)
    if not path.exists():
        console.print(f"[red]File not found: {csv_file}[/red]")
        raise typer.Exit(1)

    # Read transcripts from CSV
    transcripts: list[tuple[int, Transcript]] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sim_id = int(row["simulation_id"])
            data = json_mod.loads(row["transcript"])
            transcripts.append((sim_id, Transcript(**data)))

    if not transcripts:
        console.print("[yellow]No simulations found in file.[/yellow]")
        raise typer.Exit(0)

    # Display list of simulations
    console.print(Panel(f"[bold]{len(transcripts)} simulated interview(s)[/bold] in {csv_file}"))
    console.print()
    for sim_id, t in transcripts:
        n_messages = len(t.messages)
        first_msg = t.messages[0].text[:80] + "..." if t.messages and len(t.messages[0].text) > 80 else (t.messages[0].text if t.messages else "")
        console.print(f"  [bold]{sim_id}[/bold]. {n_messages} messages — {first_msg}")
    console.print()

    # Let user select one
    while True:
        choice = console.input(
            f"[bold]Select interview (1-{len(transcripts)}), or q to quit: [/bold]"
        ).strip()
        if choice.lower() == "q":
            return
        try:
            idx = int(choice)
            if 1 <= idx <= len(transcripts):
                break
        except ValueError:
            pass
        console.print("[red]Invalid selection.[/red]")

    # Display the selected interview
    _, transcript = transcripts[idx - 1]
    console.print()
    console.print(Panel(f"[bold]Interview {idx}[/bold]"))
    for msg in transcript.messages:
        console.print()
        if msg.role == "interviewer":
            console.print(Text("Interviewer: ", style="bold blue"), end="")
        else:
            console.print(Text("Respondent: ", style="bold green"), end="")
        console.print(msg.text)
    console.print()
    console.print(
        f"Tokens: {transcript.total_input_tokens} input, "
        f"{transcript.total_output_tokens} output"
    )


@app.command()
def preview(
    game: str = typer.Argument(..., help="Game name (matches a folder in games/)"),
    system_prompt: Optional[str] = typer.Option(
        None,
        "--system-prompt",
        "-s",
        help="Override system prompt (inline text or path to .md file)",
    ),
):
    """Print the resolved system prompt to stdout."""
    game_config = load_game(game)
    prompt = game_config.interviewer_system_prompt
    if system_prompt:
        prompt = load_prompt(system_prompt)
    console.print(Panel(prompt, title=f"{game_config.name} — System Prompt"))


@app.command()
def games():
    """List available games."""
    available = list_games()
    if not available:
        console.print("[yellow]No games found in games/ folder.[/yellow]")
        raise typer.Exit(0)

    console.print(Panel("[bold]Available Games[/bold]"))
    for g in available:
        desc = f" — {g['description']}" if g["description"] else ""
        console.print(f"  [bold]{g['name']}[/bold]{desc}")


if __name__ == "__main__":
    app()
