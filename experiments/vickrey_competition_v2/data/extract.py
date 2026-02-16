"""Extract structured data from first-price auction transcripts (v2 experiment)."""
import json
import re
import csv
from pathlib import Path

# Paths
BASE = Path(__file__).resolve().parent.parent.parent.parent
TRANSCRIPT_DIR = BASE / "transcripts"
OUTPUT = Path(__file__).resolve().parent / "data.csv"

# Known valuations per round (same across conditions)
HUMAN_VALS = [3.0, 8.0, 4.0, 9.0, 3.0, 7.0]
AI_VALS = [7.0, 4.0, 6.0, 3.0, 8.0, 5.0]
NPC_VALS = [5.0, 6.0, 8.0, 4.0, 6.0, 3.0]  # only for 3-bidder

# Nash equilibrium bid ratios: bid = val * (n-1)/n
NASH_RATIOS = {2: 0.50, 3: 2.0 / 3.0}  # 0.50 for 2-bidder, 0.6667 for 3-bidder

# Expected AI bids (Nash equilibrium)
AI_BIDS_2 = [v * 0.50 for v in AI_VALS]  # [3.50, 2.00, 3.00, 1.50, 4.00, 2.50]
AI_BIDS_3 = [round(v * 2 / 3, 2) for v in AI_VALS]  # [4.67, 2.67, 4.00, 2.00, 5.33, 3.33]
NPC_BIDS = [round(v * 2 / 3, 2) for v in NPC_VALS]  # [3.33, 4.00, 5.33, 2.67, 4.00, 2.00]

# Conditions
CONDITIONS = {
    "auction_2bidder": {"competition_size": 2, "nash_ratio": 0.50, "label": "2-bidder"},
    "auction_3bidder": {"competition_size": 3, "nash_ratio": 2.0 / 3.0, "label": "3-bidder"},
}


def extract_round_data(manager_msg: str):
    """Parse a manager round-result message to extract bids and outcomes."""
    data = {}

    m = re.search(r"Your bid:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["human_bid"] = float(m.group(1))

    m = re.search(r"AI bid:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["ai_bid"] = float(m.group(1))

    m = re.search(r"Third bidder bid:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["third_bid"] = float(m.group(1))

    m = re.search(r"Winner:\s*(Human|AI|Third bidder)", manager_msg)
    if m:
        data["winner"] = m.group(1)

    m = re.search(r"Your earnings:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["human_earned"] = float(m.group(1))

    m = re.search(r"AI earnings:\s*\$?(-?[\d.]+)", manager_msg)
    if m:
        data["ai_earned"] = float(m.group(1))

    return data


def process_transcript(filepath: Path, condition: str, sim_id: str):
    """Process one transcript file and return rows of round-level data."""
    with open(filepath) as f:
        transcript = json.load(f)

    messages = transcript["messages"]
    rows = []
    round_num = 0
    comp_size = CONDITIONS[condition]["competition_size"]
    nash_ratio = CONDITIONS[condition]["nash_ratio"]

    for msg in messages:
        if msg["role"] != "interviewer":
            continue
        text = msg["text"]

        if "Round" in text and "Result:" in text:
            round_num += 1
            if round_num > 6:
                break

            round_data = extract_round_data(text)

            human_val = HUMAN_VALS[round_num - 1]
            ai_val = AI_VALS[round_num - 1]

            human_bid = round_data.get("human_bid")
            bid_ratio = human_bid / human_val if human_bid is not None and human_val > 0 else None

            # Overbidding gap = observed ratio - Nash ratio
            overbid_gap = bid_ratio - nash_ratio if bid_ratio is not None else None

            # Nash bid for reference
            nash_bid = human_val * nash_ratio

            val_category = "low" if human_val <= 4.0 else "high"

            # Check AI bid correctness
            ai_bid = round_data.get("ai_bid")
            if comp_size == 2:
                expected_ai_bid = AI_BIDS_2[round_num - 1]
            else:
                expected_ai_bid = AI_BIDS_3[round_num - 1]
            ai_bid_correct = abs(ai_bid - expected_ai_bid) < 0.02 if ai_bid is not None else None

            row = {
                "sim_id": sim_id,
                "condition": condition,
                "competition_size": comp_size,
                "round": round_num,
                "human_valuation": human_val,
                "valuation_category": val_category,
                "human_bid": human_bid,
                "bid_valuation_ratio": round(bid_ratio, 4) if bid_ratio is not None else None,
                "nash_ratio": round(nash_ratio, 4),
                "nash_bid": round(nash_bid, 2),
                "overbid_gap": round(overbid_gap, 4) if overbid_gap is not None else None,
                "overbid_vs_valuation": 1 if bid_ratio is not None and bid_ratio > 1.0 else 0,
                "ai_valuation": ai_val,
                "ai_bid": ai_bid,
                "ai_bid_expected": expected_ai_bid,
                "ai_bid_correct": ai_bid_correct,
                "winner": round_data.get("winner"),
                "human_earned": round_data.get("human_earned"),
                "ai_earned": round_data.get("ai_earned"),
            }

            if comp_size == 3:
                row["npc_valuation"] = NPC_VALS[round_num - 1]
                row["npc_bid"] = round_data.get("third_bid")
                row["npc_bid_expected"] = NPC_BIDS[round_num - 1]
            else:
                row["npc_valuation"] = None
                row["npc_bid"] = None
                row["npc_bid_expected"] = None

            rows.append(row)

    return rows


def main():
    all_rows = []

    for condition in CONDITIONS:
        transcript_dir = TRANSCRIPT_DIR / condition
        if not transcript_dir.exists():
            print(f"Warning: {transcript_dir} not found, skipping")
            continue

        check_files = sorted(transcript_dir.glob("*_check.json"))
        for check_file in check_files:
            with open(check_file) as f:
                check = json.load(f)
            if not check.get("overall_passed", False):
                print(f"  SKIP (failed): {check_file.name}")
                continue

            transcript_file = Path(str(check_file).replace("_check.json", ".json"))
            if not transcript_file.exists():
                continue

            sim_id = f"{condition}_{transcript_file.stem}"
            rows = process_transcript(transcript_file, condition, sim_id)
            all_rows.append(rows)
            print(f"  {condition}: {transcript_file.name} -> {len(rows)} rounds")

    flat = [row for rows in all_rows for row in rows]

    if flat:
        fieldnames = list(flat[0].keys())
        with open(OUTPUT, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat)
        print(f"\nWrote {len(flat)} rows to {OUTPUT}")
    else:
        print("No data extracted!")


if __name__ == "__main__":
    main()
