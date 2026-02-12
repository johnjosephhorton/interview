from __future__ import annotations

import itertools
import re
from copy import deepcopy
from random import Random
from typing import Any

from .models import GameConfig, VariableDefinition


def draw_conditions(
    variables: dict[str, VariableDefinition],
    sim_index: int,
    rng: Random,
) -> dict[str, Any]:
    """Sample one condition set from variable definitions.

    Args:
        variables: Variable name -> definition mapping.
        sim_index: Index of the current simulation (used for "sequence" type).
        rng: Seeded Random instance for reproducibility.

    Returns:
        Dict mapping variable names to their drawn values.
    """
    conditions: dict[str, Any] = {}
    for name, var in variables.items():
        if var.type == "fixed":
            conditions[name] = var.value
        elif var.type == "choice":
            conditions[name] = rng.choice(var.values)
        elif var.type == "uniform":
            conditions[name] = rng.uniform(var.min, var.max)
        elif var.type == "sequence":
            conditions[name] = var.values[sim_index % len(var.values)]
    return conditions


def generate_factorial_design(
    variables: dict[str, VariableDefinition],
) -> list[dict[str, Any]]:
    """Generate full factorial crossing of all choice variables.

    Fixed variables get their constant value in every cell.
    Uniform variables are skipped (not discrete).
    Sequence variables use their values list as levels.

    Returns:
        List of condition dicts, one per factorial cell.
    """
    fixed_values: dict[str, Any] = {}
    varying: dict[str, list[Any]] = {}

    for name, var in variables.items():
        if var.type == "fixed":
            fixed_values[name] = var.value
        elif var.type in ("choice", "sequence"):
            varying[name] = var.values
        # uniform is skipped — not discrete

    if not varying:
        return [dict(fixed_values)] if fixed_values else [{}]

    names = list(varying.keys())
    levels = [varying[n] for n in names]
    cells = []
    for combo in itertools.product(*levels):
        cell = dict(fixed_values)
        for n, v in zip(names, combo):
            cell[n] = v
        cells.append(cell)
    return cells


def substitute_template(text: str, conditions: dict[str, Any]) -> str:
    """Replace {{var_name}} placeholders with condition values.

    Floats are formatted to 2 decimal places. Unresolved placeholders are left as-is.
    """
    def _replacer(match: re.Match) -> str:
        key = match.group(1).strip()
        if key not in conditions:
            return match.group(0)  # leave unresolved
        val = conditions[key]
        if isinstance(val, float):
            return f"{val:.2f}"
        return str(val)

    return re.sub(r"\{\{(\s*[\w]+\s*)\}\}", _replacer, text)


def apply_conditions_to_game_config(
    game_config: GameConfig,
    conditions: dict[str, Any],
) -> GameConfig:
    """Return a new GameConfig with all prompt fields template-substituted."""
    gc = deepcopy(game_config)
    gc.interviewer_system_prompt = substitute_template(
        gc.interviewer_system_prompt, conditions
    )
    gc.respondent_system_prompt = substitute_template(
        gc.respondent_system_prompt, conditions
    )
    if gc.player_system_prompt is not None:
        gc.player_system_prompt = substitute_template(
            gc.player_system_prompt, conditions
        )
    gc.opening_instruction = substitute_template(gc.opening_instruction, conditions)
    gc.last_question_response = substitute_template(gc.last_question_response, conditions)
    gc.end_of_session_response = substitute_template(gc.end_of_session_response, conditions)
    return gc
