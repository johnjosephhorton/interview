"""
Data extraction for info_precision_bargaining_v2 experiment.

3 conditions: bargain_tight_none, bargain_tight_range, bargain_tight_exact
10 simulations each, with buyer_value in {42, 45} and seller_cost = 40.
"""

import json
import re
import glob
import csv
import os

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONDITIONS = {
    "bargain_tight_none": {
        "path": "transcripts/bargain_tight_none/2026-02-12_17-01-02_sim*.json",
        "label": "none",
    },
    "bargain_tight_range": {
        "path": "transcripts/bargain_tight_range/2026-02-12_17-04-31_sim*.json",
        "label": "range",
    },
    "bargain_tight_exact": {
        "path": "transcripts/bargain_tight_exact/2026-02-12_17-07-40_sim*.json",
        "label": "exact",
    },
}

OUT_CSV = os.path.join(BASE_DIR, "writeup", "data", "info_precision_bargaining_v2_data.csv")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_sim_id(filepath):
    """Extract simulation number from filename like ...sim3.json."""
    m = re.search(r'sim(\d+)\.json$', filepath)
    return int(m.group(1)) if m else None


def parse_earnings(text):
    """Parse Human and AI earnings from the GAME OVER box."""
    human_earnings = None
    ai_earnings = None
    # Match "Human: $X.XX" (possibly with negative sign)
    hm = re.search(r'Human:\s*\$(-?\d+\.?\d*)', text)
    if hm:
        human_earnings = float(hm.group(1))
    am = re.search(r'AI:\s*\$(-?\d+\.?\d*)', text)
    if am:
        ai_earnings = float(am.group(1))
    return human_earnings, ai_earnings


def parse_round_offers(messages):
    """
    Parse offers from the message transcript.

    Returns:
        rounds_played: int
        ai_opening_offer: float or None
        human_counteroffer: float or None
        ai_final_offer: float or None
    """
    ai_opening_offer = None
    human_counteroffer = None
    ai_final_offer = None
    max_round = 1  # At minimum, Round 1 happens (AI opening)

    full_text = "\n".join(m["text"] for m in messages if m["role"] == "interviewer")

    # AI opening offer: "Round 1: The AI offers $X.XX" or similar
    m = re.search(r'Round 1.*?(?:AI|seller)\s+offers?\s+\$(\d+\.?\d*)', full_text, re.IGNORECASE)
    if m:
        ai_opening_offer = float(m.group(1))
    else:
        # Fallback: "Last offer: $X.XX by AI" in Round 1 status block
        m = re.search(r'Round 1 of 3\s*\n\s*Last offer:\s*\$(\d+\.?\d*)\s*by AI', full_text)
        if m:
            ai_opening_offer = float(m.group(1))

    # Human counteroffer in Round 2: "Round 2: You offered $X.XX"
    m = re.search(r'Round 2.*?(?:You|Human)\s+offered?\s+\$(\d+\.?\d*)', full_text, re.IGNORECASE)
    if m:
        human_counteroffer = float(m.group(1))
        max_round = max(max_round, 2)

    # AI final offer in Round 3: "Round 3.*AI counteroffers $X.XX" or "Round 3.*AI offers $X.XX"
    m = re.search(r'Round 3.*?(?:AI|seller)\s+(?:counter)?offers?\s+\$(\d+\.?\d*)', full_text, re.IGNORECASE)
    if m:
        ai_final_offer = float(m.group(1))
        max_round = max(max_round, 3)

    # Also check for Round 3 in the status block as a fallback
    if ai_final_offer is None:
        m = re.search(r'Round 3 of 3\s*\n\s*Last offer:\s*\$(\d+\.?\d*)\s*by AI', full_text)
        if m:
            ai_final_offer = float(m.group(1))
            max_round = max(max_round, 3)

    # If human counteroffer not found via Round 2 label, check if human offered
    # by looking at respondent messages that are numeric (counteroffers)
    if human_counteroffer is None:
        # Check: did the AI accept the human's offer in Round 2?
        # Pattern: "Deal reached at $X" after human counteroffer
        for i, msg in enumerate(messages):
            if msg["role"] == "respondent" and msg["text"].strip():
                text = msg["text"].strip()
                # Skip acceptance/rejection words
                if text.lower() in ("accept", "yes", "deal", "i accept", "a",
                                     "reject", "no", "no deal", "i reject", ""):
                    continue
                # Try to parse as a number
                nm = re.search(r'(\d+\.?\d*)', text)
                if nm:
                    val = float(nm.group(1))
                    if 0 <= val <= 100:
                        human_counteroffer = val
                        max_round = max(max_round, 2)
                        break

    return max_round, ai_opening_offer, human_counteroffer, ai_final_offer


def parse_deal_price(messages, human_earnings, ai_earnings, seller_cost, buyer_value):
    """
    Parse deal price from transcript text. Multiple strategies:
    1. Compute from earnings (most reliable): price = seller_cost + ai_earnings
       Cross-check: price should also = buyer_value - human_earnings
    2. "Deal at $X" or "Deal reached at $X" in non-opening messages
    """
    # Strategy 1 (primary): Compute from earnings — always correct
    if ai_earnings is not None and ai_earnings > 0:
        price_from_ai = round(seller_cost + ai_earnings, 2)
        # Cross-check with human earnings
        if human_earnings is not None and buyer_value is not None:
            price_from_human = round(buyer_value - human_earnings, 2)
            if abs(price_from_ai - price_from_human) < 0.02:
                return price_from_ai
            # If they disagree, prefer human_earnings calc (buyer_value - human_earnings)
            # since that's the buyer's perspective and more directly stated
            return price_from_human
        return price_from_ai

    # Strategy 2: "Deal at $X" in non-opening messages (skip the first interviewer msg
    # which contains examples like "Deal at $41.00 -> You earn...")
    for msg in messages[1:]:  # skip opening message
        if msg["role"] == "interviewer":
            m = re.search(r'[Dd]eal(?:\s+reached)?\s+at\s+\$(\d+\.?\d*)', msg["text"])
            if m:
                return float(m.group(1))

    return None


def process_transcript(filepath, condition_label):
    """Process a single transcript JSON file and return a data dict."""
    with open(filepath) as f:
        data = json.load(f)

    sim_id = extract_sim_id(filepath)
    conditions = data.get("conditions", {})
    seller_cost = conditions.get("seller_cost", 40)
    buyer_value = conditions.get("buyer_value")
    fair_price = conditions.get("fair_price")
    zopa = conditions.get("zopa")

    # If zopa not in conditions, compute it
    if zopa is None and buyer_value is not None:
        zopa = buyer_value - seller_cost

    messages = data.get("messages", [])

    # Concatenate all text for GAME OVER detection
    all_text = "\n".join(m["text"] for m in messages)

    # Parse earnings from GAME OVER box
    human_earnings, ai_earnings = parse_earnings(all_text)

    # Determine if deal was reached
    has_game_over = "GAME OVER" in all_text
    if human_earnings is not None and ai_earnings is not None:
        total_earnings = human_earnings + ai_earnings
        deal_reached = has_game_over and total_earnings > 0
    else:
        deal_reached = False

    # Parse deal price
    deal_price = None
    if deal_reached:
        deal_price = parse_deal_price(messages, human_earnings, ai_earnings, seller_cost, buyer_value)

    # Parse round offers
    rounds_to_deal, ai_opening_offer, human_counteroffer, ai_final_offer = parse_round_offers(messages)

    # Computed columns
    total_surplus = None
    efficiency = None
    buyer_surplus_share = None

    if deal_reached and deal_price is not None and zopa is not None and zopa > 0:
        total_surplus = round(buyer_value - seller_cost, 2)  # = zopa when deal reached
        # Actual realized surplus (should equal total_surplus if deal is in ZOPA)
        actual_surplus = round((human_earnings or 0) + (ai_earnings or 0), 2)
        efficiency = round(actual_surplus / total_surplus, 4) if total_surplus > 0 else None
        buyer_surplus_share = round((human_earnings or 0) / actual_surplus, 4) if actual_surplus > 0 else None
    elif not deal_reached:
        total_surplus = 0
        efficiency = 0
        buyer_surplus_share = None

    return {
        "sim_id": sim_id,
        "condition": condition_label,
        "buyer_value": buyer_value,
        "seller_cost": seller_cost,
        "zopa": zopa,
        "fair_price": fair_price,
        "deal_reached": deal_reached,
        "deal_price": deal_price,
        "human_earnings": human_earnings,
        "ai_earnings": ai_earnings,
        "rounds_to_deal": rounds_to_deal,
        "ai_opening_offer": ai_opening_offer,
        "human_counteroffer": human_counteroffer,
        "ai_final_offer": ai_final_offer,
        "total_surplus": total_surplus,
        "efficiency": efficiency,
        "buyer_surplus_share": buyer_surplus_share,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    rows = []

    for cond_name, cond_info in CONDITIONS.items():
        pattern = os.path.join(BASE_DIR, cond_info["path"])
        files = sorted(glob.glob(pattern))
        # Exclude _check.json files
        files = [f for f in files if "_check.json" not in f]
        print(f"  {cond_name}: found {len(files)} transcripts")

        for fpath in files:
            row = process_transcript(fpath, cond_info["label"])
            rows.append(row)

    # Sort by condition then sim_id
    rows.sort(key=lambda r: (r["condition"], r["sim_id"]))

    # Write CSV
    fieldnames = [
        "sim_id", "condition", "buyer_value", "seller_cost", "zopa", "fair_price",
        "deal_reached", "deal_price", "human_earnings", "ai_earnings",
        "rounds_to_deal", "ai_opening_offer", "human_counteroffer", "ai_final_offer",
        "total_surplus", "efficiency", "buyer_surplus_share",
    ]

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {OUT_CSV}")

    # -----------------------------------------------------------------------
    # Summary table: condition x ZOPA
    # -----------------------------------------------------------------------
    from collections import defaultdict

    groups = defaultdict(list)
    for r in rows:
        key = (r["condition"], r["zopa"])
        groups[key].append(r)

    print("\n" + "=" * 85)
    print(f"{'condition':<12} {'zopa':>6} {'N':>4} {'deal_rate':>10} {'mean_price':>11} "
          f"{'mean_ai_open':>13} {'mean_rounds':>12}")
    print("-" * 85)

    for key in sorted(groups.keys()):
        cond, zopa = key
        g = groups[key]
        n = len(g)
        deals = [r for r in g if r["deal_reached"]]
        deal_rate = len(deals) / n if n > 0 else 0

        prices = [r["deal_price"] for r in deals if r["deal_price"] is not None]
        mean_price = sum(prices) / len(prices) if prices else None

        opens = [r["ai_opening_offer"] for r in g if r["ai_opening_offer"] is not None]
        mean_open = sum(opens) / len(opens) if opens else None

        rounds = [r["rounds_to_deal"] for r in g]
        mean_rounds = sum(rounds) / len(rounds) if rounds else None

        print(f"{cond:<12} {zopa:>6} {n:>4} {deal_rate:>10.1%} "
              f"{mean_price if mean_price is not None else 'N/A':>11} "
              f"{mean_open if mean_open is not None else 'N/A':>13} "
              f"{mean_rounds if mean_rounds is not None else 'N/A':>12}")

    print("=" * 85)


if __name__ == "__main__":
    main()
