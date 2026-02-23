#!/usr/bin/env python3
"""Extract and compare baseline PD vs PD+punishment results."""
import json
import csv
import numpy as np
from scipy import stats
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = ROOT / "transcripts/pd_concordia/2026-02-18_post_fix_results.json"
PUNISH = ROOT / "transcripts/pd_concordia_punish/2026-02-21_results.json"
OUT_CSV = Path(__file__).resolve().parent / "data.csv"


def extract_baseline(path):
    """Extract from baseline PD (no punishment)."""
    with open(path) as f:
        results = json.load(f)
    rows = []
    for r in results:
        h = r["history"]
        a_choices = [x["a_choice"] for x in h]
        b_choices = [x["b_choice"] for x in h]
        mc = sum(1 for a, b in zip(a_choices, b_choices) if a == "cooperate" and b == "cooperate")
        md = sum(1 for a, b in zip(a_choices, b_choices) if a == "defect" and b == "defect")
        rows.append({
            "condition": "baseline",
            "sim_id": r["sim_id"],
            "a_total_earnings": r["a_total_earnings"],
            "b_total_earnings": r["b_total_earnings"],
            "joint_earnings": r["joint_earnings"],
            "efficiency": r["efficiency"],
            "a_coop_rate": r["a_cooperation_rate"],
            "b_coop_rate": r["b_cooperation_rate"],
            "avg_coop_rate": (r["a_cooperation_rate"] + r["b_cooperation_rate"]) / 2,
            "mutual_coop_rounds": mc,
            "mutual_defect_rounds": md,
            "full_coop": mc == 10,
            "a_punishment_rate": 0.0,
            "b_punishment_rate": 0.0,
            "total_punishments": 0,
        })
    return rows, results


def extract_punish(path):
    """Extract from PD+punishment condition."""
    with open(path) as f:
        results = json.load(f)
    rows = []
    for r in results:
        h = r["history"]
        a_choices = [x["a_choice"] for x in h]
        b_choices = [x["b_choice"] for x in h]
        mc = sum(1 for a, b in zip(a_choices, b_choices) if a == "cooperate" and b == "cooperate")
        md = sum(1 for a, b in zip(a_choices, b_choices) if a == "defect" and b == "defect")
        rows.append({
            "condition": "punishment",
            "sim_id": r["sim_id"],
            "a_total_earnings": r["a_total_earnings"],
            "b_total_earnings": r["b_total_earnings"],
            "joint_earnings": r["a_total_earnings"] + r["b_total_earnings"],
            "efficiency": (r["a_total_earnings"] + r["b_total_earnings"]) / 60,
            "a_coop_rate": r["a_cooperation_rate"],
            "b_coop_rate": r["b_cooperation_rate"],
            "avg_coop_rate": (r["a_cooperation_rate"] + r["b_cooperation_rate"]) / 2,
            "mutual_coop_rounds": mc,
            "mutual_defect_rounds": md,
            "full_coop": mc == 10,
            "a_punishment_rate": r["a_punishment_rate"],
            "b_punishment_rate": r["b_punishment_rate"],
            "total_punishments": r["total_punishments"],
        })
    return rows, results


base_rows, base_raw = extract_baseline(BASELINE)
pun_rows, pun_raw = extract_punish(PUNISH)
all_rows = base_rows + pun_rows

# Write CSV
with open(OUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    writer.writeheader()
    writer.writerows(all_rows)
print(f"Wrote {len(all_rows)} rows to {OUT_CSV}")

# ── Descriptive stats ──────────────────────────────────────────────────
def describe(rows, label):
    n = len(rows)
    vals = {
        "a_earn": [r["a_total_earnings"] for r in rows],
        "b_earn": [r["b_total_earnings"] for r in rows],
        "joint": [r["joint_earnings"] for r in rows],
        "eff": [r["efficiency"] for r in rows],
        "a_coop": [r["a_coop_rate"] for r in rows],
        "b_coop": [r["b_coop_rate"] for r in rows],
        "avg_coop": [r["avg_coop_rate"] for r in rows],
        "mc": [r["mutual_coop_rounds"] for r in rows],
        "a_punish": [r["a_punishment_rate"] for r in rows],
        "b_punish": [r["b_punishment_rate"] for r in rows],
        "total_pun": [r["total_punishments"] for r in rows],
    }
    fc = sum(1 for r in rows if r["full_coop"])

    print(f"\n{'='*60}")
    print(f"{label} (N={n})")
    print(f"{'='*60}")
    print(f"{'Metric':<30} {'Mean':>8} {'SD':>8} {'Min':>6} {'Max':>6}")
    print(f"{'-'*60}")
    for name, v in [
        ("A earnings", vals["a_earn"]),
        ("B earnings", vals["b_earn"]),
        ("Joint earnings", vals["joint"]),
        ("Efficiency", vals["eff"]),
        ("A coop rate", vals["a_coop"]),
        ("B coop rate", vals["b_coop"]),
        ("Avg coop rate", vals["avg_coop"]),
        ("Mutual coop rounds", vals["mc"]),
    ]:
        print(f"{name:<30} {np.mean(v):>8.2f} {np.std(v,ddof=1):>8.2f} {min(v):>6.2f} {max(v):>6.2f}")
    print(f"{'Full coop games':<30} {fc:>8} / {n}")
    print(f"{'A punishment rate':<30} {np.mean(vals['a_punish']):>8.3f} {np.std(vals['a_punish'],ddof=1):>8.3f}")
    print(f"{'B punishment rate':<30} {np.mean(vals['b_punish']):>8.3f} {np.std(vals['b_punish'],ddof=1):>8.3f}")
    print(f"{'Total punishments/game':<30} {np.mean(vals['total_pun']):>8.2f} {np.std(vals['total_pun'],ddof=1):>8.2f}")
    vals["fc"] = fc
    vals["n"] = n
    return vals

base_s = describe(base_rows, "BASELINE (no punishment)")
pun_s = describe(pun_rows, "PUNISHMENT (costly punishment available)")

# ── Between-condition comparisons ──────────────────────────────────────
print(f"\n{'='*60}")
print("BETWEEN-CONDITION COMPARISONS")
print(f"{'='*60}")

# Cooperation rate
t_coop, p_coop = stats.ttest_ind(base_s["avg_coop"], pun_s["avg_coop"])
print(f"\nAvg cooperation rate:")
print(f"  Baseline:   {np.mean(base_s['avg_coop']):.3f} (SD={np.std(base_s['avg_coop'],ddof=1):.3f})")
print(f"  Punishment: {np.mean(pun_s['avg_coop']):.3f} (SD={np.std(pun_s['avg_coop'],ddof=1):.3f})")
print(f"  t={t_coop:.3f}, p={p_coop:.4f}")

# Mann-Whitney U for robustness (non-normal distributions)
u_coop, p_u_coop = stats.mannwhitneyu(base_s["avg_coop"], pun_s["avg_coop"], alternative="two-sided")
print(f"  Mann-Whitney U={u_coop:.0f}, p={p_u_coop:.4f}")

# Full cooperation rate (Fisher's exact)
base_fc = base_s["fc"]
pun_fc = pun_s["fc"]
table = [[base_fc, base_s["n"] - base_fc], [pun_fc, pun_s["n"] - pun_fc]]
odds, p_fisher = stats.fisher_exact(table)
print(f"\nFull coop games:")
print(f"  Baseline:   {base_fc}/{base_s['n']} ({base_fc/base_s['n']*100:.0f}%)")
print(f"  Punishment: {pun_fc}/{pun_s['n']} ({pun_fc/pun_s['n']*100:.0f}%)")
print(f"  Fisher exact: OR={odds:.2f}, p={p_fisher:.4f}")

# Efficiency
t_eff, p_eff = stats.ttest_ind(base_s["eff"], pun_s["eff"])
print(f"\nEfficiency:")
print(f"  Baseline:   {np.mean(base_s['eff']):.3f}")
print(f"  Punishment: {np.mean(pun_s['eff']):.3f}")
print(f"  t={t_eff:.3f}, p={p_eff:.4f}")

# Joint earnings
t_je, p_je = stats.ttest_ind(base_s["joint"], pun_s["joint"])
print(f"\nJoint earnings:")
print(f"  Baseline:   ${np.mean(base_s['joint']):.1f}")
print(f"  Punishment: ${np.mean(pun_s['joint']):.1f}")
print(f"  t={t_je:.3f}, p={p_je:.4f}")

# Earnings asymmetry within each condition
base_asym = [a - b for a, b in zip(base_s["a_earn"], base_s["b_earn"])]
pun_asym = [a - b for a, b in zip(pun_s["a_earn"], pun_s["b_earn"])]
t_basym, p_basym = stats.ttest_rel(base_s["a_earn"], base_s["b_earn"])
t_pasym, p_pasym = stats.ttest_rel(pun_s["a_earn"], pun_s["b_earn"])
print(f"\nA-B earnings asymmetry:")
print(f"  Baseline:   {np.mean(base_asym):+.1f} (t={t_basym:.3f}, p={p_basym:.4f})")
print(f"  Punishment: {np.mean(pun_asym):+.1f} (t={t_pasym:.3f}, p={p_pasym:.4f})")

# Punishment usage
print(f"\nPunishment usage (punishment condition only):")
print(f"  Games with any punishment: {sum(1 for r in pun_rows if r['total_punishments'] > 0)}/30")
print(f"  Total punishments across all games: {sum(r['total_punishments'] for r in pun_rows)}")
print(f"  Mean punishments/game: {np.mean(pun_s['total_pun']):.2f}")

# Round-by-round cooperation comparison
print(f"\nROUND-BY-ROUND COOPERATION RATES:")
print(f"{'Round':<8} {'Base A':>8} {'Pun A':>8} {'Base B':>8} {'Pun B':>8}")
for rd in range(10):
    ba = sum(1 for r in base_raw if r["history"][rd]["a_choice"] == "cooperate") / 30
    pa = sum(1 for r in pun_raw if r["history"][rd]["a_choice"] == "cooperate") / 30
    bb = sum(1 for r in base_raw if r["history"][rd]["b_choice"] == "cooperate") / 30
    pb = sum(1 for r in pun_raw if r["history"][rd]["b_choice"] == "cooperate") / 30
    print(f"  {rd+1:<6} {ba:>8.0%} {pa:>8.0%} {bb:>8.0%} {pb:>8.0%}")

# Prediction evaluation
print(f"\n{'='*60}")
print("PREDICTION EVALUATION")
print(f"{'='*60}")
print(f"P1: Full coop > 50%? Punishment={pun_fc/pun_s['n']*100:.0f}% -> {'CONFIRMED' if pun_fc/pun_s['n'] > 0.5 else 'REFUTED'}")
print(f"P2: Mean coop > 80%? Punishment={np.mean(pun_s['avg_coop'])*100:.0f}% -> {'CONFIRMED' if np.mean(pun_s['avg_coop']) > 0.8 else 'REFUTED'}")
print(f"P3: Punishment declines over rounds? See round-by-round data (only 1 game used punishment)")
