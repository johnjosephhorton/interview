#!/usr/bin/env python3
"""
Concordia-based simulation for the Asymmetric Information Bargaining game.

Replaces `interview simulate bargain_asymmetric` with Concordia's component-based
agent architecture. Agents use associative memory, situation perception, and
goal-oriented reasoning instead of simple prompt-and-respond.

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
    _orig = base_gpt_model.BaseGPTModel._sample_text

    def _patched(self, prompt, reasoning_effort, verbosity, **kwargs):
        # Drop reasoning_effort and verbosity — call the OpenAI API directly
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
from interviewer.models import load_game
from interviewer.randomization import draw_conditions


def _embedder(text: str) -> np.ndarray:
    """Dummy embedder — semantic search is not needed for this game."""
    return np.zeros(16)


def _parse_action(text: str) -> tuple[str, float | None]:
    """Parse agent output into (action_type, price).

    Returns:
        ('accept', None) for acceptance
        ('offer', price) for a price offer
        ('invalid', None) for unparseable input
    """
    cleaned = text.strip().lower()
    # Strip agent name prefix if present (Concordia prepends it)
    for prefix in ("buyer ", "seller "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]

    if cleaned in ("accept", "yes", "deal", "i accept", "a"):
        return ("accept", None)

    match = re.search(r"\$?([\d]+(?:\.[\d]{1,2})?)", cleaned)
    if match:
        price = float(match.group(1))
        if 0 <= price <= 100:
            return ("offer", price)

    return ("invalid", None)


def _build_agent(
    model: GptLanguageModel,
    name: str,
    goal: str,
) -> object:
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


def run_bargaining(
    model: GptLanguageModel,
    buyer_value: float,
    seller_cost: float,
    max_rounds: int = 5,
    verbose: bool = False,
) -> dict:
    """Run one bargaining game using Concordia agents.

    Args:
        model: Concordia language model wrapper.
        buyer_value: Buyer's private valuation.
        seller_cost: Seller's private cost.
        max_rounds: Maximum negotiation rounds.
        verbose: Print round-by-round output.

    Returns:
        Dict with deal_price, earnings, history, etc.
    """
    # --- Build buyer agent ---
    buyer = _build_agent(
        model,
        name="Buyer",
        goal=(
            f"You are the BUYER in a price negotiation. "
            f"The item is worth ${buyer_value:.2f} to you. "
            f"You do NOT know the seller's exact cost — it is equally likely "
            f"to be $20, $30, $40, or $50. "
            f"The seller does NOT know your exact valuation — they know it is "
            f"one of $60, $70, $80, or $90. "
            f"Your earnings = ${buyer_value:.2f} minus the agreed price. "
            f"No deal after {max_rounds} rounds = $0. "
            f"NEVER pay more than ${buyer_value:.2f}. "
            f"Balance getting a good price against the risk of no deal."
        ),
    )

    # --- Build seller agent ---
    seller = _build_agent(
        model,
        name="Seller",
        goal=(
            f"You are the SELLER in a price negotiation. "
            f"Your cost is ${seller_cost:.2f}. "
            f"You do NOT know the buyer's exact valuation — it is equally "
            f"likely to be $60, $70, $80, or $90. "
            f"The buyer does NOT know your exact cost — they know it is "
            f"one of $20, $30, $40, or $50. "
            f"Your earnings = agreed price minus ${seller_cost:.2f}. "
            f"No deal after {max_rounds} rounds = $0. "
            f"NEVER accept below ${seller_cost:.2f}. "
            f"Balance holding out for a higher price against the risk of no deal."
        ),
    )

    # --- Seed initial context ---
    buyer.observe(
        f"You are starting a price negotiation as the buyer. "
        f"The item is worth ${buyer_value:.2f} to you. "
        f"The seller's cost is private (one of $20, $30, $40, $50). "
        f"The seller only knows your value is one of $60, $70, $80, $90. "
        f"There are {max_rounds} rounds. You offer in rounds 1, 3, 5. "
        f"The seller offers in rounds 2, 4. You go first."
    )
    seller.observe(
        f"You are starting a price negotiation as the seller. "
        f"Your cost is ${seller_cost:.2f}. "
        f"The buyer's value is private (one of $60, $70, $80, $90). "
        f"The buyer only knows your cost is one of $20, $30, $40, $50. "
        f"There are {max_rounds} rounds. The buyer offers in rounds 1, 3, 5. "
        f"You offer in rounds 2, 4. The buyer goes first."
    )

    # --- Negotiation loop ---
    # 5 rounds of alternating offers. After the final offer (round 5),
    # the other player gets one last accept/reject decision.
    history: list[dict] = []
    deal_price: float | None = None
    current_offer: float | None = None
    last_round = 0

    for round_num in range(1, max_rounds + 1):
        last_round = round_num
        is_buyer_turn = round_num % 2 == 1
        offerer = buyer if is_buyer_turn else seller
        offerer_name = "Buyer" if is_buyer_turn else "Seller"

        final_str = " This is the FINAL round!" if round_num == max_rounds else ""

        if current_offer is not None:
            other_name = "Seller" if is_buyer_turn else "Buyer"
            call = (
                f"Round {round_num} of {max_rounds}.{final_str} "
                f"The {other_name} offered ${current_offer:.2f}. "
                f"Reply with ONLY 'accept' to take this price, "
                f"or a single number (e.g. '55.00') as your counteroffer."
            )
        else:
            call = (
                f"Round {round_num} of {max_rounds}. "
                f"Make your opening offer. Reply with ONLY a single number "
                f"between 0.00 and 100.00 (e.g. '45.00')."
            )

        action_spec = ActionSpec(call_to_action=call, output_type=OutputType.FREE)
        raw = offerer.act(action_spec)
        action_type, price = _parse_action(raw)

        if verbose:
            print(f"  Round {round_num} [{offerer_name}]: {raw!r} -> {action_type}, {price}")

        if action_type == "accept" and current_offer is not None:
            deal_price = current_offer
            history.append({"round": round_num, "player": offerer_name, "action": "accept", "price": deal_price})
            obs = f"Round {round_num}: {offerer_name} accepts. Deal at ${deal_price:.2f}!"
            buyer.observe(obs)
            seller.observe(obs)
            break

        elif action_type == "offer" and price is not None:
            current_offer = price
            history.append({"round": round_num, "player": offerer_name, "action": "offer", "price": price})
            obs = f"Round {round_num}: {offerer_name} offers ${price:.2f}."
            buyer.observe(obs)
            seller.observe(obs)

        else:
            history.append({"round": round_num, "player": offerer_name, "action": "invalid", "raw": raw})
            obs = f"Round {round_num}: {offerer_name}'s response was unclear. Moving on."
            buyer.observe(obs)
            seller.observe(obs)

    # --- Final accept/reject after last offer ---
    # If the loop ended on an offer (not an acceptance), the other player
    # gets one last chance to accept or reject.
    if deal_price is None and current_offer is not None:
        is_buyer_last = last_round % 2 == 1
        responder = seller if is_buyer_last else buyer
        responder_name = "Seller" if is_buyer_last else "Buyer"
        offerer_name = "Buyer" if is_buyer_last else "Seller"

        call = (
            f"The {offerer_name}'s final offer is ${current_offer:.2f}. "
            f"This is the LAST chance — accept or reject. No more rounds. "
            f"Reply with ONLY 'accept' or 'reject'."
        )
        action_spec = ActionSpec(call_to_action=call, output_type=OutputType.FREE)
        raw = responder.act(action_spec)
        action_type, _ = _parse_action(raw)

        if verbose:
            print(f"  Final [{responder_name}]: {raw!r} -> {action_type}")

        if action_type == "accept":
            deal_price = current_offer
            history.append({"round": last_round, "player": responder_name, "action": "accept", "price": deal_price})
            obs = f"{responder_name} accepts the final offer. Deal at ${deal_price:.2f}!"
            buyer.observe(obs)
            seller.observe(obs)
        else:
            history.append({"round": last_round, "player": responder_name, "action": "reject"})
            obs = f"{responder_name} rejects. No deal reached."
            buyer.observe(obs)
            seller.observe(obs)

    # --- Compute payoffs ---
    if deal_price is not None:
        buyer_earn = round(buyer_value - deal_price, 2)
        seller_earn = round(deal_price - seller_cost, 2)
    else:
        buyer_earn = 0.0
        seller_earn = 0.0

    return {
        "buyer_value": buyer_value,
        "seller_cost": seller_cost,
        "zopa": round(buyer_value - seller_cost, 2),
        "deal_reached": deal_price is not None,
        "deal_price": deal_price,
        "buyer_earnings": buyer_earn,
        "seller_earnings": seller_earn,
        "rounds_played": len(history),
        "history": history,
    }


def _run_single_simulation(
    *,
    sim_id: int,
    model_name: str,
    buyer_value: float,
    seller_cost: float,
    verbose: bool,
) -> dict:
    model = GptLanguageModel(model_name=model_name)
    result = run_bargaining(
        model=model,
        buyer_value=buyer_value,
        seller_cost=seller_cost,
        verbose=verbose,
    )
    result["sim_id"] = sim_id
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Concordia-based asymmetric bargaining simulation"
    )
    parser.add_argument("-n", "--num-sims", type=int, default=1, help="Number of simulations")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for variable draws")
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

    game_config = load_game("bargain_asymmetric")
    rng = Random(args.seed) if args.seed is not None else Random()

    worker_count = resolve_worker_count(args.num_sims, args.parallel_workers)
    verbose_each = args.verbose and args.num_sims == 1
    if args.verbose and args.num_sims > 1 and worker_count > 1:
        print("[note] Disabling per-round verbose logs for parallel multi-sim run.")

    sim_jobs: list[dict] = []
    for sim_id in range(args.num_sims):
        conditions = draw_conditions(game_config.variables, sim_id, rng)
        sim_jobs.append(
            {
                "sim_id": sim_id,
                "buyer_value": float(conditions["buyer_value"]),
                "seller_cost": float(conditions["seller_cost"]),
                "conditions": {
                    k: float(v) if isinstance(v, (int, float)) else v
                    for k, v in conditions.items()
                },
            }
        )

    def _worker(job: dict) -> dict:
        result = _run_single_simulation(
            sim_id=job["sim_id"],
            model_name=args.model,
            buyer_value=job["buyer_value"],
            seller_cost=job["seller_cost"],
            verbose=verbose_each,
        )
        result["conditions"] = job["conditions"]
        return result

    results = parallel_map_ordered(
        sim_jobs,
        _worker,
        max_workers=worker_count,
        label="bargain_asymmetric simulations",
    )

    if args.verbose:
        for idx, result in enumerate(results, start=1):
            cond = result["conditions"]
            print(
                f"Sim {idx}/{args.num_sims}: "
                f"buyer_value={cond['buyer_value']}, seller_cost={cond['seller_cost']}"
            )
            if result["deal_reached"]:
                print(
                    f"  -> Deal at ${result['deal_price']:.2f} "
                    f"(Buyer: ${result['buyer_earnings']:.2f}, "
                    f"Seller: ${result['seller_earnings']:.2f})"
                )
            else:
                print("  -> No deal (both earn $0)")

    # --- Summary ---
    deals = [r for r in results if r["deal_reached"]]
    print(f"\n{'=' * 50}")
    print(f"Results: {len(deals)}/{len(results)} deals reached")
    if deals:
        avg_price = sum(r["deal_price"] for r in deals) / len(deals)
        avg_buyer = sum(r["buyer_earnings"] for r in deals) / len(deals)
        avg_seller = sum(r["seller_earnings"] for r in deals) / len(deals)
        print(f"Avg deal price:      ${avg_price:.2f}")
        print(f"Avg buyer earnings:  ${avg_buyer:.2f}")
        print(f"Avg seller earnings: ${avg_seller:.2f}")

    out = args.output or "bargain_asymmetric_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out}")


if __name__ == "__main__":
    main()
