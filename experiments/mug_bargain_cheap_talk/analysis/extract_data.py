#!/usr/bin/env python3
"""Extract structured dataset from mug_bargain_cheap_talk simulation results."""

import csv
import json
import glob
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.dirname(__file__)

# Condition ID mapping from filenames
CONDITION_MAP = {
    "C01": "C01_none_narrow_twosided",
    "C02": "C02_none_narrow_onesided",
    "C03": "C03_none_wide_twosided",
    "C04": "C04_none_wide_onesided",
    "C05": "C05_talk1_narrow_twosided",
    "C06": "C06_talk1_narrow_onesided",
    "C07": "C07_talk1_wide_twosided",
    "C08": "C08_talk1_wide_onesided",
    "C09": "C09_ext_narrow_twosided",
    "C10": "C10_ext_narrow_onesided",
    "C11": "C11_ext_wide_twosided",
    "C12": "C12_ext_wide_onesided",
}


def extract_condition_id(filename):
    """Extract C01-C12 from filename like 2026-02-22_09-51-22_C01.json"""
    match = re.search(r"(C\d{2})", filename)
    return match.group(1) if match else "unknown"


def main():
    # Use production files only (prod_ prefix)
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*_prod_C*.json")))
    if not files:
        # Fallback to any timestamped files
        files = sorted(glob.glob(os.path.join(DATA_DIR, "2026-*_C*.json")))
    rows = []

    for filepath in files:
        fname = os.path.basename(filepath)
        cid_short = extract_condition_id(fname)
        cid_full = CONDITION_MAP.get(cid_short, cid_short)

        with open(filepath) as f:
            sims = json.load(f)

        for sim in sims:
            sid = sim.get("sim_id", 0)
            seed = sim.get("seed", "")

            # Treatment levels
            communication = sim.get("communication", "")
            value_gap = sim.get("value_gap", "")
            info_asymmetry = sim.get("info_asymmetry", "")

            # Ground truth
            buyer_wtp = sim.get("buyer_wtp", "")
            seller_wta = sim.get("seller_wta", "")
            gains = sim.get("gains_from_trade", "")
            feasible = 1 if sim.get("feasible", False) else 0

            # Primary outcomes
            deal = 1 if sim.get("deal", False) else 0
            final_price = sim.get("final_price", "")
            surplus_captured = sim.get("surplus_captured", "")
            price_split = sim.get("price_split_ratio", "")
            rounds = sim.get("rounds_to_agreement", "")
            bargain_rounds = sim.get("bargain_rounds_played", "")

            # Earnings
            buyer_earn = sim.get("buyer_earnings", "")
            seller_earn = sim.get("seller_earnings", "")

            # Communication data
            n_comm_messages = len(sim.get("comm_messages", []))
            n_value_signals = len(sim.get("comm_value_signals", []))

            # Check for guardrail triggers in bargaining history
            guardrail_triggered = 0
            for h in sim.get("bargain_history", []):
                if "GUARDRAIL" in str(h.get("raw", "")):
                    guardrail_triggered = 1

            rows.append({
                "experiment_name": "mug_bargain_cheap_talk",
                "condition_id": cid_full,
                "condition_short": cid_short,
                "session_id": f"{cid_short}_s{sid}",
                "seed": seed,
                "communication": communication,
                "value_gap": value_gap,
                "info_asymmetry": info_asymmetry,
                "buyer_wtp": buyer_wtp,
                "seller_wta": seller_wta,
                "gains_from_trade": gains,
                "feasible": feasible,
                "deal": deal,
                "final_price": final_price if final_price else "",
                "surplus_captured": surplus_captured if surplus_captured is not None else "",
                "price_split_ratio": price_split if price_split is not None else "",
                "rounds_to_agreement": rounds if rounds else "",
                "bargain_rounds_played": bargain_rounds,
                "buyer_earnings": buyer_earn,
                "seller_earnings": seller_earn,
                "n_comm_messages": n_comm_messages,
                "n_value_signals": n_value_signals,
                "guardrail_triggered": guardrail_triggered,
            })

    # Write raw_sessions.csv
    outpath = os.path.join(OUT_DIR, "raw_sessions.csv")
    fieldnames = list(rows[0].keys())
    with open(outpath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {outpath}")


if __name__ == "__main__":
    main()
