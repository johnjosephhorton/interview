"""Analyze Vickrey auction competition experiment data."""
import csv
import os
from pathlib import Path
from collections import defaultdict

DATA = Path(__file__).resolve().parent / "data.csv"

def load_data():
    with open(DATA) as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # Convert types
            row["competition_size"] = int(row["competition_size"])
            row["round"] = int(row["round"])
            row["human_valuation"] = float(row["human_valuation"])
            row["human_bid"] = float(row["human_bid"]) if row["human_bid"] else None
            row["bid_valuation_ratio"] = float(row["bid_valuation_ratio"]) if row["bid_valuation_ratio"] else None
            row["overbid"] = int(row["overbid"])
            row["ai_bid"] = float(row["ai_bid"]) if row["ai_bid"] else None
            row["human_earned"] = float(row["human_earned"]) if row["human_earned"] else None
            rows.append(row)
        return rows

def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else 0

def std(values):
    values = [v for v in values if v is not None]
    if len(values) < 2:
        return 0
    m = mean(values)
    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5

def main():
    rows = load_data()

    print("=" * 70)
    print("VICKREY COMPETITION EXPERIMENT — ANALYSIS REPORT")
    print("=" * 70)

    # ---- 1. Data overview ----
    print("\n1. DATA OVERVIEW")
    print("-" * 40)

    cond_2 = [r for r in rows if r["competition_size"] == 2]
    cond_3 = [r for r in rows if r["competition_size"] == 3]

    sims_2 = len(set(r["sim_id"] for r in cond_2))
    sims_3 = len(set(r["sim_id"] for r in cond_3))

    print(f"  2-bidder: {sims_2} simulations, {len(cond_2)} round-level observations")
    print(f"  3-bidder: {sims_3} simulations, {len(cond_3)} round-level observations")
    print(f"  Total: {len(rows)} observations")

    # ---- 2. AI bid correctness ----
    print("\n2. AI BID CORRECTNESS (sanity check)")
    print("-" * 40)

    ai_correct_2 = sum(1 for r in cond_2 if r.get("ai_bid_correct") == "True")
    ai_correct_3 = sum(1 for r in cond_3 if r.get("ai_bid_correct") == "True")

    print(f"  2-bidder: {ai_correct_2}/{len(cond_2)} rounds AI bid correctly ({100*ai_correct_2/len(cond_2):.0f}%)")
    print(f"  3-bidder: {ai_correct_3}/{len(cond_3)} rounds AI bid correctly ({100*ai_correct_3/len(cond_3):.0f}%)")

    # ---- 3. Primary outcome: Bid/Valuation Ratio ----
    print("\n3. PRIMARY OUTCOME: BID/VALUATION RATIO")
    print("-" * 40)

    ratios_2 = [r["bid_valuation_ratio"] for r in cond_2]
    ratios_3 = [r["bid_valuation_ratio"] for r in cond_3]

    print(f"  2-bidder: mean = {mean(ratios_2):.4f}, std = {std(ratios_2):.4f}, n = {len(ratios_2)}")
    print(f"  3-bidder: mean = {mean(ratios_3):.4f}, std = {std(ratios_3):.4f}, n = {len(ratios_3)}")
    print(f"  Difference: {mean(ratios_3) - mean(ratios_2):+.4f}")

    # t-test (manual Welch's)
    n1, n2 = len(ratios_2), len(ratios_3)
    m1, m2 = mean(ratios_2), mean(ratios_3)
    s1, s2 = std(ratios_2), std(ratios_3)

    if s1 > 0 and s2 > 0:
        se = (s1**2/n1 + s2**2/n2) ** 0.5
        t_stat = (m2 - m1) / se if se > 0 else 0
        print(f"  Welch's t = {t_stat:.3f} (positive = 3-bidder higher)")

    # ---- 4. Key interaction: Competition x Valuation Level ----
    print("\n4. KEY INTERACTION: COMPETITION x VALUATION LEVEL")
    print("-" * 40)

    groups = defaultdict(list)
    for r in rows:
        key = (r["competition_size"], r["valuation_category"])
        groups[key].append(r["bid_valuation_ratio"])

    print(f"\n  {'':20s} {'2-bidder':>12s} {'3-bidder':>12s} {'Diff':>10s}")
    print(f"  {'':20s} {'─'*12:s} {'─'*12:s} {'─'*10:s}")

    for val_cat in ["low", "high"]:
        m2v = mean(groups.get((2, val_cat), []))
        m3v = mean(groups.get((3, val_cat), []))
        diff = m3v - m2v
        n2v = len(groups.get((2, val_cat), []))
        n3v = len(groups.get((3, val_cat), []))
        print(f"  {val_cat.capitalize() + ' valuation':20s} {m2v:>8.4f} (n={n2v:d}) {m3v:>8.4f} (n={n3v:d}) {diff:>+8.4f}")

    # Interaction = (3bid_low - 2bid_low) - (3bid_high - 2bid_high)
    low_diff = mean(groups.get((3, "low"), [])) - mean(groups.get((2, "low"), []))
    high_diff = mean(groups.get((3, "high"), [])) - mean(groups.get((2, "high"), []))
    interaction = low_diff - high_diff

    print(f"\n  Competition effect on LOW valuation:  {low_diff:+.4f}")
    print(f"  Competition effect on HIGH valuation: {high_diff:+.4f}")
    print(f"  INTERACTION (low - high):             {interaction:+.4f}")
    print(f"  Predicted direction:                  positive (low > high)")
    print(f"  Observed direction:                   {'CONFIRMED' if interaction > 0 else 'REFUTED'}")

    # ---- 5. Overbidding frequency ----
    print("\n5. OVERBIDDING FREQUENCY (bid > valuation)")
    print("-" * 40)

    overbid_2 = sum(r["overbid"] for r in cond_2)
    overbid_3 = sum(r["overbid"] for r in cond_3)

    print(f"  2-bidder: {overbid_2}/{len(cond_2)} rounds ({100*overbid_2/len(cond_2):.1f}%)")
    print(f"  3-bidder: {overbid_3}/{len(cond_3)} rounds ({100*overbid_3/len(cond_3):.1f}%)")

    # By valuation level
    for val_cat in ["low", "high"]:
        ob2 = sum(r["overbid"] for r in cond_2 if r["valuation_category"] == val_cat)
        n2v = sum(1 for r in cond_2 if r["valuation_category"] == val_cat)
        ob3 = sum(r["overbid"] for r in cond_3 if r["valuation_category"] == val_cat)
        n3v = sum(1 for r in cond_3 if r["valuation_category"] == val_cat)
        print(f"  {val_cat.capitalize()} val: 2-bidder {ob2}/{n2v} ({100*ob2/n2v:.0f}%) vs 3-bidder {ob3}/{n3v} ({100*ob3/n3v:.0f}%)")

    # ---- 6. Total earnings ----
    print("\n6. TOTAL EARNINGS BY CONDITION")
    print("-" * 40)

    earnings_by_sim = defaultdict(float)
    for r in rows:
        if r["human_earned"] is not None:
            earnings_by_sim[(r["condition"], r["sim_id"])] += r["human_earned"]

    earn_2 = [v for (c, _), v in earnings_by_sim.items() if "2bidder" in c]
    earn_3 = [v for (c, _), v in earnings_by_sim.items() if "3bidder" in c]

    print(f"  2-bidder: mean total earnings = ${mean(earn_2):.2f} (std = ${std(earn_2):.2f})")
    print(f"  3-bidder: mean total earnings = ${mean(earn_3):.2f} (std = ${std(earn_3):.2f})")
    print(f"  Difference: ${mean(earn_3) - mean(earn_2):+.2f}")

    # ---- 7. Round-by-round patterns ----
    print("\n7. ROUND-BY-ROUND BID RATIOS")
    print("-" * 40)

    print(f"\n  {'Round':>5s} {'2-bidder':>10s} {'3-bidder':>10s} {'Diff':>8s} {'Human Val':>10s}")
    print(f"  {'─'*5:s} {'─'*10:s} {'─'*10:s} {'─'*8:s} {'─'*10:s}")

    for rnd in range(1, 7):
        r2 = [r["bid_valuation_ratio"] for r in cond_2 if r["round"] == rnd]
        r3 = [r["bid_valuation_ratio"] for r in cond_3 if r["round"] == rnd]
        m2r = mean(r2)
        m3r = mean(r3)
        print(f"  {rnd:>5d} {m2r:>10.4f} {m3r:>10.4f} {m3r-m2r:>+8.4f} {'$'+str(HUMAN_VALS[rnd-1]):>10s}")

    # ---- 8. Individual bid distributions ----
    print("\n8. INDIVIDUAL BIDS BY CONDITION AND ROUND")
    print("-" * 40)

    for rnd in range(1, 7):
        bids_2 = [r["human_bid"] for r in cond_2 if r["round"] == rnd and r["human_bid"] is not None]
        bids_3 = [r["human_bid"] for r in cond_3 if r["round"] == rnd and r["human_bid"] is not None]
        val = HUMAN_VALS[rnd - 1]
        cat = "LOW" if val <= 4 else "HIGH"
        print(f"  R{rnd} (val=${val:.0f}, {cat}): 2bid={[f'{b:.2f}' for b in bids_2]}  3bid={[f'{b:.2f}' for b in bids_3]}")

    # ---- 9. Prediction evaluation ----
    print("\n" + "=" * 70)
    print("PREDICTION EVALUATION")
    print("=" * 70)

    # P1: Main effect
    main_effect = mean(ratios_3) - mean(ratios_2)
    p1 = "CONFIRMED" if main_effect > 0.01 else ("REFUTED" if main_effect < -0.01 else "NULL")
    print(f"\n  P1. Main effect (3-bidder > 2-bidder): {main_effect:+.4f} → {p1}")

    # P2: Interaction
    p2 = "CONFIRMED" if interaction > 0.01 else ("REFUTED" if interaction < -0.01 else "NULL")
    print(f"  P2. Interaction (low > high effect):   {interaction:+.4f} → {p2}")

    # P3: Overbid frequency
    ob_diff = (overbid_3/len(cond_3)) - (overbid_2/len(cond_2))
    p3 = "CONFIRMED" if ob_diff > 0.01 else ("REFUTED" if ob_diff < -0.01 else "NULL")
    print(f"  P3. Overbid frequency higher:          {ob_diff:+.4f} → {p3}")

    # P4: Earnings lower
    earn_diff = mean(earn_3) - mean(earn_2)
    p4 = "CONFIRMED" if earn_diff < -0.01 else ("REFUTED" if earn_diff > 0.01 else "NULL")
    print(f"  P4. Earnings lower in 3-bidder:        ${earn_diff:+.2f} → {p4}")

    # Overall verdict
    confirmed_count = sum(1 for p in [p1, p2, p3, p4] if p == "CONFIRMED")
    if confirmed_count >= 3:
        verdict = "YES_INTERESTING"
    elif confirmed_count >= 1:
        verdict = "PARTIALLY"
    else:
        verdict = "NO_NULL"

    print(f"\n  VERDICT: {verdict} ({confirmed_count}/4 predictions confirmed)")

    # Human vals for reference
    HUMAN_VALS_REF = [3.0, 8.0, 4.0, 9.0, 3.0, 7.0]


# Import human vals at module level
HUMAN_VALS = [3.0, 8.0, 4.0, 9.0, 3.0, 7.0]

if __name__ == "__main__":
    main()
