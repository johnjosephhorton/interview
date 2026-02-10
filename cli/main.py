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
    CheckResult,
    Interviewer,
    Message,
    Simulation,
    Transcript,
    TranscriptChecker,
    auto_save_transcript,
    list_games,
    load_game,
    load_prompt,
    save_transcript,
)

app = typer.Typer(name="interview", help="AI Interviewer CLI")
console = Console()

END_GAME_MARKERS = ("GAME OVER", "YOU ARE FINISHED")
POST_GAME_RESPONSE = "The game is complete. You do not need to do anything else. Thank you for participating!"


def _check_game_ended(text: str) -> bool:
    """Check if the LLM response contains either end-of-game marker."""
    return any(marker in text for marker in END_GAME_MARKERS)


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

        if _check_game_ended(response.text):
            break

    console.print(
        f"\nTokens used: {transcript.total_input_tokens} input, "
        f"{transcript.total_output_tokens} output"
    )

    # Auto-save transcript
    saved_path = auto_save_transcript(transcript, game_name)
    console.print(f"\nTranscript saved to {saved_path}")

    # Auto-check
    try:
        checker = TranscriptChecker()
        result = await checker.check(game_name, transcript.messages)

        status = "[green]PASS[/green]" if result.overall_passed else "[red]FAIL[/red]"
        console.print(f"\nChecker: {status}")
        for c in result.criteria:
            if not c.passed:
                console.print(f"  [red]x {c.criterion}[/red]: {c.explanation}")
            else:
                console.print(f"  [green]✓ {c.criterion}[/green]: {c.explanation}")

        # Save check results alongside transcript
        import json as json_mod
        check_path = saved_path.with_name(saved_path.stem + "_check.json")
        check_path.write_text(json_mod.dumps(result.model_dump(), indent=2))
        console.print(f"\nCheck results saved to {check_path}")
    except Exception as e:
        console.print(f"\n[yellow]Checker skipped: {e}[/yellow]")

    # Additional copy if --save specified
    if save_path:
        fmt = "csv" if save_path.endswith(".csv") else "json"
        save_transcript(transcript, save_path, format=fmt)
        console.print(f"Additional copy saved to {save_path}")


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
    save: Optional[str] = typer.Option(None, "--save", "-o", help="Additional CSV export path"),
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
    save_path: str | None,
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

    total_input = sum(t.total_input_tokens for t in transcripts)
    total_output = sum(t.total_output_tokens for t in transcripts)
    console.print(
        f"\n{num_simulations} simulation(s) complete. "
        f"Tokens: {total_input} input, {total_output} output"
    )

    # Auto-save each transcript
    from datetime import datetime as dt
    timestamp = dt.now().strftime("%Y-%m-%d_%H-%M-%S")
    saved_paths = []
    for i, transcript in enumerate(transcripts):
        suffix = f"sim{i + 1}"
        p = auto_save_transcript(transcript, game_name, suffix=suffix, timestamp=timestamp)
        saved_paths.append(p)
        console.print(f"  Saved: {p}")

    # Auto-check all transcripts in parallel
    try:
        checker = TranscriptChecker()
        check_tasks = [checker.check(game_name, t.messages) for t in transcripts]
        results: list[CheckResult] = await asyncio.gather(*check_tasks)

        import json as json_mod
        console.print()
        for i, (result, sp) in enumerate(zip(results, saved_paths)):
            status = "[green]PASS[/green]" if result.overall_passed else "[red]FAIL[/red]"
            console.print(f"  Sim {i + 1}: {status}")
            if not result.overall_passed:
                for c in result.criteria:
                    if not c.passed:
                        console.print(f"    [red]x {c.criterion}[/red]: {c.explanation}")

            check_path = sp.with_name(sp.stem + "_check.json")
            check_path.write_text(json_mod.dumps(result.model_dump(), indent=2))

        passed = sum(1 for r in results if r.overall_passed)
        console.print(f"\n{passed}/{len(results)} transcripts passed all checks.")
    except Exception as e:
        console.print(f"\n[yellow]Checker skipped: {e}[/yellow]")

    # Additional CSV export if --save specified
    if save_path:
        path = Path(save_path)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["simulation_id", "transcript"])
            for i, transcript in enumerate(transcripts):
                transcript_json = transcript.model_dump_json(
                    exclude={"llm_calls": {"__all__": {"messages"}}}
                )
                writer.writerow([i + 1, transcript_json])
        console.print(f"Additional CSV saved to {save_path}")


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


@app.command()
def check(
    game: str = typer.Argument(..., help="Game name (matches a folder in games/)"),
    transcript_file: str = typer.Argument(..., help="Path to transcript file (JSON or CSV)"),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="Checker model"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show per-criterion details"),
    save: Optional[str] = typer.Option(None, "--save", help="Save results to JSON file"),
):
    """Check a game transcript for correctness."""
    asyncio.run(_check(game, transcript_file, model, verbose, save))


async def _check(
    game_name: str,
    transcript_file: str,
    model: str,
    verbose: bool,
    save_path: str | None,
):
    import json as json_mod

    path = Path(transcript_file)
    if not path.exists():
        console.print(f"[red]File not found: {transcript_file}[/red]")
        raise typer.Exit(1)

    checker = TranscriptChecker(model=model)

    # Parse input — JSON (single) or CSV (batch)
    transcripts: list[tuple[int, list[Message]]] = []

    if path.suffix == ".json":
        data = json_mod.loads(path.read_text())
        messages = [Message(**m) for m in data.get("messages", [])]
        transcripts.append((1, messages))
    elif path.suffix == ".csv":
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sim_id = int(row["simulation_id"])
                data = json_mod.loads(row["transcript"])
                messages = [Message(**m) for m in data.get("messages", [])]
                transcripts.append((sim_id, messages))
    else:
        console.print(f"[red]Unsupported file format: {path.suffix}. Use .json or .csv[/red]")
        raise typer.Exit(1)

    if not transcripts:
        console.print("[yellow]No transcripts found in file.[/yellow]")
        raise typer.Exit(0)

    console.print(
        f"Checking {len(transcripts)} transcript(s) for [bold]{game_name}[/bold] "
        f"with model [bold]{model}[/bold]...\n"
    )

    # Run checks in parallel
    tasks = [checker.check(game_name, msgs) for _, msgs in transcripts]
    results: list[CheckResult] = await asyncio.gather(*tasks)

    # Display results
    for (sim_id, _), result in zip(transcripts, results):
        status = "[green]PASS[/green]" if result.overall_passed else "[red]FAIL[/red]"
        console.print(f"  Simulation {sim_id}: {status}")

        if verbose or not result.overall_passed:
            for c in result.criteria:
                if not c.passed:
                    console.print(f"    [red]x {c.criterion}[/red]: {c.explanation}")
                elif verbose:
                    console.print(f"    [green]✓ {c.criterion}[/green]: {c.explanation}")

    # Summary
    passed = sum(1 for r in results if r.overall_passed)
    total = len(results)
    console.print(f"\n{passed}/{total} transcripts passed all checks.")

    total_input = sum(r.input_tokens for r in results)
    total_output = sum(r.output_tokens for r in results)
    console.print(f"Checker tokens: {total_input} input, {total_output} output")

    # Save results
    if save_path:
        output = [r.model_dump() for r in results]
        Path(save_path).write_text(json_mod.dumps(output, indent=2))
        console.print(f"\nResults saved to {save_path}")


@app.command(name="check-summary")
def check_summary(
    game: str = typer.Argument(..., help="Game name (matches a folder in games/)"),
    no_suggest: bool = typer.Option(False, "--no-suggest", help="Skip LLM suggestions, report only"),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="Model for suggestions"),
):
    """Aggregate checker results and optionally get LLM suggestions for fixing failures."""
    asyncio.run(_check_summary(game, no_suggest, model))


async def _check_summary(game_name: str, no_suggest: bool, model: str):
    import json as json_mod
    from collections import defaultdict

    transcripts_dir = Path("transcripts") / game_name
    if not transcripts_dir.is_dir():
        console.print(f"[red]No transcripts directory found: {transcripts_dir}[/red]")
        raise typer.Exit(1)

    check_files = sorted(transcripts_dir.glob("*_check.json"))
    if not check_files:
        console.print(f"[yellow]No *_check.json files found in {transcripts_dir}[/yellow]")
        raise typer.Exit(0)

    # Aggregate pass/fail counts per criterion
    criterion_stats: dict[str, dict] = defaultdict(
        lambda: {"pass": 0, "fail": 0, "fail_explanations": []}
    )

    for cf in check_files:
        try:
            data = json_mod.loads(cf.read_text())
            for c in data.get("criteria", []):
                name = c["criterion"]
                if c["passed"]:
                    criterion_stats[name]["pass"] += 1
                else:
                    criterion_stats[name]["fail"] += 1
                    criterion_stats[name]["fail_explanations"].append(
                        {"file": cf.name, "explanation": c["explanation"]}
                    )
        except Exception:
            console.print(f"[yellow]Skipping malformed file: {cf.name}[/yellow]")

    total_transcripts = len(check_files)
    console.print(
        Panel(
            f"[bold]{game_name}[/bold] — {total_transcripts} checked transcript(s)",
            title="Check Summary",
        )
    )

    # Display table
    has_failures = False
    for name, stats in sorted(criterion_stats.items()):
        total = stats["pass"] + stats["fail"]
        fail_rate = stats["fail"] / total * 100 if total > 0 else 0
        if stats["fail"] > 0:
            has_failures = True
            console.print(
                f"  [red]x {name}[/red]: {stats['fail']}/{total} failed ({fail_rate:.0f}%)"
            )
            # Show up to 2 sample explanations
            for sample in stats["fail_explanations"][:2]:
                console.print(f"      {sample['file']}: {sample['explanation']}")
        else:
            console.print(f"  [green]✓ {name}[/green]: {total}/{total} passed")

    if not has_failures:
        console.print("\n[green]All criteria passed across all transcripts.[/green]")
        return

    if no_suggest:
        return

    # Build failure summary for LLM
    failure_lines = []
    for name, stats in sorted(criterion_stats.items()):
        if stats["fail"] > 0:
            total = stats["pass"] + stats["fail"]
            failure_lines.append(f"- {name}: {stats['fail']}/{total} failed")
            for sample in stats["fail_explanations"][:3]:
                failure_lines.append(f"  Example: {sample['explanation']}")
    failure_summary = "\n".join(failure_lines)

    # Load current game prompts
    manager_prompt, player_prompt, opening_instruction = TranscriptChecker._load_game_prompts(
        game_name
    )

    suggestion_prompt = f"""You are a game prompt debugger. A game called "{game_name}" has recurring checker failures across multiple transcripts.

## Failure Patterns

{failure_summary}

## Current Manager Prompt (manager.md)

{manager_prompt}

## Current Player Prompt (player.md)

{player_prompt}

## Current Opening Instruction (config.toml)

{opening_instruction}

## Task

Based on the failure patterns, suggest specific edits to the manager prompt, player prompt, or opening instruction that would fix the recurring issues. For each suggestion:
1. State which file to edit (manager.md, player.md, or config.toml)
2. Quote the relevant section that needs to change
3. Provide the suggested replacement text
4. Explain why this fix addresses the failure pattern

Be concrete and actionable. Do not suggest changes unrelated to the observed failures."""

    console.print("\n[bold]Generating suggestions...[/bold]\n")

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": suggestion_prompt}],
            temperature=0.3,
        )
        suggestion = response.choices[0].message.content or ""
        console.print(Panel(suggestion, title="Suggested Fixes"))

        usage = response.usage
        if usage:
            console.print(
                f"\nSuggestion tokens: {usage.prompt_tokens} input, "
                f"{usage.completion_tokens} output"
            )
    except Exception as e:
        console.print(f"[yellow]Could not generate suggestions: {e}[/yellow]")


if __name__ == "__main__":
    app()
