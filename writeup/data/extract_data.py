"""
Extract structured data from info_source_bargaining experiment transcripts.
Reads 90 simulation transcripts (30 per condition) and outputs a CSV.
"""

import json, glob, re, csv, os

os.makedirs('writeup/data', exist_ok=True)

conditions_map = {
    "bargain_source_none": "transcripts/bargain_source_none/2026-02-12_14-35-08_sim*.json",
    "bargain_source_verified": "transcripts/bargain_source_verified/2026-02-12_14-36-57_sim*.json",
    "bargain_source_claimed": "transcripts/bargain_source_claimed/2026-02-12_14-40-08_sim*.json",
}

rows = []


def safe_float(s):
    """Convert string to float, stripping trailing periods."""
    return float(s.rstrip('.'))


for condition, pattern in conditions_map.items():
    files = sorted([f for f in glob.glob(pattern) if '_check' not in f])
    for f in files:
        sim_match = re.search(r'sim(\d+)\.json$', f)
        sim_id = int(sim_match.group(1)) if sim_match else 0

        data = json.load(open(f))
        messages = data.get("messages", [])
        conds = data.get("conditions", {})

        # Token usage
        input_tokens = data.get("total_input_tokens", 0)
        output_tokens = data.get("total_output_tokens", 0)

        # Checker result from corresponding _check.json
        check_file = f.replace('.json', '_check.json')
        checker_passed = None
        try:
            check_data = json.load(open(check_file))
            checker_passed = check_data.get("overall_passed", None)
        except (FileNotFoundError, json.JSONDecodeError):
            checker_passed = None

        # Parse messages
        full_text = "\n".join(m.get("text", "") for m in messages)

        # Initialize outcome variables
        deal_reached = False
        deal_price = None
        human_earnings = None
        ai_earnings = None
        final_round = None
        first_offer = None
        first_human_response = None
        first_human_counteroffer = None
        rounds_played = 0

        # ---- Extract from GAME OVER box ----
        game_over_match = re.search(r'GAME OVER.*', full_text, re.DOTALL)
        game_over_text = game_over_match.group(0) if game_over_match else ""

        # Extract earnings from GAME OVER box
        human_earn_match = re.search(r'Human:\s*\$?([\d.]+)', game_over_text)
        ai_earn_match = re.search(r'AI:\s*\$?([\d.]+)', game_over_text)
        if human_earn_match:
            human_earnings = safe_float(human_earn_match.group(1))
        if ai_earn_match:
            ai_earnings = safe_float(ai_earn_match.group(1))

        # Determine deal status
        if human_earnings is not None and human_earnings > 0:
            deal_reached = True
        elif human_earnings is not None and human_earnings == 0 and ai_earnings is not None and ai_earnings == 0:
            deal_reached = False
        else:
            # Fallback: check for "Deal reached" text
            if re.search(r'[Dd]eal\s+reached', full_text):
                deal_reached = True

        # ---- Extract deal price ----
        # Try "Deal reached at $X" pattern
        deal_at_match = re.search(r'[Dd]eal\s+reached\s+at\s+\$?([\d.]+)', full_text)
        if deal_at_match:
            deal_price = safe_float(deal_at_match.group(1))
        elif deal_reached and human_earnings is not None:
            # Infer from earnings: human_earnings = buyer_value - price
            buyer_value = conds.get("buyer_value", 80)
            deal_price = buyer_value - human_earnings

        # ---- Count rounds and find final round ----
        round_mentions = re.findall(r'Round\s+(\d+)', full_text)
        if round_mentions:
            rounds_played = max(int(r) for r in round_mentions)

        # Final round = round where deal was made
        if deal_reached:
            last_round_seen = 1
            for i, m in enumerate(messages):
                round_in_msg = re.findall(r'Round\s+(\d+)', m.get("text", ""))
                if round_in_msg:
                    last_round_seen = max(int(r) for r in round_in_msg)
                # If respondent says "accept"
                if m.get("role") == "respondent" and re.search(r'accept', m.get("text", ""), re.IGNORECASE):
                    final_round = last_round_seen
                    break
                # If manager announces AI accepted the human's offer
                if m.get("role") == "interviewer" and re.search(r'AI\s+accepts', m.get("text", ""), re.IGNORECASE):
                    human_offer_rounds = re.findall(r'Round\s+(\d+):\s+You\s+offered', m.get("text", ""))
                    if human_offer_rounds:
                        final_round = int(human_offer_rounds[-1])
                    else:
                        final_round = last_round_seen

            if final_round is None:
                final_round = last_round_seen

        # ---- Extract first offer (AI's Round 1 price) ----
        opening_msg = messages[0].get("text", "") if messages else ""
        first_offer_match = re.search(r'(?:AI|seller)\s+offers?\s+\$?([\d.]+)', opening_msg, re.IGNORECASE)
        if not first_offer_match:
            first_offer_match = re.search(r'offers?\s+\$?([\d.]+)', opening_msg, re.IGNORECASE)
        if first_offer_match:
            first_offer = safe_float(first_offer_match.group(1))

        # ---- Extract first human response ----
        if len(messages) >= 2:
            first_resp = messages[1]
            if first_resp.get("role") == "respondent":
                resp_text = first_resp.get("text", "").strip()
                if re.search(r'^accept$', resp_text, re.IGNORECASE):
                    first_human_response = "accept"
                else:
                    counter_match = re.search(r'\$?([\d.]+)', resp_text)
                    if counter_match:
                        first_human_response = "counteroffer"
                        first_human_counteroffer = safe_float(counter_match.group(1))
                    else:
                        first_human_response = resp_text[:50]

        # ---- Calculate surplus and efficiency ----
        buyer_value = conds.get("buyer_value", 80)
        seller_cost = conds.get("seller_cost", 50)
        zopa = buyer_value - seller_cost

        total_surplus = None
        efficiency = None
        if human_earnings is not None and ai_earnings is not None:
            total_surplus = round(human_earnings + ai_earnings, 2)
            efficiency = round(total_surplus / zopa, 4) if zopa > 0 else None

        buyer_share = None
        if deal_reached and human_earnings is not None and total_surplus and total_surplus > 0:
            buyer_share = round(human_earnings / total_surplus, 4)

        row = {
            "condition": condition,
            "sim_id": sim_id,
            "deal_reached": deal_reached,
            "deal_price": deal_price,
            "rounds_played": rounds_played,
            "final_round": final_round,
            "human_earnings": human_earnings,
            "ai_earnings": ai_earnings,
            "total_surplus": total_surplus,
            "efficiency": efficiency,
            "buyer_share": buyer_share,
            "first_offer": first_offer,
            "first_human_response": first_human_response,
            "first_human_counteroffer": first_human_counteroffer,
            "buyer_value": conds.get("buyer_value"),
            "seller_cost": conds.get("seller_cost"),
            "opening_price": conds.get("opening_price"),
            "accept_threshold": conds.get("accept_threshold"),
            "buyer_accept_threshold": conds.get("buyer_accept_threshold"),
            "info_range_low": conds.get("info_range_low"),
            "info_range_high": conds.get("info_range_high"),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "checker_passed": checker_passed,
        }
        rows.append(row)

# Write CSV
outpath = 'writeup/data/info_source_bargaining_data.csv'
fieldnames = list(rows[0].keys()) if rows else []
with open(outpath, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Extracted {len(rows)} transcripts -> {outpath}")

# ---- Summary statistics ----
import collections

by_cond = collections.defaultdict(list)
for r in rows:
    by_cond[r["condition"]].append(r)

for cond in ["bargain_source_none", "bargain_source_verified", "bargain_source_claimed"]:
    rr = by_cond[cond]
    n = len(rr)
    deals = sum(1 for r in rr if r["deal_reached"])
    prices = [r["deal_price"] for r in rr if r["deal_price"] is not None]
    rounds = [r["rounds_played"] for r in rr if r["rounds_played"]]
    h_earn = [r["human_earnings"] for r in rr if r["human_earnings"] is not None]
    a_earn = [r["ai_earnings"] for r in rr if r["ai_earnings"] is not None]
    first_accepts = sum(1 for r in rr if r["first_human_response"] == "accept")
    counters = [r["first_human_counteroffer"] for r in rr if r["first_human_counteroffer"] is not None]
    surpluses = [r["total_surplus"] for r in rr if r["total_surplus"] is not None]
    buyer_shares = [r["buyer_share"] for r in rr if r["buyer_share"] is not None]
    checkers_passed = sum(1 for r in rr if r["checker_passed"] is True)

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0

    def sd(xs):
        m = mean(xs)
        return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5 if xs else 0

    print(f"\n{'='*60}")
    print(f"{cond} (N={n})")
    print(f"{'='*60}")
    print(f"  Deal rate:            {deals}/{n} ({100*deals/n:.0f}%)")
    if prices:
        print(f"  Mean deal price:      ${mean(prices):.2f} (SD={sd(prices):.2f})")
        print(f"  Price range:          ${min(prices):.2f} - ${max(prices):.2f}")
    if rounds:
        print(f"  Mean rounds played:   {mean(rounds):.1f} (SD={sd(rounds):.1f})")
    if h_earn:
        print(f"  Mean human earnings:  ${mean(h_earn):.2f} (SD={sd(h_earn):.2f})")
    if a_earn:
        print(f"  Mean AI earnings:     ${mean(a_earn):.2f} (SD={sd(a_earn):.2f})")
    if surpluses:
        print(f"  Mean total surplus:   ${mean(surpluses):.2f} (SD={sd(surpluses):.2f})")
    if buyer_shares:
        print(f"  Mean buyer share:     {100*mean(buyer_shares):.1f}%")
    print(f"  First-round accepts:  {first_accepts}/{n} ({100*first_accepts/n:.0f}%)")
    if counters:
        print(f"  Mean 1st counteroffer: ${mean(counters):.2f} (SD={sd(counters):.2f})")
    print(f"  Checker passed:       {checkers_passed}/{n}")
