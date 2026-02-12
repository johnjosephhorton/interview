"""Tests for the randomization module."""

from random import Random

from interviewer.models import GameConfig, VariableDefinition
from interviewer.randomization import (
    apply_conditions_to_game_config,
    draw_conditions,
    generate_factorial_design,
    substitute_template,
)


def _make_variables(**kwargs) -> dict[str, VariableDefinition]:
    return {k: VariableDefinition(**v) for k, v in kwargs.items()}


def test_draw_conditions_choice():
    variables = _make_variables(color={"type": "choice", "values": ["red", "blue", "green"]})
    rng = Random(42)
    result = draw_conditions(variables, 0, rng)
    assert result["color"] in ["red", "blue", "green"]


def test_draw_conditions_uniform():
    variables = _make_variables(price={"type": "uniform", "min": 1.0, "max": 10.0})
    rng = Random(42)
    result = draw_conditions(variables, 0, rng)
    assert 1.0 <= result["price"] <= 10.0


def test_draw_conditions_fixed():
    variables = _make_variables(valuation={"type": "fixed", "value": 8.0})
    rng = Random(42)
    result = draw_conditions(variables, 0, rng)
    assert result["valuation"] == 8.0


def test_draw_conditions_sequence():
    variables = _make_variables(
        treatment={"type": "sequence", "values": ["control", "treatment_a", "treatment_b"]}
    )
    rng = Random(42)
    assert draw_conditions(variables, 0, rng)["treatment"] == "control"
    assert draw_conditions(variables, 1, rng)["treatment"] == "treatment_a"
    assert draw_conditions(variables, 2, rng)["treatment"] == "treatment_b"
    assert draw_conditions(variables, 3, rng)["treatment"] == "control"  # wraps


def test_substitute_template():
    text = "The price is ${{price}} and color is {{color}}."
    conditions = {"price": 6.50, "color": "red"}
    result = substitute_template(text, conditions)
    assert result == "The price is $6.50 and color is red."


def test_substitute_template_no_match():
    text = "The value is {{unknown_var}}."
    conditions = {"price": 5.0}
    result = substitute_template(text, conditions)
    assert result == "The value is {{unknown_var}}."


def test_substitute_template_int():
    text = "Round {{round_num}} of the game."
    conditions = {"round_num": 3}
    result = substitute_template(text, conditions)
    assert result == "Round 3 of the game."


def test_substitute_template_whitespace_in_placeholder():
    text = "Value: {{ price }}."
    conditions = {"price": 4.00}
    result = substitute_template(text, conditions)
    assert result == "Value: 4.00."


def test_apply_conditions_to_game_config():
    gc = GameConfig(
        name="Test",
        interviewer_system_prompt="AI valuation: ${{ai_val}}",
        respondent_system_prompt="Human valuation: ${{human_val}}",
        player_system_prompt="Player sees ${{ai_val}}",
        opening_instruction="Start with {{ai_val}}",
        last_question_response="Final at ${{ai_val}}",
        end_of_session_response="Done with {{human_val}}",
    )
    conditions = {"ai_val": 6.0, "human_val": 8.0}
    result = apply_conditions_to_game_config(gc, conditions)

    assert result.interviewer_system_prompt == "AI valuation: $6.00"
    assert result.respondent_system_prompt == "Human valuation: $8.00"
    assert result.player_system_prompt == "Player sees $6.00"
    assert result.opening_instruction == "Start with 6.00"
    assert result.last_question_response == "Final at $6.00"
    assert result.end_of_session_response == "Done with 8.00"
    # Original should be unmodified
    assert gc.interviewer_system_prompt == "AI valuation: ${{ai_val}}"


def test_apply_conditions_no_player_prompt():
    gc = GameConfig(
        name="Test",
        interviewer_system_prompt="Val: {{x}}",
        respondent_system_prompt="Resp: {{x}}",
        player_system_prompt=None,
        opening_instruction="open",
        last_question_response="last",
        end_of_session_response="end",
    )
    conditions = {"x": 5.0}
    result = apply_conditions_to_game_config(gc, conditions)
    assert result.interviewer_system_prompt == "Val: 5.00"
    assert result.player_system_prompt is None


def test_generate_factorial_design():
    variables = _make_variables(
        color={"type": "choice", "values": ["red", "blue"]},
        size={"type": "choice", "values": ["S", "M", "L"]},
        constant={"type": "fixed", "value": 42},
    )
    cells = generate_factorial_design(variables)
    assert len(cells) == 6  # 2 x 3
    # Every cell should have the fixed value
    for cell in cells:
        assert cell["constant"] == 42
    # Check all combinations exist
    combos = {(c["color"], c["size"]) for c in cells}
    assert combos == {("red", "S"), ("red", "M"), ("red", "L"), ("blue", "S"), ("blue", "M"), ("blue", "L")}


def test_generate_factorial_design_no_varying():
    variables = _make_variables(x={"type": "fixed", "value": 1})
    cells = generate_factorial_design(variables)
    assert cells == [{"x": 1}]


def test_generate_factorial_design_empty():
    cells = generate_factorial_design({})
    assert cells == [{}]


def test_generate_factorial_design_sequence_as_levels():
    variables = _make_variables(
        t={"type": "sequence", "values": ["A", "B"]},
        v={"type": "choice", "values": [1, 2]},
    )
    cells = generate_factorial_design(variables)
    assert len(cells) == 4  # 2 x 2


def test_seed_reproducibility():
    variables = _make_variables(
        val={"type": "choice", "values": [1, 2, 3, 4, 5]},
        price={"type": "uniform", "min": 0.0, "max": 100.0},
    )
    draws_a = [draw_conditions(variables, i, Random(42)) for i in range(10)]
    draws_b = [draw_conditions(variables, i, Random(42)) for i in range(10)]
    assert draws_a == draws_b


def test_variable_definition_model():
    v = VariableDefinition(type="choice", values=[1, 2, 3])
    assert v.type == "choice"
    assert v.values == [1, 2, 3]

    v2 = VariableDefinition(type="fixed", value="hello")
    assert v2.value == "hello"

    v3 = VariableDefinition(type="uniform", min=0.0, max=1.0)
    assert v3.min == 0.0
    assert v3.max == 1.0


def test_game_config_variables_default():
    gc = GameConfig(
        name="Test",
        interviewer_system_prompt="p",
        respondent_system_prompt="r",
        opening_instruction="o",
        last_question_response="l",
        end_of_session_response="e",
    )
    assert gc.variables == {}


def test_transcript_conditions_default():
    from interviewer.models import Transcript
    t = Transcript()
    assert t.conditions == {}


# --- Derived variable tests ---


def test_derived_from_choice():
    """Derived variable computed from a choice variable."""
    variables = _make_variables(
        base={"type": "choice", "values": [40]},
        derived={"type": "derived", "formula": "base + 10"},
    )
    rng = Random(42)
    result = draw_conditions(variables, 0, rng)
    assert result["base"] == 40
    assert result["derived"] == 50


def test_derived_chain():
    """Derived variable that depends on another derived variable."""
    variables = _make_variables(
        x={"type": "fixed", "value": 10},
        y={"type": "derived", "formula": "x * 2"},
        z={"type": "derived", "formula": "y + 5"},
    )
    rng = Random(42)
    result = draw_conditions(variables, 0, rng)
    assert result["x"] == 10
    assert result["y"] == 20
    assert result["z"] == 25


def test_derived_round_to():
    """Derived variable with round_to applied."""
    variables = _make_variables(
        cost={"type": "fixed", "value": 40},
        value={"type": "fixed", "value": 70},
        opening={"type": "derived", "formula": "cost + 0.7 * (value - cost)", "round_to": 1.0},
    )
    rng = Random(42)
    result = draw_conditions(variables, 0, rng)
    # 40 + 0.7 * 30 = 61.0
    assert result["opening"] == 61


def test_derived_round_to_decimal():
    """Derived variable with fractional round_to."""
    variables = _make_variables(
        m={"type": "fixed", "value": 1.6},
        mpcr={"type": "derived", "formula": "m / 2", "round_to": 0.01},
    )
    rng = Random(42)
    result = draw_conditions(variables, 0, rng)
    assert result["mpcr"] == 0.8


def test_factorial_computes_derived():
    """Factorial design computes derived variables for each cell."""
    variables = _make_variables(
        a={"type": "choice", "values": [10, 20]},
        b={"type": "choice", "values": [3, 5]},
        ab={"type": "derived", "formula": "a * b"},
    )
    cells = generate_factorial_design(variables)
    assert len(cells) == 4  # 2 x 2 (derived not crossed)
    products = {c["ab"] for c in cells}
    assert products == {30, 50, 60, 100}


def test_factorial_does_not_cross_derived():
    """Derived variables are NOT part of the factorial crossing."""
    variables = _make_variables(
        x={"type": "choice", "values": [1, 2]},
        d={"type": "derived", "formula": "x * 10"},
    )
    cells = generate_factorial_design(variables)
    assert len(cells) == 2  # only 2 cells (from x), not 2*N


def test_derived_circular_dependency():
    """Circular dependency among derived variables raises ValueError."""
    import pytest
    variables = _make_variables(
        a={"type": "derived", "formula": "b + 1"},
        b={"type": "derived", "formula": "a + 1"},
    )
    with pytest.raises(ValueError, match="Circular dependency"):
        draw_conditions(variables, 0, Random(42))


def test_variable_definition_derived():
    """VariableDefinition accepts 'derived' type with formula and round_to."""
    v = VariableDefinition(type="derived", formula="x * 2", round_to=0.5)
    assert v.type == "derived"
    assert v.formula == "x * 2"
    assert v.round_to == 0.5


def test_game_config_respondent_temperature():
    """GameConfig has an optional respondent_temperature field."""
    gc = GameConfig(
        name="Test",
        interviewer_system_prompt="p",
        respondent_system_prompt="r",
        opening_instruction="o",
        last_question_response="l",
        end_of_session_response="e",
        respondent_temperature=0.0,
    )
    assert gc.respondent_temperature == 0.0

    gc2 = GameConfig(
        name="Test",
        interviewer_system_prompt="p",
        respondent_system_prompt="r",
        opening_instruction="o",
        last_question_response="l",
        end_of_session_response="e",
    )
    assert gc2.respondent_temperature is None
