"""Tests for TranscriptChecker (model construction, formatting, prompt building — no real API calls)."""

import os

import pytest

from interviewer.checker import TranscriptChecker
from interviewer.models import CheckResult, CriterionResult, Message


@pytest.fixture
def checker():
    return TranscriptChecker(api_key="sk-test-dummy")


def test_constructor_defaults():
    c = TranscriptChecker(api_key="sk-test-dummy")
    assert c._api_key == "sk-test-dummy"
    assert c.model == "gpt-4o"


def test_constructor_custom_model():
    c = TranscriptChecker(api_key="sk-test-dummy", model="gpt-5")
    assert c.model == "gpt-5"


def test_api_key_missing_raises():
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="API key required"):
            TranscriptChecker(api_key=None)
    finally:
        if old:
            os.environ["OPENAI_API_KEY"] = old


def test_format_transcript_basic(checker):
    messages = [
        Message(role="interviewer", text="Welcome to the game."),
        Message(role="respondent", text="I bid $10."),
        Message(role="interviewer", text="Round 1 results..."),
        Message(role="respondent", text="I bid $15."),
    ]
    result = checker._format_transcript(messages)

    assert "[Turn 1] MANAGER: Welcome to the game." in result
    assert "[Turn 1] HUMAN: I bid $10." in result
    assert "[Turn 2] MANAGER: Round 1 results..." in result
    assert "[Turn 2] HUMAN: I bid $15." in result


def test_format_transcript_empty(checker):
    assert checker._format_transcript([]) == ""


def test_format_transcript_manager_only(checker):
    messages = [
        Message(role="interviewer", text="Hello"),
        Message(role="interviewer", text="Goodbye"),
    ]
    result = checker._format_transcript(messages)
    assert "[Turn 1] MANAGER: Hello" in result
    assert "[Turn 2] MANAGER: Goodbye" in result


def test_load_game_prompts_bargainer(checker):
    manager, player, opening_instruction = checker._load_game_prompts("bargainer")
    assert len(manager) > 0
    assert len(player) > 0
    assert "game manager" in manager.lower() or "manager" in manager.lower()
    assert len(opening_instruction) > 0


def test_load_game_prompts_not_found(checker):
    with pytest.raises(ValueError, match="Game not found"):
        checker._load_game_prompts("nonexistent_game_xyz")


def test_build_prompt_contains_sections(checker):
    messages = [
        Message(role="interviewer", text="Welcome!"),
        Message(role="respondent", text="Thanks."),
    ]
    prompt = checker._build_prompt("bargainer", messages)

    # Should contain the template sections
    assert "Manager Instructions" in prompt
    assert "AI Player Strategy" in prompt
    assert "Opening Instruction" in prompt
    assert "Transcript" in prompt
    # Should contain the formatted transcript
    assert "[Turn 1] MANAGER: Welcome!" in prompt
    assert "[Turn 1] HUMAN: Thanks." in prompt


def test_load_game_prompts_opening_instruction(checker):
    _, _, opening_instruction = checker._load_game_prompts("pd_rep")
    assert "cooperate" in opening_instruction.lower() or "COOPERATE" in opening_instruction
    assert "defect" in opening_instruction.lower() or "DEFECT" in opening_instruction


def test_criterion_result_model():
    cr = CriterionResult(
        criterion="arithmetic_correctness",
        passed=True,
        explanation="All calculations verified.",
    )
    assert cr.criterion == "arithmetic_correctness"
    assert cr.passed is True


def test_check_result_model():
    criteria = [
        CriterionResult(criterion="arithmetic_correctness", passed=True, explanation="ok"),
        CriterionResult(criterion="running_total_consistency", passed=False, explanation="mismatch"),
    ]
    result = CheckResult(
        game_name="bargainer",
        transcript_summary="A 5-round bargaining game.",
        criteria=criteria,
        overall_passed=False,
        checker_model="gpt-4o",
        input_tokens=1000,
        output_tokens=200,
    )
    assert result.game_name == "bargainer"
    assert result.overall_passed is False
    assert len(result.criteria) == 2
    assert result.input_tokens == 1000


def test_check_result_defaults():
    result = CheckResult(
        game_name="test",
        transcript_summary="summary",
        criteria=[],
        overall_passed=True,
        checker_model="gpt-4o",
    )
    assert result.input_tokens == 0
    assert result.output_tokens == 0
