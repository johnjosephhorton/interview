"""Analyze first-price auction competition experiment data (v2)."""
import csv
from pathlib import Path
from collections import defaultdict

DATA = Path(__file__).resolve().parent / "data.csv"

HUMAN_VALS = [3.0, 8.0, 4.0, 9.0, 3.0, 7.0]


def load_data():
    with open(DATA) as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            row["competition_size"] = int(row["competition_size"])
            row["round"] = int(row["round"])
            row["human_valuation"] = float(row["human_valuation"])
            row["human_bid"] = float(row["human_bid"]) if row["human_bid"] else None
            row["bid_valuation_ratio"] = float(row["bid_valuation_ratio"]) if row["bid_valuation_ratio"] else None
            row["nash_ratio"] = float(row["nash_ratio"]) if row["nash_ratio"] else None
            row["overbid_gap"] = float(row["overbid_gap"]) if row["overbid_gap"] else None
            row["overbid_vs_valuation"] = int(row["overbid_vs_valuation"])
            row["ai_bid"] = float(row["ai_bid"]) if row["ai_bid"] else None
            row["human_earned"] = float(row["human_earned"]) if row["human_earned"] else None
            row["ai_earned"] = float(row["ai_earned"]) if row["ai_earned"] else None
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
    print("FIRST-PRICE AUCTION COMPETITION EXPERIMENT (v2) — ANALYSIS")
    print("=" * 70)

    # ---- 1. Data overview ----
    print("\n1. DATA OVERVIEW")
    print("-" * 50)

    cond_2 = [r for r in rows if r["competition_size"] == 2]
    cond_3 = [r for r in rows if r["competition_size"] == 3]

    sims_2 = len(set(r["sim_id"] for r in cond_2))
    sims_3 = len(set(r["sim_id"] for r in cond_3))

    print(f"  2-bidder: {sims_2} simulations, {len(cond_2)} round-level observations")
    print(f"  3-bidder: {sims_3} simulations, {len(cond_3)} round-level observations")
    print(f"  Total: {len(rows)} observations")

    # ---- 2. AI bid correctness ----
    print("\n2. AI BID CORRECTNESS (sanity check)")
    print("-" * 50)

    ai_correct_2 = sum(1 for r in cond_2 if str(r.get("ai_bid_correct")) == "True")
    ai_correct_3 = sum(1 for r in cond_3 if str(r.get("ai_bid_correct")) == "True")

    print(f"  2-bidder: {ai_correct_2}/{len(cond_2)} ({100*ai_correct_2/max(len(cond_2),1):.0f}%)")
    print(f"  3-bidder: {ai_correct_3}/{len(cond_3)} ({100*ai_correct_3/max(len(cond_3),1):.0f}%)")

    # ---- 3. Primary outcome: Bid/Valuation Ratio ----
    print("\n3. PRIMARY OUTCOME: BID/VALUATION RATIO")
    print("-" * 50)

    ratios_2 = [r["bid_valuation_ratio"] for r in cond_2]
    ratios_3 = [r["bid_valuation_ratio"] for r in cond_3]

    print(f"  2-bidder: mean = {mean(ratios_2):.4f}, std = {std(ratios_2):.4f}, n = {len(ratios_2)}")
    print(f"  3-bidder: mean = {mean(ratios_3):.4f}, std = {std(ratios_3):.4f}, n = {len(ratios_3)}")
    print(f"  Difference: {mean(ratios_3) - mean(ratios_2):+.4f}")
    print(f"  Nash equilibrium ratios: 2-bidder = 0.5000, 3-bidder = 0.6667")

    # t-test
    n1, n2 = len(ratios_2), len(ratios_3)
    m1, m2 = mean(ratios_2), mean(ratios_3)
    s1, s2 = std(ratios_2), std(ratios_3)

    if s1 > 0 and s2 > 0:
        se = (s1**2 / n1 + s2**2 / n2) ** 0.5
        t_stat = (m2 - m1) / se if se > 0 else 0
        print(f"  Welch's t = {t_stat:.3f} (positive = 3-bidder higher)")

    # ---- 4. Key outcome: Overbidding gap (bid ratio - Nash ratio) ----
    print("\n4. KEY OUTCOME: OVERBIDDING GAP (bid ratio - Nash ratio)")
    print("-" * 50)

    gaps_2 = [r["overbid_gap"] for r in cond_2]
    gaps_3 = [r["overbid_gap"] for r in cond_3]

    mg2, mg3 = mean(gaps_2), mean(gaps_3)
    sg2, sg3 = std(gaps_2), std(gaps_3)

    print(f"  2-bidder: mean gap = {mg2:+.4f}, std = {sg2:.4f}, n = {len(gaps_2)}")
    print(f"    (bid ratio {mean(ratios_2):.4f} vs Nash 0.5000)")
    print(f"  3-bidder: mean gap = {mg3:+.4f}, std = {sg3:.4f}, n = {len(gaps_3)}")
    print(f"    (bid ratio {mean(ratios_3):.4f} vs Nash 0.6667)")
    print(f"  Gap difference (3b - 2b): {mg3 - mg2:+.4f}")

    if sg2 > 0 and sg3 > 0:
        se_gap = (sg2**2 / len(gaps_2) + sg3**2 / len(gaps_3)) ** 0.5
        t_gap = (mg3 - mg2) / se_gap if se_gap > 0 else 0
        print(f"  Welch's t (gap): {t_gap:.3f}")

    # ---- 5. Key interaction: Competition x Valuation Level ----
    print("\n5. INTERACTION: COMPETITION x VALUATION LEVEL")
    print("-" * 50)

    groups_ratio = defaultdict(list)
    groups_gap = defaultdict(list)
    for r in rows:
        key = (r["competition_size"], r["valuation_category"])
        groups_ratio[key].append(r["bid_valuation_ratio"])
        groups_gap[key].append(r["overbid_gap"])

    print(f"\n  BID/VALUATION RATIO:")
    print(f"  {'':20s} {'2-bidder':>12s} {'3-bidder':>12s} {'Diff':>10s}")
    print(f"  {'':20s} {'─' * 12:s} {'─' * 12:s} {'─' * 10:s}")

    for val_cat in ["low", "high"]:
        m2v = mean(groups_ratio.get((2, val_cat), []))
        m3v = mean(groups_ratio.get((3, val_cat), []))
        diff = m3v - m2v
        n2v = len(groups_ratio.get((2, val_cat), []))
        n3v = len(groups_ratio.get((3, val_cat), []))
        print(f"  {val_cat.capitalize() + ' val':20s} {m2v:>8.4f} (n={n2v:d}) {m3v:>8.4f} (n={n3v:d}) {diff:>+8.4f}")

    print(f"\n  OVERBIDDING GAP (ratio - Nash):")
    print(f"  {'':20s} {'2-bidder':>12s} {'3-bidder':>12s} {'Diff':>10s}")
    print(f"  {'':20s} {'─' * 12:s} {'─' * 12:s} {'─' * 10:s}")

    for val_cat in ["low", "high"]:
        m2v = mean(groups_gap.get((2, val_cat), []))
        m3v = mean(groups_gap.get((3, val_cat), []))
        diff = m3v - m2v
        n2v = len(groups_gap.get((2, val_cat), []))
        n3v = len(groups_gap.get((3, val_cat), []))
        print(f"  {val_cat.capitalize() + ' val':20s} {m2v:>+8.4f} (n={n2v:d}) {m3v:>+8.4f} (n={n3v:d}) {diff:>+8.4f}")

    # Interaction on gap
    low_diff = mean(groups_gap.get((3, "low"), [])) - mean(groups_gap.get((2, "low"), []))
    high_diff = mean(groups_gap.get((3, "high"), [])) - mean(groups_gap.get((2, "high"), []))
    interaction = low_diff - high_diff

    print(f"\n  Competition effect on LOW val gap:   {low_diff:+.4f}")
    print(f"  Competition effect on HIGH val gap:  {high_diff:+.4f}")
    print(f"  INTERACTION (low - high):            {interaction:+.4f}")
    print(f"  Predicted direction:                 positive (low > high)")
    print(f"  Observed:                            {'CONFIRMED' if interaction > 0 else 'REFUTED'}")

    # ---- 6. Overbidding vs valuation frequency ----
    print("\n6. OVERBIDDING vs VALUATION (bid > valuation)")
    print("-" * 50)

    ob_2 = sum(r["overbid_vs_valuation"] for r in cond_2)
    ob_3 = sum(r["overbid_vs_valuation"] for r in cond_3)

    print(f"  2-bidder: {ob_2}/{len(cond_2)} ({100 * ob_2 / max(len(cond_2), 1):.1f}%)")
    print(f"  3-bidder: {ob_3}/{len(cond_3)} ({100 * ob_3 / max(len(cond_3), 1):.1f}%)")

    # ---- 7. Total earnings ----
    print("\n7. TOTAL EARNINGS BY CONDITION")
    print("-" * 50)

    earnings_by_sim = defaultdict(float)
    for r in rows:
        if r["human_earned"] is not None:
            earnings_by_sim[(r["condition"], r["sim_id"])] += r["human_earned"]

    earn_2 = [v for (c, _), v in earnings_by_sim.items() if "2bidder" in c]
    earn_3 = [v for (c, _), v in earnings_by_sim.items() if "3bidder" in c]

    print(f"  2-bidder: mean = ${mean(earn_2):.2f} (std = ${std(earn_2):.2f}), n = {len(earn_2)}")
    print(f"  3-bidder: mean = ${mean(earn_3):.2f} (std = ${std(earn_3):.2f}), n = {len(earn_3)}")
    print(f"  Difference: ${mean(earn_3) - mean(earn_2):+.2f}")

    # ---- 8. Win rates ----
    print("\n8. WIN RATES")
    print("-" * 50)

    human_wins_2 = sum(1 for r in cond_2 if r["winner"] == "Human")
    human_wins_3 = sum(1 for r in cond_3 if r["winner"] == "Human")
    print(f"  2-bidder: Human wins {human_wins_2}/{len(cond_2)} ({100 * human_wins_2 / max(len(cond_2), 1):.1f}%)")
    print(f"  3-bidder: Human wins {human_wins_3}/{len(cond_3)} ({100 * human_wins_3 / max(len(cond_3), 1):.1f}%)")

    # ---- 9. Round-by-round ----
    print("\n9. ROUND-BY-ROUND DETAIL")
    print("-" * 50)

    print(f"\n  {'Rnd':>3s} {'Val':>5s} {'Cat':>5s} "
          f"{'2b Bid':>8s} {'2b Ratio':>8s} {'2b Gap':>8s} "
          f"{'3b Bid':>8s} {'3b Ratio':>8s} {'3b Gap':>8s}")
    print(f"  {'─' * 3:s} {'─' * 5:s} {'─' * 5:s} "
          f"{'─' * 8:s} {'─' * 8:s} {'─' * 8:s} "
          f"{'─' * 8:s} {'─' * 8:s} {'─' * 8:s}")

    for rnd in range(1, 7):
        val = HUMAN_VALS[rnd - 1]
        cat = "LOW" if val <= 4 else "HIGH"
        bids_2 = [r["human_bid"] for r in cond_2 if r["round"] == rnd and r["human_bid"] is not None]
        bids_3 = [r["human_bid"] for r in cond_3 if r["round"] == rnd and r["human_bid"] is not None]
        rats_2 = [r["bid_valuation_ratio"] for r in cond_2 if r["round"] == rnd]
        rats_3 = [r["bid_valuation_ratio"] for r in cond_3 if r["round"] == rnd]
        gaps_2r = [r["overbid_gap"] for r in cond_2 if r["round"] == rnd]
        gaps_3r = [r["overbid_gap"] for r in cond_3 if r["round"] == rnd]
        print(f"  {rnd:>3d} ${val:>4.0f} {cat:>5s} "
              f"${mean(bids_2):>6.2f} {mean(rats_2):>8.4f} {mean(gaps_2r):>+8.4f} "
              f"${mean(bids_3):>6.2f} {mean(rats_3):>8.4f} {mean(gaps_3r):>+8.4f}")

    # ---- 10. Individual bids ----
    print("\n10. INDIVIDUAL BIDS")
    print("-" * 50)

    for rnd in range(1, 7):
        bids_2 = [r["human_bid"] for r in cond_2 if r["round"] == rnd and r["human_bid"] is not None]
        bids_3 = [r["human_bid"] for r in cond_3 if r["round"] == rnd and r["human_bid"] is not None]
        val = HUMAN_VALS[rnd - 1]
        cat = "LOW" if val <= 4 else "HIGH"
        nash_2 = val * 0.50
        nash_3 = round(val * 2 / 3, 2)
        print(f"  R{rnd} val=${val:.0f} ({cat}) Nash2=${nash_2:.2f} Nash3=${nash_3:.2f}:")
        print(f"    2b: {[f'{b:.2f}' for b in bids_2]}")
        print(f"    3b: {[f'{b:.2f}' for b in bids_3]}")

    # ---- PREDICTION EVALUATION ----
    print("\n" + "=" * 70)
    print("PREDICTION EVALUATION")
    print("=" * 70)

    # P1: LLMs overbid relative to Nash in BOTH conditions
    p1a = mg2 > 0.02  # 2-bidder gap positive
    p1b = mg3 > 0.02  # 3-bidder gap positive
    p1 = "CONFIRMED" if (p1a and p1b) else ("PARTIALLY" if (p1a or p1b) else "REFUTED")
    print(f"\n  P1. Overbid relative to Nash (both conditions):")
    print(f"      2-bidder gap: {mg2:+.4f} ({'yes' if p1a else 'no'})")
    print(f"      3-bidder gap: {mg3:+.4f} ({'yes' if p1b else 'no'})")
    print(f"      → {p1}")

    # P2: Overbidding gap larger in 3-bidder
    gap_diff = mg3 - mg2
    p2 = "CONFIRMED" if gap_diff > 0.02 else ("REFUTED" if gap_diff < -0.02 else "NULL")
    print(f"\n  P2. Gap larger in 3-bidder than 2-bidder:")
    print(f"      Gap difference: {gap_diff:+.4f}")
    print(f"      → {p2}")

    # P3: Interaction — competition x valuation
    p3 = "CONFIRMED" if interaction > 0.02 else ("REFUTED" if interaction < -0.02 else "NULL")
    print(f"\n  P3. Interaction (competition effect larger for low val):")
    print(f"      Interaction: {interaction:+.4f}")
    print(f"      → {p3}")

    # P4: Earnings lower in 3-bidder
    earn_diff = mean(earn_3) - mean(earn_2)
    p4 = "CONFIRMED" if earn_diff < -0.10 else ("REFUTED" if earn_diff > 0.10 else "NULL")
    print(f"\n  P4. Earnings lower in 3-bidder:")
    print(f"      Difference: ${earn_diff:+.2f}")
    print(f"      → {p4}")

    # Overall verdict
    results = [p1, p2, p3, p4]
    confirmed = sum(1 for p in results if p == "CONFIRMED")
    partial = sum(1 for p in results if p == "PARTIALLY")
    if confirmed >= 3:
        verdict = "YES_INTERESTING"
    elif confirmed >= 1 or partial >= 2:
        verdict = "PARTIALLY"
    else:
        verdict = "NO_NULL"

    print(f"\n  {'=' * 50}")
    print(f"  VERDICT: {verdict} ({confirmed}/4 confirmed, {partial}/4 partial)")
    print(f"  {'=' * 50}")


if __name__ == "__main__":
    main()
