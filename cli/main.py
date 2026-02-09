from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from interviewer import (
    DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
    DEFAULT_MODEL,
    DEFAULT_RESPONDENT_SYSTEM_PROMPT,
    AgentConfig,
    Interviewer,
    Message,
    Simulation,
    load_prompt,
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
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Sampling temperature"),
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
    temperature: float = typer.Option(0.7, "--temperature", "-t"),
    max_tokens: int = typer.Option(200, "--max-tokens"),
    max_turns: int = typer.Option(5, "--max-turns", help="Number of conversation turns"),
    save: Optional[str] = typer.Option(None, "--save", help="Save transcript to file"),
):
    """Fully automated simulation — both sides are AI."""
    asyncio.run(
        _simulate(
            interviewer_prompt, respondent_prompt, model, temperature, max_tokens, max_turns, save
        )
    )


async def _simulate(
    interviewer_prompt: str,
    respondent_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    save_path: str | None,
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

    sim = Simulation()
    transcript = await sim.run(
        interviewer_config, respondent_config, max_turns=max_turns, on_message=on_message
    )

    if save_path:
        fmt = "csv" if save_path.endswith(".csv") else "json"
        save_transcript(transcript, save_path, format=fmt)
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
