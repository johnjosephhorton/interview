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
    DEFAULT_GAME_MODEL,
    DEFAULT_GAME_PLAYER_MODEL,
    DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
    DEFAULT_MODEL,
    DEFAULT_RESPONDENT_SYSTEM_PROMPT,
    AgentConfig,
    GameOrchestrator,
    GameRunner,
    Interviewer,
    Message,
    Simulation,
    Transcript,
    load_prompt,
    save_game_transcript,
    save_transcript,
)

app = typer.Typer(name="interview", help="AI Interviewer CLI")
console = Console()


@app.command()
def chat(
    system_prompt: str = typer.Option(
        DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
        "--system-prompt",
        "-s",
        help="Interviewer system prompt (inline text or path to .md file)",
    ),
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help="OpenAI model"),
    temperature: float = typer.Option(1.0, "--temperature", "-t", help="Sampling temperature"),
    max_tokens: int = typer.Option(200, "--max-tokens", help="Max tokens per response"),
    save: Optional[str] = typer.Option(None, "--save", help="Save transcript to file (json/csv)"),
):
    """Interactive CLI chat — you are the respondent."""
    asyncio.run(_chat(system_prompt, model, temperature, max_tokens, save))


async def _chat(
    system_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    save_path: str | None,
):
    from interviewer import Transcript

    resolved_prompt = load_prompt(system_prompt)
    config = AgentConfig(
        system_prompt=resolved_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    interviewer = Interviewer()
    messages: list[Message] = []
    transcript = Transcript(interviewer_config=config)

    console.print(
        Panel(
            "[bold]AI Interview[/bold] — Type your responses.\n"
            "  /last_question — signal the interviewer to ask a final question\n"
            "  /end           — end the interview"
        )
    )

    def _print_interviewer(text: str):
        console.print()
        console.print(Text("Interviewer: ", style="bold blue"), end="")
        console.print(text)

    def _track(resp):
        if resp.llm_call_info:
            transcript.llm_calls.append(resp.llm_call_info)
            transcript.total_input_tokens += resp.llm_call_info.input_tokens
            transcript.total_output_tokens += resp.llm_call_info.output_tokens

    # Opening message
    opening = await interviewer.generate_response(messages, config, message_type="opening_message")
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
                messages, config, message_type="last_question"
            )
            msg = Message(role="interviewer", text=last_q.text)
            messages.append(msg)
            transcript.messages.append(msg)
            _track(last_q)
            _print_interviewer(last_q.text)
            continue

        if cmd == "/end":
            end = await interviewer.generate_response(
                messages, config, message_type="end_of_interview"
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
            messages, config, message_type="next_message"
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
    interviewer_prompt: str = typer.Option(
        DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
        "--interviewer-prompt",
        "-i",
        help="Interviewer system prompt (inline text or path to .md file)",
    ),
    respondent_prompt: str = typer.Option(
        DEFAULT_RESPONDENT_SYSTEM_PROMPT,
        "--respondent-prompt",
        "-r",
        help="Respondent system prompt (inline text or path to .md file)",
    ),
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help="OpenAI model"),
    temperature: float = typer.Option(1.0, "--temperature", "-t"),
    max_tokens: int = typer.Option(200, "--max-tokens"),
    max_turns: int = typer.Option(5, "--max-turns", help="Number of conversation turns"),
    num_simulations: int = typer.Option(1, "--num-simulations", "-n", help="Number of simulations to run in parallel"),
    save: str = typer.Option(..., "--save", "-o", help="Output CSV file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print conversation to terminal"),
):
    """Fully automated simulation — both sides are AI."""
    asyncio.run(
        _simulate(
            interviewer_prompt, respondent_prompt, model, temperature, max_tokens,
            max_turns, num_simulations, save, verbose,
        )
    )


async def _run_one_simulation(
    sim_id: int,
    interviewer_config: AgentConfig,
    respondent_config: AgentConfig,
    max_turns: int,
    on_message: callable | None = None,
) -> Transcript:
    """Run a single simulation and return its transcript."""
    sim = Simulation()
    return await sim.run(
        interviewer_config, respondent_config, max_turns=max_turns, on_message=on_message
    )


async def _simulate(
    interviewer_prompt: str,
    respondent_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    num_simulations: int,
    save_path: str,
    verbose: bool,
):
    resolved_interviewer = load_prompt(interviewer_prompt)
    resolved_respondent = load_prompt(respondent_prompt)

    interviewer_config = AgentConfig(
        system_prompt=resolved_interviewer,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    respondent_config = AgentConfig(
        system_prompt=resolved_respondent,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    on_message = None
    if verbose and num_simulations == 1:
        console.print(
            Panel(f"[bold]Simulated Interview[/bold] — {max_turns} turns, model: {model}")
        )

        def on_message(msg: Message):
            console.print()
            if msg.role == "interviewer":
                console.print(Text("Interviewer: ", style="bold blue"), end="")
            else:
                console.print(Text("Respondent: ", style="bold green"), end="")
            console.print(msg.text)

    # Run simulations in parallel
    tasks = [
        _run_one_simulation(i, interviewer_config, respondent_config, max_turns, on_message)
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
def game(
    game_path: str = typer.Option(
        ...,
        "--game",
        "-G",
        help="Path to game folder (containing game.yaml, manager.md, player.md)",
    ),
    model: str = typer.Option(DEFAULT_GAME_MODEL, "--model", "-m", help="OpenAI model for manager"),
    player_model: str = typer.Option(
        DEFAULT_GAME_PLAYER_MODEL, "--player-model", help="OpenAI model for player"
    ),
    temperature: float = typer.Option(1.0, "--temperature", "-t", help="Sampling temperature"),
    manager_max_tokens: int = typer.Option(
        2048, "--manager-max-tokens", help="Max tokens for manager responses"
    ),
    player_max_tokens: int = typer.Option(
        256, "--player-max-tokens", help="Max tokens for player responses"
    ),
    save: Optional[str] = typer.Option(None, "--save", help="Save transcript to file (json/csv)"),
):
    """Interactive game — you are the human player."""
    asyncio.run(
        _game(
            game_path, model, player_model, temperature,
            manager_max_tokens, player_max_tokens, save,
        )
    )


async def _game(
    game_path: str,
    model: str,
    player_model: str,
    temperature: float,
    manager_max_tokens: int,
    player_max_tokens: int,
    save_path: str | None,
):
    from interviewer.game_models import GameMessage, GameTranscript

    realized = GameRunner.load_game(game_path)

    # Apply CLI overrides to configs from the game definition
    manager_config = AgentConfig(
        system_prompt=realized.manager_config.system_prompt,
        model=model,
        temperature=temperature,
        max_tokens=manager_max_tokens,
    )
    player_config = AgentConfig(
        system_prompt=realized.player_config.system_prompt,
        model=player_model,
        temperature=temperature,
        max_tokens=player_max_tokens,
    )

    orchestrator = GameOrchestrator()
    messages: list[GameMessage] = []
    transcript = GameTranscript(
        manager_config=manager_config,
        player_config=player_config,
        realized_params=realized.realized_params,
        game_name=realized.name,
    )

    # Display human instructions (private briefing)
    if realized.human_instructions:
        console.print(
            Panel(
                realized.human_instructions,
                title=f"[bold]{realized.name}[/bold] — Your Private Instructions",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(f"[bold]{realized.name}[/bold] — Type your moves.\n  /end  — end the game")
        )
    console.print("[dim]Type /end to quit.[/dim]\n")

    def _print_game(text: str):
        console.print()
        console.print(Text("Game Manager: ", style="bold cyan"), end="")
        console.print(Text(text))

    def _track_calls(llm_calls):
        for call in llm_calls:
            transcript.llm_calls.append(call)
            transcript.total_input_tokens += call.input_tokens
            transcript.total_output_tokens += call.output_tokens

    # Opening
    with console.status("[bold cyan]Game Manager is starting the game..."):
        new_msgs, llm_calls = await orchestrator.process_opening(manager_config, player_config)
    messages.extend(new_msgs)
    transcript.messages.extend(new_msgs)
    _track_calls(llm_calls)

    for msg in new_msgs:
        if msg.visible and msg.role == "manager":
            _print_game(msg.text)

    while True:
        console.print()
        user_input = console.input("[bold green]You: [/bold green]").strip()

        if not user_input:
            continue

        if user_input.lower() == "/end":
            break

        with console.status("[bold cyan]Game Manager is thinking..."):
            new_msgs, llm_calls = await orchestrator.process_human_input(
                user_input, messages, manager_config, player_config
            )
        messages.extend(new_msgs)
        transcript.messages.extend(new_msgs)
        _track_calls(llm_calls)

        for msg in new_msgs:
            if msg.visible and msg.role == "manager":
                _print_game(msg.text)

    if save_path:
        fmt = "csv" if save_path.endswith(".csv") else "json"
        save_game_transcript(transcript, save_path, format=fmt)
        console.print(f"\nTranscript saved to {save_path}")

    console.print(
        f"\nTokens used: {transcript.total_input_tokens} input, "
        f"{transcript.total_output_tokens} output"
    )


@app.command()
def preview(
    system_prompt: str = typer.Option(
        DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
        "--system-prompt",
        "-s",
        help="System prompt (inline text or path to .md file)",
    ),
):
    """Print the resolved system prompt to stdout."""
    resolved = load_prompt(system_prompt)
    console.print(Panel(resolved, title="System Prompt"))


if __name__ == "__main__":
    app()
