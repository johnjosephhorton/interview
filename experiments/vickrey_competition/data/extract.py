"""Extract structured data from Vickrey auction transcripts."""
import json
import re
import csv
import os
from pathlib import Path

# Paths
BASE = Path(__file__).resolve().parent.parent.parent.parent
TRANSCRIPT_DIR = BASE / "transcripts"
OUTPUT = Path(__file__).resolve().parent / "data.csv"

# Known valuations per round
HUMAN_VALS = [3.0, 8.0, 4.0, 9.0, 3.0, 7.0]
AI_VALS = [7.0, 4.0, 6.0, 3.0, 8.0, 5.0]
NPC_VALS = [5.0, 6.0, 8.0, 4.0, 6.0, 3.0]  # only for 3-bidder

# Conditions
CONDITIONS = {
    "vickrey_2bidder": {"competition_size": 2, "label": "2-bidder"},
    "vickrey_3bidder": {"competition_size": 3, "label": "3-bidder"},
}

def extract_round_data(manager_msg: str, condition: str, round_num: int):
    """Parse a manager round-result message to extract bids and outcomes."""
    data = {}

    # Extract human bid
    m = re.search(r"Your bid:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["human_bid"] = float(m.group(1))

    # Extract AI bid
    m = re.search(r"AI bid:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["ai_bid"] = float(m.group(1))

    # Extract third bidder bid (3-bidder only)
    m = re.search(r"Third bidder bid:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["third_bid"] = float(m.group(1))

    # Extract second price
    m = re.search(r"(?:Second[- ]highest bid|Second price)\s*\(?payment\)?:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["second_price"] = float(m.group(1))

    # Extract winner
    m = re.search(r"Winner:\s*(Human|AI|Third bidder)", manager_msg)
    if m:
        data["winner"] = m.group(1)

    # Extract human earnings for this round
    m = re.search(r"Your earnings:\s*\$?([\d.]+)", manager_msg)
    if m:
        data["human_earned"] = float(m.group(1))

    # Extract AI earnings for this round
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

    for msg in messages:
        if msg["role"] != "interviewer":
            continue
        text = msg["text"]

        # Check if this is a round result message
        if "Round" in text and "Result:" in text:
            round_num += 1
            if round_num > 6:
                break

            round_data = extract_round_data(text, condition, round_num)

            human_val = HUMAN_VALS[round_num - 1]
            ai_val = AI_VALS[round_num - 1]

            # Compute bid/valuation ratio
            human_bid = round_data.get("human_bid", None)
            bid_ratio = human_bid / human_val if human_bid is not None and human_val > 0 else None

            # Categorize valuation level
            val_category = "low" if human_val <= 4.0 else "high"

            # Check if AI bid correctly (truthful bidding)
            ai_bid = round_data.get("ai_bid", None)
            ai_bid_correct = abs(ai_bid - ai_val) < 0.01 if ai_bid is not None else None

            row = {
                "sim_id": sim_id,
                "condition": condition,
                "competition_size": CONDITIONS[condition]["competition_size"],
                "round": round_num,
                "human_valuation": human_val,
                "valuation_category": val_category,
                "human_bid": human_bid,
                "bid_valuation_ratio": round(bid_ratio, 4) if bid_ratio else None,
                "overbid": 1 if bid_ratio and bid_ratio > 1.0 else 0,
                "ai_valuation": ai_val,
                "ai_bid": ai_bid,
                "ai_bid_correct": ai_bid_correct,
                "second_price": round_data.get("second_price"),
                "winner": round_data.get("winner"),
                "human_earned": round_data.get("human_earned"),
                "ai_earned": round_data.get("ai_earned"),
            }

            if condition == "vickrey_3bidder":
                row["npc_valuation"] = NPC_VALS[round_num - 1]
                row["npc_bid"] = round_data.get("third_bid")
            else:
                row["npc_valuation"] = None
                row["npc_bid"] = None

            rows.append(row)

    return rows


def main():
    all_rows = []

    for condition in CONDITIONS:
        transcript_dir = TRANSCRIPT_DIR / condition
        if not transcript_dir.exists():
            print(f"Warning: {transcript_dir} not found, skipping")
            continue

        # Find passing transcripts
        check_files = sorted(transcript_dir.glob("*_check.json"))
        for check_file in check_files:
            with open(check_file) as f:
                check = json.load(f)
            if not check.get("overall_passed", False):
                continue

            # Get the corresponding transcript file
            transcript_file = Path(str(check_file).replace("_check.json", ".json"))
            if not transcript_file.exists():
                continue

            sim_id = f"{condition}_{transcript_file.stem}"
            rows = process_transcript(transcript_file, condition, sim_id)
            all_rows.append(rows)
            print(f"  {condition}: {transcript_file.name} -> {len(rows)} rounds")

    # Flatten
    flat = [row for rows in all_rows for row in rows]

    # Write CSV
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
