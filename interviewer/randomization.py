from __future__ import annotations

import itertools
import math
import re
from copy import deepcopy
from random import Random
from typing import Any

from .models import GameConfig, VariableDefinition


def _topo_sort_derived(variables: dict[str, VariableDefinition]) -> list[str]:
    """Return derived variable names in topological order (dependencies first).

    Raises ValueError on circular dependencies.
    """
    derived = {n: v for n, v in variables.items() if v.type == "derived"}
    if not derived:
        return []

    # Build dependency graph: which other variables does each derived var reference?
    all_var_names = set(variables.keys())
    deps: dict[str, set[str]] = {}
    for name, var in derived.items():
        # Find variable references in formula by checking which known var names appear
        refs = set()
        for other in all_var_names:
            if other != name and other in var.formula:
                refs.add(other)
        deps[name] = refs

    # Kahn's algorithm
    in_degree = {n: 0 for n in derived}
    for name, ref_set in deps.items():
        for r in ref_set:
            if r in in_degree:
                in_degree[name] += 1  # r is a derived var that must come before name

    # Actually recount properly: for each derived var, count how many of its deps are also derived
    in_degree = {n: 0 for n in derived}
    for name, ref_set in deps.items():
        for r in ref_set:
            if r in derived:
                in_degree[name] += 1

    queue = [n for n, d in in_degree.items() if d == 0]
    result = []
    while queue:
        queue.sort()  # deterministic order
        node = queue.pop(0)
        result.append(node)
        # Reduce in-degree for nodes that depend on this one
        for name, ref_set in deps.items():
            if node in ref_set and name in in_degree:
                in_degree[name] -= 1
                if in_degree[name] == 0:
                    queue.append(name)

    if len(result) != len(derived):
        remaining = set(derived.keys()) - set(result)
        raise ValueError(f"Circular dependency among derived variables: {remaining}")

    return result


def _eval_derived(
    formula: str, conditions: dict[str, Any], round_to: float | None,
) -> float | int:
    """Evaluate a derived variable formula safely."""
    safe_globals = {"__builtins__": {}, "abs": abs, "min": min, "max": max, "round": round}
    val = eval(formula, safe_globals, dict(conditions))
    if round_to is not None:
        val = round(val / round_to) * round_to
        # Clean up floating point: if round_to >= 1, return int
        if round_to >= 1.0 and val == int(val):
            val = int(val)
    return val


def _compute_derived(
    variables: dict[str, VariableDefinition], conditions: dict[str, Any],
) -> None:
    """Evaluate all derived variables and add them to conditions in-place."""
    order = _topo_sort_derived(variables)
    for name in order:
        var = variables[name]
        conditions[name] = _eval_derived(var.formula, conditions, var.round_to)


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
        # derived vars are computed after all base vars are drawn

    _compute_derived(variables, conditions)
    return conditions


def generate_factorial_design(
    variables: dict[str, VariableDefinition],
) -> list[dict[str, Any]]:
    """Generate full factorial crossing of all choice variables.

    Fixed variables get their constant value in every cell.
    Uniform variables are skipped (not discrete).
    Sequence variables use their values list as levels.
    Derived variables are computed after base variables are set.

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
        # derived is computed post-crossing

    if not varying:
        base = [dict(fixed_values)] if fixed_values else [{}]
    else:
        names = list(varying.keys())
        levels = [varying[n] for n in names]
        base = []
        for combo in itertools.product(*levels):
            cell = dict(fixed_values)
            for n, v in zip(names, combo):
                cell[n] = v
            base.append(cell)

    # Compute derived variables for each cell
    has_derived = any(v.type == "derived" for v in variables.values())
    if has_derived:
        for cell in base:
            _compute_derived(variables, cell)

    return base


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
