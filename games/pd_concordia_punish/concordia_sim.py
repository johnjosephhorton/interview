#!/usr/bin/env python3
"""
Concordia-based simulation for the Repeated Prisoner's Dilemma with Costly Punishment.

Each round has two stages:
  1. PD stage: both choose COOPERATE or DEFECT (CC=3/3, CD=0/5, DC=5/0, DD=1/1)
  2. Punishment stage: both choose PUNISH or NO_PUNISH (cost $1 to punisher, -$3 to target)

Usage:
    python concordia_sim.py --seed 42 -n 1 -v
    python concordia_sim.py -n 10 -j 8 --model gpt-4o-mini
    python concordia_sim.py -n 5 --seed 42 -o results.json -v
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from random import Random

from dotenv import load_dotenv
load_dotenv()

import numpy as np

from concordia.associative_memory.basic_associative_memory import (
    AssociativeMemoryBank,
)
from concordia.contrib.language_models.openai import base_gpt_model
from concordia.contrib.language_models.openai.gpt_model import GptLanguageModel
from concordia.prefabs.entity.rational import Entity as RationalEntity
from concordia.typing.entity import ActionSpec, OutputType


def _patch_concordia_for_non_reasoning_models():
    """Patch Concordia's GPT wrapper to drop unsupported parameters.

    Concordia v2.3 sends `reasoning_effort` and `verbosity` to the OpenAI API,
    which are only supported by reasoning models (o-series / GPT-5). For
    standard models (gpt-4o-mini, gpt-4o, etc.) we strip these parameters.
    """
    def _patched(self, prompt, reasoning_effort, verbosity, **kwargs):
        messages = [{"role": "user", "content": prompt}]
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 2048),
            temperature=kwargs.get("temperature", 1.0),
            seed=kwargs.get("seed"),
        )
        return response.choices[0].message.content

    base_gpt_model.BaseGPTModel._sample_text = _patched


_patch_concordia_for_non_reasoning_models()

# Add project root so we can import interviewer
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from interviewer.concordia_parallel import parallel_map_ordered, resolve_worker_count


def _embedder(text: str) -> np.ndarray:
    """Dummy embedder -- semantic search not needed for structured games."""
    return np.zeros(16)


# -- Payoff matrix constants --------------------------------------------------
PAYOFF = {
    "cooperate": {"cooperate": 3, "defect": 0},
    "defect": {"cooperate": 5, "defect": 1},
}

PUNISH_COST = 1    # cost to the punisher
PUNISH_DAMAGE = 3  # reduction to the target's earnings


# -- Section 1: Action Parsers ------------------------------------------------

def _parse_pd_action(text: str) -> str:
    """Parse agent output into 'cooperate', 'defect', or 'invalid'."""
    cleaned = text.strip().lower()
    for prefix in ("player a ", "player b "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]

    if re.search(r"\bcooperate\b", cleaned):
        if not re.search(r"\bdefect\b", cleaned):
            return "cooperate"
    if cleaned in ("c", "coop", "co-operate"):
        return "cooperate"

    if re.search(r"\bdefect\b", cleaned):
        if not re.search(r"\bcooperate\b", cleaned):
            return "defect"
    if cleaned in ("d", "def"):
        return "defect"

    return "invalid"


def _parse_punish_action(text: str) -> str:
    """Parse agent output into 'punish', 'no_punish', or 'invalid'."""
    cleaned = text.strip().lower()
    for prefix in ("player a ", "player b "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]

    # Check for "no punish" / "no_punish" / "don't punish" first (before "punish")
    if re.search(r"\bno[_ ]?punish\b", cleaned) or re.search(r"\bdon'?t punish\b", cleaned):
        return "no_punish"
    if cleaned in ("no", "n", "no punish", "no_punish", "don't punish", "skip"):
        return "no_punish"

    if re.search(r"\bpunish\b", cleaned):
        return "punish"
    if cleaned in ("p", "yes", "y"):
        return "punish"

    return "invalid"


# -- Section 2: Agent Factory --------------------------------------------------

def _build_agent(model: GptLanguageModel, name: str, goal: str) -> object:
    """Build a Concordia RationalEntity agent."""
    prefab = RationalEntity()
    prefab.params = {
        "name": name,
        "goal": goal,
        "randomize_choices": False,
        "prefix_entity_name": True,
    }
    memory = AssociativeMemoryBank(sentence_embedder=_embedder)
    return prefab.build(model=model, memory_bank=memory)


# -- Section 3: Game Loop -----------------------------------------------------

MAX_ROUNDS = 10

GOAL_TEMPLATE = (
    "You are {name} in a 10-round Repeated Prisoner's Dilemma WITH PUNISHMENT. "
    "Each round has TWO stages: "
    "STAGE 1 (PD): Both players simultaneously choose COOPERATE or DEFECT. "
    "Payoffs: Both cooperate -> each earns $3. Both defect -> each earns $1. "
    "You defect and they cooperate -> you earn $5, they earn $0. "
    "You cooperate and they defect -> you earn $0, they earn $5. "
    "STAGE 2 (PUNISHMENT): After seeing the Stage 1 outcome, both players "
    "simultaneously choose PUNISH or NO_PUNISH. "
    "If you PUNISH: you pay $1 and the other player loses $3 from their round earnings. "
    "If you choose NO_PUNISH: nothing happens. "
    "Round earnings can go negative. "
    "Your goal is to maximize YOUR total earnings over all 10 rounds. "
    "You must choose exactly COOPERATE or DEFECT in Stage 1, "
    "and exactly PUNISH or NO_PUNISH in Stage 2."
)


def run_game(
    model: GptLanguageModel,
    max_rounds: int = MAX_ROUNDS,
    rng: Random | None = None,
    verbose: bool = False,
) -> dict:
    """Run one PD+Punishment game using Concordia agents.

    Returns:
        Dict with per-round history, total earnings, cooperation rates, punishment rates.
    """
    # --- Build agents ---
    agent_a = _build_agent(
        model,
        name="Player A",
        goal=GOAL_TEMPLATE.format(name="Player A"),
    )
    agent_b = _build_agent(
        model,
        name="Player B",
        goal=GOAL_TEMPLATE.format(name="Player B"),
    )

    # --- Seed initial observations (role-relative) ---
    intro = (
        "You are about to play a 10-round Prisoner's Dilemma WITH PUNISHMENT against another player. "
        "Each round has two stages. "
        "Stage 1: You both simultaneously choose COOPERATE or DEFECT. "
        "Payoffs: Both cooperate = $3 each. Both defect = $1 each. "
        "You defect while they cooperate = you get $5, they get $0. "
        "You cooperate while they defect = you get $0, they get $5. "
        "Stage 2: After seeing the Stage 1 result, you both simultaneously choose PUNISH or NO_PUNISH. "
        "Punishing costs you $1 and reduces the other player's round earnings by $3. "
        "Round earnings can go negative. Total earnings = sum over 10 rounds."
    )
    agent_a.observe(intro)
    agent_b.observe(intro)

    # --- Game loop ---
    history: list[dict] = []
    a_total = 0
    b_total = 0

    local_rng = rng or Random()
    for round_num in range(1, max_rounds + 1):
        final_str = " This is the FINAL round!" if round_num == max_rounds else ""

        # ── Stage 1: PD choice ──
        pd_call = (
            f"Round {round_num} of {max_rounds}, Stage 1 (PD).{final_str} "
            f"Choose your action. Reply with ONLY one word: COOPERATE or DEFECT."
        )
        pd_spec = ActionSpec(call_to_action=pd_call, output_type=OutputType.FREE)

        # Randomize act order
        a_first = local_rng.choice([True, False])
        if a_first:
            raw_a_pd = agent_a.act(pd_spec)
            raw_b_pd = agent_b.act(pd_spec)
        else:
            raw_b_pd = agent_b.act(pd_spec)
            raw_a_pd = agent_a.act(pd_spec)

        choice_a = _parse_pd_action(raw_a_pd)
        choice_b = _parse_pd_action(raw_b_pd)

        effective_a = choice_a if choice_a != "invalid" else "defect"
        effective_b = choice_b if choice_b != "invalid" else "defect"

        # PD payoffs (before punishment)
        a_pd_earn = PAYOFF[effective_a][effective_b]
        b_pd_earn = PAYOFF[effective_b][effective_a]

        # Observe PD outcome (role-relative) before punishment decision
        pd_obs_a = (
            f"Round {round_num} Stage 1 result: "
            f"You chose {effective_a.upper()}. "
            f"The other player chose {effective_b.upper()}. "
            f"Your Stage 1 earnings: ${a_pd_earn}. Their Stage 1 earnings: ${b_pd_earn}."
        )
        pd_obs_b = (
            f"Round {round_num} Stage 1 result: "
            f"You chose {effective_b.upper()}. "
            f"The other player chose {effective_a.upper()}. "
            f"Your Stage 1 earnings: ${b_pd_earn}. Their Stage 1 earnings: ${a_pd_earn}."
        )
        agent_a.observe(pd_obs_a)
        agent_b.observe(pd_obs_b)

        # ── Stage 2: Punishment choice ──
        punish_call = (
            f"Round {round_num}, Stage 2 (Punishment). "
            f"You saw the Stage 1 outcome. "
            f"You may now PUNISH the other player (costs you $1, reduces their earnings by $3) "
            f"or choose NO_PUNISH. "
            f"Reply with ONLY: PUNISH or NO_PUNISH."
        )
        punish_spec = ActionSpec(call_to_action=punish_call, output_type=OutputType.FREE)

        # Randomize act order for punishment stage too
        a_first_p = local_rng.choice([True, False])
        if a_first_p:
            raw_a_p = agent_a.act(punish_spec)
            raw_b_p = agent_b.act(punish_spec)
        else:
            raw_b_p = agent_b.act(punish_spec)
            raw_a_p = agent_a.act(punish_spec)

        punish_a = _parse_punish_action(raw_a_p)
        punish_b = _parse_punish_action(raw_b_p)

        # Default invalid punishment actions to no_punish (conservative)
        eff_punish_a = punish_a if punish_a != "invalid" else "no_punish"
        eff_punish_b = punish_b if punish_b != "invalid" else "no_punish"

        # Compute final round earnings
        a_round_earn = a_pd_earn
        b_round_earn = b_pd_earn

        if eff_punish_a == "punish":
            a_round_earn -= PUNISH_COST
            b_round_earn -= PUNISH_DAMAGE
        if eff_punish_b == "punish":
            b_round_earn -= PUNISH_COST
            a_round_earn -= PUNISH_DAMAGE

        a_total += a_round_earn
        b_total += b_round_earn

        if verbose:
            inv_a = " [INV->defect]" if choice_a == "invalid" else ""
            inv_b = " [INV->defect]" if choice_b == "invalid" else ""
            inv_pa = " [INV->no_punish]" if punish_a == "invalid" else ""
            inv_pb = " [INV->no_punish]" if punish_b == "invalid" else ""
            print(
                f"  Round {round_num}: "
                f"A={effective_a}{inv_a}, B={effective_b}{inv_b} "
                f"| punish: A={eff_punish_a}{inv_pa}, B={eff_punish_b}{inv_pb} "
                f"-> A=${a_round_earn}, B=${b_round_earn} "
                f"(cum: A=${a_total}, B=${b_total})"
            )

        history.append({
            "round": round_num,
            "a_choice": effective_a,
            "b_choice": effective_b,
            "a_raw_pd": raw_a_pd,
            "b_raw_pd": raw_b_pd,
            "a_pd_invalid": choice_a == "invalid",
            "b_pd_invalid": choice_b == "invalid",
            "a_pd_earned": a_pd_earn,
            "b_pd_earned": b_pd_earn,
            "a_punish": eff_punish_a,
            "b_punish": eff_punish_b,
            "a_raw_punish": raw_a_p,
            "b_raw_punish": raw_b_p,
            "a_punish_invalid": punish_a == "invalid",
            "b_punish_invalid": punish_b == "invalid",
            "a_round_earned": a_round_earn,
            "b_round_earned": b_round_earn,
            "a_pd_acted_first": a_first,
            "a_punish_acted_first": a_first_p,
        })

        # Observe full round outcome (role-relative)
        punish_obs_a = (
            f"Round {round_num} final result: "
            f"You chose {eff_punish_a.upper().replace('_', ' ')}. "
            f"The other player chose {eff_punish_b.upper().replace('_', ' ')}. "
            f"Your round earnings: ${a_round_earn}. Their round earnings: ${b_round_earn}. "
            f"Your cumulative: ${a_total}. Their cumulative: ${b_total}."
        )
        punish_obs_b = (
            f"Round {round_num} final result: "
            f"You chose {eff_punish_b.upper().replace('_', ' ')}. "
            f"The other player chose {eff_punish_a.upper().replace('_', ' ')}. "
            f"Your round earnings: ${b_round_earn}. Their round earnings: ${a_round_earn}. "
            f"Your cumulative: ${b_total}. Their cumulative: ${a_total}."
        )
        agent_a.observe(punish_obs_a)
        agent_b.observe(punish_obs_b)

    # --- Compute summary stats ---
    a_coops = sum(1 for h in history if h["a_choice"] == "cooperate")
    b_coops = sum(1 for h in history if h["b_choice"] == "cooperate")
    mutual_coop = sum(
        1 for h in history
        if h["a_choice"] == "cooperate" and h["b_choice"] == "cooperate"
    )
    mutual_defect = sum(
        1 for h in history
        if h["a_choice"] == "defect" and h["b_choice"] == "defect"
    )
    a_punishments = sum(1 for h in history if h["a_punish"] == "punish")
    b_punishments = sum(1 for h in history if h["b_punish"] == "punish")

    return {
        "max_rounds": max_rounds,
        "rounds_played": len(history),
        "a_total_earnings": a_total,
        "b_total_earnings": b_total,
        "a_cooperation_rate": a_coops / max_rounds,
        "b_cooperation_rate": b_coops / max_rounds,
        "a_punishment_rate": a_punishments / max_rounds,
        "b_punishment_rate": b_punishments / max_rounds,
        "total_punishments": a_punishments + b_punishments,
        "mutual_cooperation_rounds": mutual_coop,
        "mutual_defection_rounds": mutual_defect,
        "joint_earnings": a_total + b_total,
        "max_joint_earnings": max_rounds * 6,
        "efficiency": (a_total + b_total) / (max_rounds * 6),
        "history": history,
    }


def _run_single_simulation(
    sim_id: int,
    *,
    model_name: str,
    max_rounds: int,
    sim_seed: int,
    verbose: bool,
) -> dict:
    model = GptLanguageModel(model_name=model_name)
    result = run_game(
        model=model,
        max_rounds=max_rounds,
        rng=Random(sim_seed),
        verbose=verbose,
    )
    result["sim_id"] = sim_id
    result["seed"] = sim_seed
    return result


# -- Section 4: CLI -----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Concordia-based Repeated PD with Costly Punishment"
    )
    parser.add_argument("-n", "--num-sims", type=int, default=1, help="Number of simulations")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (for reproducibility)")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI model name")
    parser.add_argument(
        "-j",
        "--parallel-workers",
        type=int,
        default=1,
        help="Number of parallel simulations to run (1 = sequential)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print round-by-round output")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    worker_count = resolve_worker_count(args.num_sims, args.parallel_workers)
    verbose_each = args.verbose and args.num_sims == 1
    if args.verbose and args.num_sims > 1 and worker_count > 1:
        print("[note] Disabling per-round verbose logs for parallel multi-sim run.")

    seed_rng = Random(args.seed) if args.seed is not None else Random()
    sim_jobs: list[tuple[int, int]] = []
    for sim_id in range(args.num_sims):
        if args.seed is not None:
            sim_seed = args.seed + sim_id
        else:
            sim_seed = seed_rng.randrange(0, 2**31 - 1)
        sim_jobs.append((sim_id, sim_seed))

    def _worker(job: tuple[int, int]) -> dict:
        sim_id, sim_seed = job
        return _run_single_simulation(
            sim_id=sim_id,
            model_name=args.model,
            max_rounds=MAX_ROUNDS,
            sim_seed=sim_seed,
            verbose=verbose_each,
        )

    results = parallel_map_ordered(
        sim_jobs,
        _worker,
        max_workers=worker_count,
        label="pd_concordia_punish simulations",
    )

    if args.verbose:
        for idx, result in enumerate(results, start=1):
            print(
                f"Sim {idx}/{args.num_sims} (seed={result['seed']}): "
                f"A=${result['a_total_earnings']}, "
                f"B=${result['b_total_earnings']}, "
                f"efficiency={result['efficiency']:.1%}, "
                f"punishments={result['total_punishments']}"
            )

    # --- Summary ---
    n = len(results)
    avg_a = sum(r["a_total_earnings"] for r in results) / n
    avg_b = sum(r["b_total_earnings"] for r in results) / n
    avg_eff = sum(r["efficiency"] for r in results) / n
    avg_a_coop = sum(r["a_cooperation_rate"] for r in results) / n
    avg_b_coop = sum(r["b_cooperation_rate"] for r in results) / n
    avg_mc = sum(r["mutual_cooperation_rounds"] for r in results) / n
    avg_a_punish = sum(r["a_punishment_rate"] for r in results) / n
    avg_b_punish = sum(r["b_punishment_rate"] for r in results) / n
    avg_total_punish = sum(r["total_punishments"] for r in results) / n

    print(f"\n{'=' * 50}")
    print(f"Results: {n} simulations")
    print(f"Avg Player A earnings:     ${avg_a:.1f}")
    print(f"Avg Player B earnings:     ${avg_b:.1f}")
    print(f"Avg efficiency:            {avg_eff:.1%}")
    print(f"Avg A cooperation rate:    {avg_a_coop:.1%}")
    print(f"Avg B cooperation rate:    {avg_b_coop:.1%}")
    print(f"Avg mutual coop rounds:    {avg_mc:.1f} / {MAX_ROUNDS}")
    print(f"Avg A punishment rate:     {avg_a_punish:.1%}")
    print(f"Avg B punishment rate:     {avg_b_punish:.1%}")
    print(f"Avg total punishments:     {avg_total_punish:.1f} / {MAX_ROUNDS * 2}")

    out = args.output or "pd_concordia_punish_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out}")


if __name__ == "__main__":
    main()
