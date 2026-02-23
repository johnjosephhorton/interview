#!/usr/bin/env python3
"""
Concordia-based simulation for the Mug Bargain with Cheap Talk experiment.

Implements all 12 conditions from the mug_bargain_cheap_talk design:
  - Communication: none / cheap_talk / extended_talk
  - Value gap: narrow / wide
  - Info asymmetry: two_sided_private / one_sided_buyer_known

Usage:
    # Single simulation, specific condition
    python concordia_sim.py --communication cheap_talk --value-gap narrow \
        --info-asymmetry two_sided_private --seed 5001 -v

    # Run a batch for one condition
    python concordia_sim.py --communication none --value-gap narrow \
        --info-asymmetry two_sided_private -n 30 --seed 1001 -o results_C01.json

    # Run all 12 conditions (use run_all.sh)
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


# ---------------------------------------------------------------------------
# Patch Concordia for non-reasoning models
# ---------------------------------------------------------------------------

def _patch_concordia_for_non_reasoning_models():
    """Drop unsupported parameters (reasoning_effort, verbosity) for standard models."""
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

# Add project root so we can import interviewer helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from interviewer.concordia_parallel import parallel_map_ordered, resolve_worker_count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _embedder(text: str) -> np.ndarray:
    """Dummy embedder — semantic search not needed for this game."""
    return np.zeros(16)


def _parse_action(text: str) -> tuple[str, float | None]:
    """Parse agent output into (action_type, price).

    Returns:
        ('accept', None) for acceptance
        ('reject', None) for rejection
        ('offer', price) for a price offer
        ('invalid', None) for unparseable input
    """
    cleaned = text.strip().lower()
    # Strip agent name prefix if present (Concordia prepends it)
    for prefix in ("buyer ", "seller "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]

    if cleaned in ("accept", "yes", "deal", "i accept", "a", "ok"):
        return ("accept", None)
    if cleaned in ("reject", "no", "no deal", "i reject"):
        return ("reject", None)

    match = re.search(r"\$?([\d]+(?:\.[\d]{1,2})?)", cleaned)
    if match:
        price = float(match.group(1))
        if 0 <= price <= 20:
            return ("offer", price)

    return ("invalid", None)


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


# ---------------------------------------------------------------------------
# Value draws
# ---------------------------------------------------------------------------

def draw_values(value_gap: str, rng: Random) -> tuple[float, float]:
    """Draw buyer WTP and seller WTA from the condition's distribution.

    Args:
        value_gap: 'narrow' or 'wide'
        rng: seeded random instance

    Returns:
        (buyer_wtp, seller_wta) rounded to 2 decimal places
    """
    if value_gap == "narrow":
        buyer_wtp = round(rng.uniform(8.0, 12.0), 2)
        seller_wta = round(rng.uniform(6.0, 10.0), 2)
    elif value_gap == "wide":
        buyer_wtp = round(rng.uniform(5.0, 15.0), 2)
        seller_wta = round(rng.uniform(5.0, 15.0), 2)
    else:
        raise ValueError(f"Unknown value_gap: {value_gap}")
    return buyer_wtp, seller_wta


# ---------------------------------------------------------------------------
# Communication phase
# ---------------------------------------------------------------------------

def run_communication(
    buyer,
    seller,
    buyer_wtp: float,
    seller_wta: float,
    communication: str,
    info_asymmetry: str,
    talk_order_rng: Random,
    verbose: bool = False,
) -> list[dict]:
    """Run pre-play cheap talk phase.

    Returns list of message dicts: [{speaker, round, message}]
    """
    if communication == "none":
        return []

    messages = []

    if communication == "cheap_talk":
        # One simultaneous round: both speak before seeing the other's message
        buyer_call = (
            "Before bargaining begins, you can send ONE free-form message to the seller. "
            "This message is NON-BINDING — you are not committed to anything you say. "
            "You may say anything: your intentions, questions, persuasive claims, or bluffs. "
            "Reply with your message."
        )
        seller_call = (
            "Before bargaining begins, you can send ONE free-form message to the buyer. "
            "This message is NON-BINDING — you are not committed to anything you say. "
            "You may say anything: your intentions, questions, persuasive claims, or bluffs. "
            "Reply with your message."
        )
        buyer_spec = ActionSpec(call_to_action=buyer_call, output_type=OutputType.FREE)
        seller_spec = ActionSpec(call_to_action=seller_call, output_type=OutputType.FREE)

        # Randomize who speaks first to eliminate positional bias
        if talk_order_rng.choice([True, False]):
            buyer_msg = buyer.act(buyer_spec)
            seller_msg = seller.act(seller_spec)
        else:
            seller_msg = seller.act(seller_spec)
            buyer_msg = buyer.act(buyer_spec)

        messages.append({"speaker": "Buyer", "round": 1, "message": buyer_msg})
        messages.append({"speaker": "Seller", "round": 1, "message": seller_msg})

        if verbose:
            print(f"  [Cheap Talk] Buyer: {buyer_msg!r}")
            print(f"  [Cheap Talk] Seller: {seller_msg!r}")

        # Both observe the other's message
        buyer.observe(f"The seller sent you this message (non-binding cheap talk): {seller_msg}")
        seller.observe(f"The buyer sent you this message (non-binding cheap talk): {buyer_msg}")

    elif communication == "extended_talk":
        # Three alternating rounds: Seller→Buyer→Seller→Buyer→Seller→Buyer
        speakers = ["Seller", "Buyer"] * 3
        agents = {"Seller": seller, "Buyer": buyer}

        for i, speaker_name in enumerate(speakers):
            talk_round = i // 2 + 1
            agent = agents[speaker_name]
            other_name = "Buyer" if speaker_name == "Seller" else "Seller"

            call = (
                f"Communication round {talk_round} of 3. "
                f"Send a free-form message to the {other_name}. "
                f"This is NON-BINDING cheap talk — you are not committed to anything you say. "
                f"Reply with your message."
            )
            spec = ActionSpec(call_to_action=call, output_type=OutputType.FREE)
            msg = agent.act(spec)

            messages.append({"speaker": speaker_name, "round": talk_round, "message": msg})

            if verbose:
                print(f"  [Talk R{talk_round}] {speaker_name}: {msg!r}")

            # Other agent observes
            other_agent = agents[other_name]
            other_agent.observe(
                f"The {speaker_name} sent you this message (non-binding cheap talk, "
                f"round {talk_round}): {msg}"
            )
    else:
        raise ValueError(f"Unknown communication: {communication}")

    return messages


# ---------------------------------------------------------------------------
# Bargaining phase
# ---------------------------------------------------------------------------

def run_bargaining(
    buyer,
    seller,
    buyer_wtp: float,
    seller_wta: float,
    max_rounds: int = 4,
    verbose: bool = False,
) -> tuple[float | None, list[dict]]:
    """Run alternating-offer bargaining.

    Protocol:
      Round 1: Seller proposes
      Round 2: Buyer accepts or counter-offers
      Round 3: Seller accepts counter-offer or makes final offer
      Round 4: Buyer accepts or rejects final offer

    Returns:
        (deal_price or None, history list)
    """
    history: list[dict] = []
    current_offer: float | None = None
    deal_price: float | None = None

    for round_num in range(1, max_rounds + 1):
        is_seller_turn = round_num % 2 == 1
        offerer = seller if is_seller_turn else buyer
        offerer_name = "Seller" if is_seller_turn else "Buyer"

        is_final = round_num == max_rounds

        if current_offer is not None:
            other_name = "Buyer" if is_seller_turn else "Seller"
            if is_final:
                # Final round: emphasize payoff consequences
                if not is_seller_turn:
                    # Buyer's final decision
                    earn_if_accept = round(buyer_wtp - current_offer, 2)
                    call = (
                        f"The {other_name}'s final offer is ${current_offer:.2f}. "
                        f"This is the LAST chance. If you accept, you earn "
                        f"${buyer_wtp:.2f} - ${current_offer:.2f} = ${earn_if_accept:.2f}. "
                        f"If you reject, you earn $0.00 (no deal). "
                        f"Reply with ONLY 'accept' or 'reject'."
                    )
                else:
                    # Seller's final decision
                    earn_if_accept = round(current_offer - seller_wta, 2)
                    call = (
                        f"The {other_name}'s final offer is ${current_offer:.2f}. "
                        f"This is the LAST chance. If you accept, you earn "
                        f"${current_offer:.2f} - ${seller_wta:.2f} = ${earn_if_accept:.2f}. "
                        f"If you reject, you earn $0.00 (no deal). "
                        f"Reply with ONLY 'accept' or 'reject'."
                    )
            else:
                # Non-final round: add role-specific directional hint
                if not is_seller_turn:
                    # Buyer responding to seller's ask
                    call = (
                        f"Bargaining round {round_num} of {max_rounds}. "
                        f"The Seller is asking ${current_offer:.2f}. "
                        f"You want a LOWER price (you earn ${buyer_wtp:.2f} minus the price). "
                        f"Reply with ONLY 'accept' to buy at ${current_offer:.2f}, "
                        f"or a LOWER number as your counteroffer (e.g. '{max(0, current_offer - 2):.2f}')."
                    )
                else:
                    # Seller responding to buyer's bid
                    call = (
                        f"Bargaining round {round_num} of {max_rounds}. "
                        f"The Buyer is bidding ${current_offer:.2f}. "
                        f"You want a HIGHER price (you earn the price minus ${seller_wta:.2f}). "
                        f"Reply with ONLY 'accept' to sell at ${current_offer:.2f}, "
                        f"or a HIGHER number as your counteroffer (e.g. '{min(15, current_offer + 2):.2f}')."
                    )
        else:
            call = (
                f"Bargaining round {round_num} of {max_rounds}. "
                f"Make your opening offer for the mug. "
                f"Reply with ONLY a single number between 0.00 and 15.00 (e.g. '9.50')."
            )

        action_spec = ActionSpec(call_to_action=call, output_type=OutputType.FREE)
        raw = offerer.act(action_spec)
        action_type, price = _parse_action(raw)

        # Final-round rationality guardrail: no rational agent rejects
        # guaranteed positive earnings on the last round.
        if is_final and action_type == "reject" and current_offer is not None:
            if not is_seller_turn:
                # Buyer: accept if WTP > offer price
                if buyer_wtp > current_offer:
                    action_type = "accept"
                    if verbose:
                        print(f"  Round {round_num} [{offerer_name}]: {raw!r} -> "
                              f"GUARDRAIL: reject overridden to accept "
                              f"(WTP ${buyer_wtp:.2f} > offer ${current_offer:.2f})")
            else:
                # Seller: accept if offer > WTA
                if current_offer > seller_wta:
                    action_type = "accept"
                    if verbose:
                        print(f"  Round {round_num} [{offerer_name}]: {raw!r} -> "
                              f"GUARDRAIL: reject overridden to accept "
                              f"(offer ${current_offer:.2f} > WTA ${seller_wta:.2f})")

        if verbose and action_type != "accept":
            print(f"  Round {round_num} [{offerer_name}]: {raw!r} -> {action_type}, {price}")

        if action_type == "accept" and current_offer is not None:
            deal_price = current_offer
            history.append({
                "round": round_num, "player": offerer_name,
                "action": "accept", "price": deal_price,
            })
            obs = f"Round {round_num}: {offerer_name} accepts. Deal at ${deal_price:.2f}!"
            buyer.observe(obs)
            seller.observe(obs)
            break

        elif action_type == "reject":
            history.append({
                "round": round_num, "player": offerer_name, "action": "reject",
            })
            obs = f"Round {round_num}: {offerer_name} rejects. No deal reached."
            buyer.observe(obs)
            seller.observe(obs)
            break

        elif action_type == "offer" and price is not None:
            current_offer = price
            history.append({
                "round": round_num, "player": offerer_name,
                "action": "offer", "price": price,
            })
            obs = f"Round {round_num}: {offerer_name} offers ${price:.2f}."
            buyer.observe(obs)
            seller.observe(obs)

        else:
            # Invalid response — treat as pass, move to next round
            history.append({
                "round": round_num, "player": offerer_name,
                "action": "invalid", "raw": raw,
            })
            obs = f"Round {round_num}: {offerer_name}'s response was unclear. Moving on."
            buyer.observe(obs)
            seller.observe(obs)

    return deal_price, history


# ---------------------------------------------------------------------------
# Full game
# ---------------------------------------------------------------------------

def run_game(
    model: GptLanguageModel,
    communication: str,
    value_gap: str,
    info_asymmetry: str,
    buyer_wtp: float,
    seller_wta: float,
    talk_order_rng: Random,
    verbose: bool = False,
) -> dict:
    """Run one complete mug bargaining game.

    Returns dict with all outcome variables and metadata.
    """
    max_bargaining_rounds = 4

    # --- Info structure descriptions ---
    if info_asymmetry == "two_sided_private":
        if value_gap == "narrow":
            buyer_info = (
                f"You do NOT know the seller's exact valuation — "
                f"you only know the mug is worth somewhere between $6 and $10 to them."
            )
            seller_info = (
                f"You do NOT know the buyer's exact valuation — "
                f"you only know the mug is worth somewhere between $8 and $12 to them."
            )
        else:  # wide
            buyer_info = (
                f"You do NOT know the seller's exact valuation — "
                f"you only know the mug is worth somewhere between $5 and $15 to them."
            )
            seller_info = (
                f"You do NOT know the buyer's exact valuation — "
                f"you only know the mug is worth somewhere between $5 and $15 to them."
            )
    elif info_asymmetry == "one_sided_buyer_known":
        buyer_info = (
            f"The seller KNOWS your valuation is ${buyer_wtp:.2f}. "
        )
        if value_gap == "narrow":
            buyer_info += (
                f"You do NOT know the seller's exact valuation — "
                f"you only know the mug is worth somewhere between $6 and $10 to them."
            )
            seller_info = (
                f"You KNOW the buyer values the mug at ${buyer_wtp:.2f}. "
                f"The buyer does NOT know your exact cost."
            )
        else:  # wide
            buyer_info += (
                f"You do NOT know the seller's exact valuation — "
                f"you only know the mug is worth somewhere between $5 and $15 to them."
            )
            seller_info = (
                f"You KNOW the buyer values the mug at ${buyer_wtp:.2f}. "
                f"The buyer does NOT know your exact cost."
            )
    else:
        raise ValueError(f"Unknown info_asymmetry: {info_asymmetry}")

    # --- Build agents ---
    buyer_goal = (
        f"You are the BUYER in a price negotiation over a coffee mug. "
        f"The mug is worth ${buyer_wtp:.2f} to you. "
        f"{buyer_info} "
        f"Your earnings = ${buyer_wtp:.2f} minus the agreed price. "
        f"No deal = $0. "
        f"NEVER pay more than ${buyer_wtp:.2f}. "
        f"Balance getting a good price against the risk of no deal."
    )
    seller_goal = (
        f"You are the SELLER in a price negotiation over a coffee mug. "
        f"The mug is worth ${seller_wta:.2f} to you (your minimum acceptable price). "
        f"{seller_info} "
        f"Your earnings = agreed price minus ${seller_wta:.2f}. "
        f"No deal = $0. "
        f"NEVER accept below ${seller_wta:.2f}. "
        f"Balance holding out for a higher price against the risk of no deal."
    )

    buyer = _build_agent(model, name="Buyer", goal=buyer_goal)
    seller = _build_agent(model, name="Seller", goal=seller_goal)

    # --- Seed initial context ---
    comm_desc = {
        "none": "There is no communication phase. Bargaining starts immediately.",
        "cheap_talk": (
            "Before bargaining, you will each send one non-binding message to the other. "
            "Then bargaining begins."
        ),
        "extended_talk": (
            "Before bargaining, there will be 3 rounds of alternating non-binding messages "
            "(seller and buyer take turns). Then bargaining begins."
        ),
    }[communication]

    intro_buyer = (
        f"You are about to negotiate over a coffee mug as the buyer. "
        f"The mug is worth ${buyer_wtp:.2f} to you. {buyer_info} "
        f"{comm_desc} "
        f"Bargaining has {max_bargaining_rounds} rounds: seller offers on rounds 1 & 3, "
        f"you offer on rounds 2 & 4. On round 4, you can only accept or reject."
    )
    intro_seller = (
        f"You are about to negotiate over a coffee mug as the seller. "
        f"The mug is worth ${seller_wta:.2f} to you. {seller_info} "
        f"{comm_desc} "
        f"Bargaining has {max_bargaining_rounds} rounds: you offer on rounds 1 & 3, "
        f"buyer offers on rounds 2 & 4. On round 4, buyer can only accept or reject."
    )

    buyer.observe(intro_buyer)
    seller.observe(intro_seller)

    # --- Communication phase ---
    comm_messages = run_communication(
        buyer=buyer,
        seller=seller,
        buyer_wtp=buyer_wtp,
        seller_wta=seller_wta,
        communication=communication,
        info_asymmetry=info_asymmetry,
        talk_order_rng=talk_order_rng,
        verbose=verbose,
    )

    if comm_messages:
        buyer.observe("The communication phase is over. Bargaining begins now.")
        seller.observe("The communication phase is over. Bargaining begins now.")

    # --- Bargaining phase ---
    deal_price, bargain_history = run_bargaining(
        buyer=buyer,
        seller=seller,
        buyer_wtp=buyer_wtp,
        seller_wta=seller_wta,
        max_rounds=max_bargaining_rounds,
        verbose=verbose,
    )

    # --- Compute outcomes ---
    deal = deal_price is not None
    if deal:
        buyer_earn = round(buyer_wtp - deal_price, 2)
        seller_earn = round(deal_price - seller_wta, 2)
    else:
        buyer_earn = 0.0
        seller_earn = 0.0

    gains_from_trade = buyer_wtp - seller_wta
    feasible = gains_from_trade > 0

    if deal and feasible:
        surplus_captured = round((buyer_earn + seller_earn) / gains_from_trade, 4)
        price_split_ratio = round((deal_price - seller_wta) / gains_from_trade, 4)
    else:
        surplus_captured = 0.0 if feasible else None
        price_split_ratio = None

    rounds_to_agreement = None
    if deal:
        for h in bargain_history:
            if h["action"] == "accept":
                rounds_to_agreement = h["round"]
                break

    # Extract numerical value signals from communication messages
    comm_value_signals = []
    for msg in comm_messages:
        numbers = re.findall(r"\$?([\d]+(?:\.[\d]{1,2})?)", msg["message"])
        for n in numbers:
            val = float(n)
            if 0 < val <= 20:
                comm_value_signals.append({
                    "speaker": msg["speaker"],
                    "round": msg["round"],
                    "value_mentioned": val,
                })

    return {
        # Condition metadata
        "communication": communication,
        "value_gap": value_gap,
        "info_asymmetry": info_asymmetry,
        # Ground truth values
        "buyer_wtp": buyer_wtp,
        "seller_wta": seller_wta,
        "gains_from_trade": round(gains_from_trade, 2),
        "feasible": feasible,
        # Primary outcomes
        "deal": deal,
        "final_price": deal_price,
        "surplus_captured": surplus_captured,
        "price_split_ratio": price_split_ratio,
        "rounds_to_agreement": rounds_to_agreement,
        # Earnings
        "buyer_earnings": buyer_earn,
        "seller_earnings": seller_earn,
        # Communication data
        "comm_messages": comm_messages,
        "comm_value_signals": comm_value_signals,
        # Bargaining data
        "bargain_history": bargain_history,
        "bargain_rounds_played": len(bargain_history),
    }


def _run_single_simulation(
    *,
    sim_id: int,
    sim_seed: int,
    model_name: str,
    communication: str,
    value_gap: str,
    info_asymmetry: str,
    buyer_wtp: float,
    seller_wta: float,
    verbose: bool,
) -> dict:
    model = GptLanguageModel(model_name=model_name)
    result = run_game(
        model=model,
        communication=communication,
        value_gap=value_gap,
        info_asymmetry=info_asymmetry,
        buyer_wtp=buyer_wtp,
        seller_wta=seller_wta,
        talk_order_rng=Random(sim_seed),
        verbose=verbose,
    )
    result["sim_id"] = sim_id
    result["seed"] = sim_seed
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Concordia-based mug bargaining with cheap talk"
    )
    parser.add_argument(
        "--communication", required=True,
        choices=["none", "cheap_talk", "extended_talk"],
        help="Communication treatment",
    )
    parser.add_argument(
        "--value-gap", required=True,
        choices=["narrow", "wide"],
        help="Value gap treatment",
    )
    parser.add_argument(
        "--info-asymmetry", required=True,
        choices=["two_sided_private", "one_sided_buyer_known"],
        help="Information structure treatment",
    )
    parser.add_argument("-n", "--num-sims", type=int, default=1, help="Number of simulations")
    parser.add_argument("--seed", type=int, default=None, help="Starting random seed")
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
    sim_jobs: list[dict] = []
    for sim_id in range(args.num_sims):
        if args.seed is not None:
            sim_seed = args.seed + sim_id
        else:
            sim_seed = seed_rng.randrange(0, 2**31 - 1)
        buyer_wtp, seller_wta = draw_values(args.value_gap, Random(sim_seed))
        sim_jobs.append(
            {
                "sim_id": sim_id,
                "sim_seed": sim_seed,
                "buyer_wtp": buyer_wtp,
                "seller_wta": seller_wta,
            }
        )

    def _worker(job: dict) -> dict:
        return _run_single_simulation(
            sim_id=job["sim_id"],
            sim_seed=job["sim_seed"],
            model_name=args.model,
            communication=args.communication,
            value_gap=args.value_gap,
            info_asymmetry=args.info_asymmetry,
            buyer_wtp=job["buyer_wtp"],
            seller_wta=job["seller_wta"],
            verbose=verbose_each,
        )

    results = parallel_map_ordered(
        sim_jobs,
        _worker,
        max_workers=worker_count,
        label="mug_bargain_cheap_talk simulations",
    )

    if args.verbose:
        for idx, result in enumerate(results, start=1):
            print(
                f"Sim {idx}/{args.num_sims} (seed={result['seed']}): "
                f"WTP={result['buyer_wtp']}, WTA={result['seller_wta']}, "
                f"gap={round(result['buyer_wtp'] - result['seller_wta'], 2)}"
            )
            if result["deal"]:
                print(
                    f"  -> Deal at ${result['final_price']:.2f} "
                    f"(Buyer: ${result['buyer_earnings']:.2f}, "
                    f"Seller: ${result['seller_earnings']:.2f})"
                )
            else:
                print("  -> No deal (both earn $0)")

    # --- Summary ---
    deals = [r for r in results if r["deal"]]
    feasible = [r for r in results if r["feasible"]]
    n = len(results)
    print(f"\n{'=' * 60}")
    print(f"Condition: {args.communication} / {args.value_gap} / {args.info_asymmetry}")
    print(f"Simulations: {n}")
    print(f"Feasible trades: {len(feasible)}/{n}")
    print(f"Deals reached: {len(deals)}/{n} ({100 * len(deals) / n:.0f}%)")
    if deals:
        avg_price = sum(r["final_price"] for r in deals) / len(deals)
        avg_buyer = sum(r["buyer_earnings"] for r in deals) / len(deals)
        avg_seller = sum(r["seller_earnings"] for r in deals) / len(deals)
        print(f"Avg deal price:      ${avg_price:.2f}")
        print(f"Avg buyer earnings:  ${avg_buyer:.2f}")
        print(f"Avg seller earnings: ${avg_seller:.2f}")
    feasible_deals = [r for r in deals if r["feasible"] and r["surplus_captured"] is not None]
    if feasible_deals:
        avg_surplus = sum(r["surplus_captured"] for r in feasible_deals) / len(feasible_deals)
        print(f"Avg surplus captured: {avg_surplus:.2%}")

    # Save results
    cond_tag = f"{args.communication}_{args.value_gap}_{args.info_asymmetry}"
    out = args.output or f"mug_bargain_{cond_tag}_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out}")


if __name__ == "__main__":
    main()
