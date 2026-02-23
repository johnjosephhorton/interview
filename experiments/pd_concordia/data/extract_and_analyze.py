#!/usr/bin/env python3
"""Extract structured data from pd_concordia results and compute statistics."""
import json
import csv
import sys
from pathlib import Path

DATA_FILE = Path("transcripts/pd_concordia/2026-02-17_results.json")
OUT_CSV = Path("experiments/pd_concordia/data/data.csv")

with open(DATA_FILE) as f:
    results = json.load(f)

# ── Extract per-simulation summary ──────────────────────────────────────
rows = []
for r in results:
    history = r["history"]
    # Per-round cooperation sequences
    a_choices = [h["a_choice"] for h in history]
    b_choices = [h["b_choice"] for h in history]

    # Detect end-game defection (last 3 rounds)
    a_endgame_defect = sum(1 for c in a_choices[-3:] if c == "defect")
    b_endgame_defect = sum(1 for c in b_choices[-3:] if c == "defect")

    # First defection round (0 if never defected)
    a_first_defect = next((i+1 for i, c in enumerate(a_choices) if c == "defect"), 0)
    b_first_defect = next((i+1 for i, c in enumerate(b_choices) if c == "defect"), 0)

    # Mutual outcomes
    mutual_coop = sum(1 for a, b in zip(a_choices, b_choices) if a == "cooperate" and b == "cooperate")
    mutual_defect = sum(1 for a, b in zip(a_choices, b_choices) if a == "defect" and b == "defect")
    a_exploit = sum(1 for a, b in zip(a_choices, b_choices) if a == "defect" and b == "cooperate")
    b_exploit = sum(1 for a, b in zip(a_choices, b_choices) if b == "defect" and a == "cooperate")

    # Invalids
    a_invalids = sum(1 for h in history if h["a_invalid"])
    b_invalids = sum(1 for h in history if h["b_invalid"])

    rows.append({
        "sim_id": r["sim_id"],
        "a_total_earnings": r["a_total_earnings"],
        "b_total_earnings": r["b_total_earnings"],
        "joint_earnings": r["joint_earnings"],
        "efficiency": r["efficiency"],
        "a_coop_rate": r["a_cooperation_rate"],
        "b_coop_rate": r["b_cooperation_rate"],
        "mutual_coop_rounds": mutual_coop,
        "mutual_defect_rounds": mutual_defect,
        "a_exploit_rounds": a_exploit,
        "b_exploit_rounds": b_exploit,
        "a_first_defect_round": a_first_defect,
        "b_first_defect_round": b_first_defect,
        "a_endgame_defects": a_endgame_defect,
        "b_endgame_defects": b_endgame_defect,
        "a_invalids": a_invalids,
        "b_invalids": b_invalids,
        "a_choices": ",".join(a_choices),
        "b_choices": ",".join(b_choices),
    })

# Write CSV
with open(OUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} rows to {OUT_CSV}")

# ── Descriptive Statistics ──────────────────────────────────────────────
import numpy as np

n = len(rows)
a_earnings = [r["a_total_earnings"] for r in rows]
b_earnings = [r["b_total_earnings"] for r in rows]
joint = [r["joint_earnings"] for r in rows]
eff = [r["efficiency"] for r in rows]
a_coop = [r["a_coop_rate"] for r in rows]
b_coop = [r["b_coop_rate"] for r in rows]
mc = [r["mutual_coop_rounds"] for r in rows]
md = [r["mutual_defect_rounds"] for r in rows]
a_exploit = [r["a_exploit_rounds"] for r in rows]
b_exploit = [r["b_exploit_rounds"] for r in rows]
a_endgame = [r["a_endgame_defects"] for r in rows]
b_endgame = [r["b_endgame_defects"] for r in rows]
a_fd = [r["a_first_defect_round"] for r in rows]
b_fd = [r["b_first_defect_round"] for r in rows]

print(f"\n{'='*60}")
print(f"DESCRIPTIVE STATISTICS (N={n})")
print(f"{'='*60}")
print(f"{'Metric':<35} {'Mean':>8} {'SD':>8} {'Min':>6} {'Max':>6}")
print(f"{'-'*60}")
print(f"{'Player A earnings':<35} {np.mean(a_earnings):>8.1f} {np.std(a_earnings, ddof=1):>8.1f} {min(a_earnings):>6} {max(a_earnings):>6}")
print(f"{'Player B earnings':<35} {np.mean(b_earnings):>8.1f} {np.std(b_earnings, ddof=1):>8.1f} {min(b_earnings):>6} {max(b_earnings):>6}")
print(f"{'Joint earnings':<35} {np.mean(joint):>8.1f} {np.std(joint, ddof=1):>8.1f} {min(joint):>6} {max(joint):>6}")
print(f"{'Efficiency':<35} {np.mean(eff):>8.2f} {np.std(eff, ddof=1):>8.2f} {min(eff):>6.2f} {max(eff):>6.2f}")
print(f"{'A cooperation rate':<35} {np.mean(a_coop):>8.2f} {np.std(a_coop, ddof=1):>8.2f} {min(a_coop):>6.2f} {max(a_coop):>6.2f}")
print(f"{'B cooperation rate':<35} {np.mean(b_coop):>8.2f} {np.std(b_coop, ddof=1):>8.2f} {min(b_coop):>6.2f} {max(b_coop):>6.2f}")
print(f"{'Mutual cooperation rounds':<35} {np.mean(mc):>8.1f} {np.std(mc, ddof=1):>8.1f} {min(mc):>6} {max(mc):>6}")
print(f"{'Mutual defection rounds':<35} {np.mean(md):>8.1f} {np.std(md, ddof=1):>8.1f} {min(md):>6} {max(md):>6}")
print(f"{'A exploits B rounds':<35} {np.mean(a_exploit):>8.1f} {np.std(a_exploit, ddof=1):>8.1f} {min(a_exploit):>6} {max(a_exploit):>6}")
print(f"{'B exploits A rounds':<35} {np.mean(b_exploit):>8.1f} {np.std(b_exploit, ddof=1):>8.1f} {min(b_exploit):>6} {max(b_exploit):>6}")

# Full cooperation games
full_coop = sum(1 for r in rows if r["mutual_coop_rounds"] == 10)
print(f"\nFull mutual cooperation games: {full_coop}/{n} ({100*full_coop/n:.0f}%)")

# Endgame defection analysis
a_endgame_any = sum(1 for r in rows if r["a_endgame_defects"] > 0)
b_endgame_any = sum(1 for r in rows if r["b_endgame_defects"] > 0)
print(f"Games with A endgame defection (last 3): {a_endgame_any}/{n} ({100*a_endgame_any/n:.0f}%)")
print(f"Games with B endgame defection (last 3): {b_endgame_any}/{n} ({100*b_endgame_any/n:.0f}%)")

# First defection distribution
a_defectors = [r for r in rows if r["a_first_defect_round"] > 0]
b_defectors = [r for r in rows if r["b_first_defect_round"] > 0]
print(f"\nA ever defects: {len(a_defectors)}/{n} ({100*len(a_defectors)/n:.0f}%)")
print(f"B ever defects: {len(b_defectors)}/{n} ({100*len(b_defectors)/n:.0f}%)")
if a_defectors:
    a_fd_vals = [r["a_first_defect_round"] for r in a_defectors]
    print(f"  A first defection round: mean={np.mean(a_fd_vals):.1f}, median={np.median(a_fd_vals):.0f}")
if b_defectors:
    b_fd_vals = [r["b_first_defect_round"] for r in b_defectors]
    print(f"  B first defection round: mean={np.mean(b_fd_vals):.1f}, median={np.median(b_fd_vals):.0f}")

# Round-by-round cooperation rates
print(f"\nROUND-BY-ROUND COOPERATION RATES:")
print(f"{'Round':<8} {'A coop%':>10} {'B coop%':>10} {'Mutual coop%':>14} {'Mutual def%':>14}")
for rd in range(10):
    a_c = sum(1 for r in results if r["history"][rd]["a_choice"] == "cooperate")
    b_c = sum(1 for r in results if r["history"][rd]["b_choice"] == "cooperate")
    mc_r = sum(1 for r in results if r["history"][rd]["a_choice"] == "cooperate" and r["history"][rd]["b_choice"] == "cooperate")
    md_r = sum(1 for r in results if r["history"][rd]["a_choice"] == "defect" and r["history"][rd]["b_choice"] == "defect")
    print(f"  {rd+1:<6} {100*a_c/n:>10.0f}% {100*b_c/n:>10.0f}% {100*mc_r/n:>13.0f}% {100*md_r/n:>13.0f}%")

# A vs B earnings comparison (paired t-test)
from scipy import stats
t_stat, p_val = stats.ttest_rel(a_earnings, b_earnings)
print(f"\nPAIRED T-TEST: A earnings vs B earnings")
print(f"  A mean={np.mean(a_earnings):.1f}, B mean={np.mean(b_earnings):.1f}, diff={np.mean(a_earnings)-np.mean(b_earnings):.1f}")
print(f"  t={t_stat:.3f}, p={p_val:.4f}")

# One-sample t-test: cooperation rate vs 0.5
t_a, p_a = stats.ttest_1samp(a_coop, 0.5)
t_b, p_b = stats.ttest_1samp(b_coop, 0.5)
print(f"\nONE-SAMPLE T-TEST: cooperation rate vs 0.5 (random baseline)")
print(f"  A: mean={np.mean(a_coop):.2f}, t={t_a:.3f}, p={p_a:.4f}")
print(f"  B: mean={np.mean(b_coop):.2f}, t={t_b:.3f}, p={p_b:.4f}")

# One-sample t-test: efficiency vs theoretical benchmarks
t_eff1, p_eff1 = stats.ttest_1samp(eff, 1.0)  # vs full cooperation
t_eff2, p_eff2 = stats.ttest_1samp(eff, 1/3)  # vs mutual defection (10/30 = 0.333)
print(f"\nEFFICIENCY TESTS:")
print(f"  vs 100% (full coop): mean={np.mean(eff):.2f}, t={t_eff1:.3f}, p={p_eff1:.4f}")
print(f"  vs 33% (mutual def): mean={np.mean(eff):.2f}, t={t_eff2:.3f}, p={p_eff2:.4f}")

# Classify game outcomes
outcome_types = {"full_coop": 0, "partial_coop": 0, "unraveling": 0, "immediate_defect": 0}
for r in rows:
    if r["mutual_coop_rounds"] == 10:
        outcome_types["full_coop"] += 1
    elif r["a_first_defect_round"] <= 2 or r["b_first_defect_round"] <= 2:
        # Someone defected in first 2 rounds
        if r["a_first_defect_round"] <= 2 and r["b_first_defect_round"] <= 2:
            outcome_types["immediate_defect"] += 1
        else:
            outcome_types["partial_coop"] += 1
    elif r["a_endgame_defects"] >= 2 or r["b_endgame_defects"] >= 2:
        outcome_types["unraveling"] += 1
    else:
        outcome_types["partial_coop"] += 1

print(f"\nGAME OUTCOME TYPOLOGY:")
for k, v in outcome_types.items():
    print(f"  {k:<20}: {v:>3} ({100*v/n:.0f}%)")
