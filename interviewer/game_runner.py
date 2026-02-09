"""Config-driven game loading: read game.yaml, sample parameters, render prompt templates."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .models import AgentConfig


class DrawSpec(BaseModel):
    """Distribution specification for a randomized parameter."""

    distribution: str  # "uniform", "uniform_int"
    min: float = 0
    max: float = 1
    precision: int = 2


class ParamDef(BaseModel):
    """A single parameter definition from game.yaml."""

    description: str = ""
    type: str = "float"  # "float", "int", "str"
    value: Any | None = None  # fixed value
    draw: DrawSpec | None = None  # distribution spec


class GameConfig(BaseModel):
    """Parsed game.yaml — metadata + parameter definitions."""

    name: str = ""
    description: str = ""
    extends: str | None = None
    parameters: dict[str, ParamDef] = Field(default_factory=dict)


class RealizedGame(BaseModel):
    """A game with all parameters sampled and prompts rendered."""

    name: str
    description: str = ""
    manager_config: AgentConfig
    player_config: AgentConfig
    realized_params: dict[str, Any] = Field(default_factory=dict)
    human_instructions: str = ""


class GameRunner:
    """Loads game definitions, samples parameters, and renders prompt templates."""

    @staticmethod
    def load_game(
        game_path: str,
        param_overrides: dict[str, Any] | None = None,
    ) -> RealizedGame:
        """Load game.yaml, resolve extends, sample params, render templates.

        Args:
            game_path: Path to the game folder (containing game.yaml, manager.md, player.md).
            param_overrides: Optional dict of parameter values to override after sampling.

        Returns:
            RealizedGame with fully rendered AgentConfigs and realized parameter values.
        """
        game_dir = Path(game_path)
        if not game_dir.is_dir():
            raise FileNotFoundError(f"Game folder not found: {game_path}")

        yaml_path = game_dir / "game.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"game.yaml not found in {game_path}")

        with open(yaml_path) as f:
            raw = yaml.safe_load(f)

        # Resolve extends chain
        resolved = GameRunner._resolve_extends(raw, game_dir)
        config = GameRunner._parse_config(resolved)

        # Find prompt templates (walk up extends chain if needed)
        manager_template = GameRunner._find_template("manager.md", game_dir, resolved)
        player_template = GameRunner._find_template("player.md", game_dir, resolved)

        # Human instructions are optional
        try:
            human_template = GameRunner._find_template("human.md", game_dir, resolved)
        except FileNotFoundError:
            human_template = None

        # Sample parameters
        realized_params: dict[str, Any] = {}
        for name, param_def in config.parameters.items():
            realized_params[name] = GameRunner._sample_param(param_def)

        # Apply overrides
        if param_overrides:
            for key, val in param_overrides.items():
                if key in config.parameters:
                    realized_params[key] = val

        # Render templates
        manager_prompt = manager_template.format(**realized_params)
        player_prompt = player_template.format(**realized_params)
        human_instructions = human_template.format(**realized_params) if human_template else ""

        return RealizedGame(
            name=config.name,
            description=config.description,
            manager_config=AgentConfig(system_prompt=manager_prompt),
            player_config=AgentConfig(system_prompt=player_prompt),
            realized_params=realized_params,
            human_instructions=human_instructions,
        )

    @staticmethod
    def _parse_config(raw: dict) -> GameConfig:
        """Parse a resolved (merged) YAML dict into a GameConfig."""
        params = {}
        for name, pdef in raw.get("parameters", {}).items():
            if isinstance(pdef, dict):
                draw_raw = pdef.get("draw")
                draw = DrawSpec(**draw_raw) if draw_raw else None
                params[name] = ParamDef(
                    description=pdef.get("description", ""),
                    type=pdef.get("type", "float"),
                    value=pdef.get("value"),
                    draw=draw,
                )
            else:
                # Bare value shorthand
                params[name] = ParamDef(value=pdef)

        return GameConfig(
            name=raw.get("name", ""),
            description=raw.get("description", ""),
            extends=raw.get("extends"),
            parameters=params,
        )

    @staticmethod
    def _sample_param(param_def: ParamDef) -> Any:
        """Sample a value from a parameter definition."""
        if param_def.draw is not None:
            spec = param_def.draw
            if spec.distribution == "uniform":
                val = random.uniform(spec.min, spec.max)
                return round(val, spec.precision)
            elif spec.distribution == "uniform_int":
                return random.randint(int(spec.min), int(spec.max))
            else:
                raise ValueError(f"Unknown distribution: {spec.distribution}")

        if param_def.value is not None:
            return param_def.value

        raise ValueError(f"Parameter has neither 'value' nor 'draw': {param_def}")

    @staticmethod
    def _resolve_extends(raw: dict, game_dir: Path) -> dict:
        """Recursively resolve extends chain, merging parameters."""
        extends = raw.get("extends")
        if not extends:
            return raw

        # Resolve base game folder relative to the prompts root
        prompts_root = game_dir.parent
        base_dir = prompts_root / extends

        if not base_dir.is_dir():
            raise FileNotFoundError(
                f"Extended game folder not found: {base_dir} (from extends: {extends})"
            )

        base_yaml_path = base_dir / "game.yaml"
        if not base_yaml_path.exists():
            raise FileNotFoundError(f"game.yaml not found in base game: {base_dir}")

        with open(base_yaml_path) as f:
            base_raw = yaml.safe_load(f)

        # Recursively resolve the base
        base_resolved = GameRunner._resolve_extends(base_raw, base_dir)

        # Merge: base first, then overlay current
        merged = dict(base_resolved)

        # Overlay top-level non-parameter fields
        for key in ("name", "description"):
            if key in raw:
                merged[key] = raw[key]

        # Deep-merge parameters
        base_params = dict(merged.get("parameters", {}))
        override_params = raw.get("parameters", {})
        for param_name, param_override in override_params.items():
            if param_name in base_params and isinstance(param_override, dict):
                # Merge into existing param def
                base_param = dict(base_params[param_name])
                base_param.update(param_override)
                base_params[param_name] = base_param
            else:
                base_params[param_name] = param_override
        merged["parameters"] = base_params

        # Preserve extends info for template resolution
        merged["_base_dir"] = str(base_dir)

        return merged

    @staticmethod
    def _find_template(filename: str, game_dir: Path, resolved: dict) -> str:
        """Find and read a prompt template, checking current dir then base dirs."""
        # Check current game directory first
        path = game_dir / filename
        if path.exists():
            return path.read_text().strip()

        # Check base directory from extends resolution
        base_dir_str = resolved.get("_base_dir")
        if base_dir_str:
            base_path = Path(base_dir_str) / filename
            if base_path.exists():
                return base_path.read_text().strip()

        raise FileNotFoundError(
            f"Template {filename} not found in {game_dir} or any base game folder"
        )

    @staticmethod
    def list_games(prompts_root: str = "prompts") -> list[dict[str, str]]:
        """List all available game folders under the prompts root.

        Returns:
            List of dicts with 'path', 'name', and 'description' for each game.
        """
        root = Path(prompts_root)
        games = []
        if not root.is_dir():
            return games

        for child in sorted(root.iterdir()):
            yaml_path = child / "game.yaml"
            if child.is_dir() and yaml_path.exists():
                with open(yaml_path) as f:
                    raw = yaml.safe_load(f)
                games.append({
                    "path": str(child),
                    "name": raw.get("name", child.name),
                    "description": raw.get("description", ""),
                })
        return games
