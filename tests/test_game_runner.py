"""Tests for GameRunner: game loading, parameter sampling, template rendering, extends resolution."""

from __future__ import annotations

import pytest

from interviewer.game_runner import DrawSpec, GameRunner, ParamDef, RealizedGame


# --- ParamDef / DrawSpec tests ---


def test_param_def_fixed_value():
    p = ParamDef(type="int", value=6)
    assert GameRunner._sample_param(p) == 6


def test_param_def_fixed_string():
    p = ParamDef(type="str", value="mug")
    assert GameRunner._sample_param(p) == "mug"


def test_param_def_uniform_draw():
    spec = DrawSpec(distribution="uniform", min=2.0, max=8.0, precision=2)
    p = ParamDef(type="float", draw=spec)
    for _ in range(50):
        val = GameRunner._sample_param(p)
        assert 2.0 <= val <= 8.0
        # Check precision: no more than 2 decimal places
        assert val == round(val, 2)


def test_param_def_uniform_int_draw():
    spec = DrawSpec(distribution="uniform_int", min=1, max=10)
    p = ParamDef(type="int", draw=spec)
    for _ in range(50):
        val = GameRunner._sample_param(p)
        assert isinstance(val, int)
        assert 1 <= val <= 10


def test_param_def_unknown_distribution():
    spec = DrawSpec(distribution="gaussian", min=0, max=1)
    p = ParamDef(type="float", draw=spec)
    with pytest.raises(ValueError, match="Unknown distribution"):
        GameRunner._sample_param(p)


def test_param_def_no_value_or_draw():
    p = ParamDef(type="float")
    with pytest.raises(ValueError, match="neither"):
        GameRunner._sample_param(p)


# --- GameRunner.load_game tests ---


def test_load_bargaining_game():
    game = GameRunner.load_game("prompts/bargaining")
    assert game.name == "Bargaining Game"
    assert "seller_value" in game.realized_params
    assert "buyer_value" in game.realized_params
    assert "num_rounds" in game.realized_params
    assert game.realized_params["num_rounds"] == 6
    assert game.realized_params["object_name"] == "mug"
    # Check seller_value is within range
    assert 2.0 <= game.realized_params["seller_value"] <= 8.0
    assert 5.0 <= game.realized_params["buyer_value"] <= 10.0
    # Check prompts are rendered (no leftover placeholders)
    assert "{seller_value" not in game.manager_config.system_prompt
    assert "{buyer_value" not in game.manager_config.system_prompt
    assert "{object_name" not in game.manager_config.system_prompt
    assert "{seller_value" not in game.player_config.system_prompt


def test_load_ultimatum_game():
    game = GameRunner.load_game("prompts/ultimatum")
    assert game.name == "Ultimatum Game"
    assert game.realized_params["pot"] == 100
    assert game.realized_params["num_rounds"] == 4
    assert "{pot" not in game.manager_config.system_prompt
    assert "{num_rounds" not in game.manager_config.system_prompt


def test_load_game_not_found():
    with pytest.raises(FileNotFoundError, match="Game folder not found"):
        GameRunner.load_game("prompts/nonexistent_game")


def test_load_game_no_yaml():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError, match="game.yaml not found"):
            GameRunner.load_game(tmpdir)


# --- Extends resolution tests ---


def test_load_bargaining_wide_values():
    game = GameRunner.load_game("prompts/bargaining_wide_values")
    # Should inherit name from base
    assert game.name == "Bargaining Game"
    # Should use overridden value ranges
    assert game.realized_params["object_name"] == "mug"  # inherited
    assert game.realized_params["num_rounds"] == 6  # inherited
    # seller_value should be in wider range [1, 12]
    assert 1.0 <= game.realized_params["seller_value"] <= 12.0
    # buyer_value should be in wider range [8, 20]
    assert 8.0 <= game.realized_params["buyer_value"] <= 20.0
    # price_max overridden
    assert game.realized_params["price_max"] == 25.00


def test_extends_bad_base():
    import tempfile
    import os
    import yaml

    with tempfile.TemporaryDirectory() as tmpdir:
        game_yaml = os.path.join(tmpdir, "game.yaml")
        with open(game_yaml, "w") as f:
            yaml.dump({"extends": "nonexistent_base", "parameters": {}}, f)
        with pytest.raises(FileNotFoundError, match="Extended game folder not found"):
            GameRunner.load_game(tmpdir)


# --- Param overrides tests ---


def test_param_overrides():
    game = GameRunner.load_game(
        "prompts/bargaining",
        param_overrides={"seller_value": 5.55, "buyer_value": 9.99},
    )
    assert game.realized_params["seller_value"] == 5.55
    assert game.realized_params["buyer_value"] == 9.99
    # Prompts should use overridden values
    assert "5.55" in game.manager_config.system_prompt
    assert "9.99" in game.manager_config.system_prompt


# --- Template rendering tests ---


def test_rendered_prompt_contains_game_manager_label():
    game = GameRunner.load_game("prompts/bargaining")
    assert "GAME MANAGER" in game.manager_config.system_prompt
    assert "AI Player" in game.manager_config.system_prompt


def test_rendered_ultimatum_contains_pot():
    game = GameRunner.load_game("prompts/ultimatum")
    assert "$100" in game.manager_config.system_prompt
    assert "$100" in game.player_config.system_prompt


# --- RealizedGame model tests ---


def test_realized_game_model():
    from interviewer.models import AgentConfig

    game = RealizedGame(
        name="Test",
        manager_config=AgentConfig(system_prompt="mgr"),
        player_config=AgentConfig(system_prompt="plr"),
        realized_params={"x": 1},
    )
    assert game.name == "Test"
    assert game.realized_params["x"] == 1


# --- list_games tests ---


def test_list_games():
    games = GameRunner.list_games("prompts")
    names = [g["name"] for g in games]
    assert "Bargaining Game" in names
    assert "Ultimatum Game" in names


def test_list_games_empty():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        games = GameRunner.list_games(tmpdir)
        assert games == []
