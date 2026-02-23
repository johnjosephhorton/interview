#!/usr/bin/env python3
"""Extract and compare pre-fix vs post-fix pd_concordia results."""
import json
import csv
import numpy as np
from scipy import stats
from pathlib import Path

PRE = Path("transcripts/pd_concordia/2026-02-17_results.json")
POST = Path("transcripts/pd_concordia/2026-02-18_post_fix_results.json")
OUT_CSV = Path("experiments/pd_concordia/data/data_v2.csv")

def load_and_extract(path, condition_label):
    with open(path) as f:
        results = json.load(f)
    rows = []
    for r in results:
        h = r["history"]
        a_choices = [x["a_choice"] for x in h]
        b_choices = [x["b_choice"] for x in h]
        a_endgame = sum(1 for c in a_choices[-3:] if c == "defect")
        b_endgame = sum(1 for c in b_choices[-3:] if c == "defect")
        a_first_def = next((i+1 for i, c in enumerate(a_choices) if c == "defect"), 0)
        b_first_def = next((i+1 for i, c in enumerate(b_choices) if c == "defect"), 0)
        mc = sum(1 for a, b in zip(a_choices, b_choices) if a == "cooperate" and b == "cooperate")
        md = sum(1 for a, b in zip(a_choices, b_choices) if a == "defect" and b == "defect")
        a_exploit = sum(1 for a, b in zip(a_choices, b_choices) if a == "defect" and b == "cooperate")
        b_exploit = sum(1 for a, b in zip(a_choices, b_choices) if b == "defect" and a == "cooperate")
        rows.append({
            "condition": condition_label,
            "sim_id": r["sim_id"],
            "a_total_earnings": r["a_total_earnings"],
            "b_total_earnings": r["b_total_earnings"],
            "joint_earnings": r["joint_earnings"],
            "efficiency": r["efficiency"],
            "a_coop_rate": r["a_cooperation_rate"],
            "b_coop_rate": r["b_cooperation_rate"],
            "mutual_coop_rounds": mc,
            "mutual_defect_rounds": md,
            "a_exploit_rounds": a_exploit,
            "b_exploit_rounds": b_exploit,
            "a_first_defect_round": a_first_def,
            "b_first_defect_round": b_first_def,
            "a_endgame_defects": a_endgame,
            "b_endgame_defects": b_endgame,
            "full_coop": mc == 10,
        })
    return rows, results

pre_rows, pre_raw = load_and_extract(PRE, "pre_fix")
post_rows, post_raw = load_and_extract(POST, "post_fix")
all_rows = pre_rows + post_rows

# Write combined CSV
with open(OUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    writer.writeheader()
    writer.writerows(all_rows)
print(f"Wrote {len(all_rows)} rows to {OUT_CSV}")

# ── Descriptive stats by condition ──────────────────────────────────────
def describe(rows, label):
    n = len(rows)
    a_e = [r["a_total_earnings"] for r in rows]
    b_e = [r["b_total_earnings"] for r in rows]
    je = [r["joint_earnings"] for r in rows]
    eff = [r["efficiency"] for r in rows]
    ac = [r["a_coop_rate"] for r in rows]
    bc = [r["b_coop_rate"] for r in rows]
    mc = [r["mutual_coop_rounds"] for r in rows]
    fc = sum(1 for r in rows if r["full_coop"])
    a_expl = [r["a_exploit_rounds"] for r in rows]
    b_expl = [r["b_exploit_rounds"] for r in rows]

    print(f"\n{'='*60}")
    print(f"{label} (N={n})")
    print(f"{'='*60}")
    print(f"{'Metric':<30} {'Mean':>8} {'SD':>8} {'Min':>6} {'Max':>6}")
    print(f"{'-'*60}")
    print(f"{'A earnings':<30} {np.mean(a_e):>8.1f} {np.std(a_e,ddof=1):>8.1f} {min(a_e):>6} {max(a_e):>6}")
    print(f"{'B earnings':<30} {np.mean(b_e):>8.1f} {np.std(b_e,ddof=1):>8.1f} {min(b_e):>6} {max(b_e):>6}")
    print(f"{'Joint earnings':<30} {np.mean(je):>8.1f} {np.std(je,ddof=1):>8.1f} {min(je):>6} {max(je):>6}")
    print(f"{'Efficiency':<30} {np.mean(eff):>8.2f} {np.std(eff,ddof=1):>8.2f} {min(eff):>6.2f} {max(eff):>6.2f}")
    print(f"{'A coop rate':<30} {np.mean(ac):>8.2f} {np.std(ac,ddof=1):>8.2f} {min(ac):>6.2f} {max(ac):>6.2f}")
    print(f"{'B coop rate':<30} {np.mean(bc):>8.2f} {np.std(bc,ddof=1):>8.2f} {min(bc):>6.2f} {max(bc):>6.2f}")
    print(f"{'Mutual coop rounds':<30} {np.mean(mc):>8.1f} {np.std(mc,ddof=1):>8.1f} {min(mc):>6} {max(mc):>6}")
    print(f"{'Full coop games':<30} {fc:>8} / {n}")
    print(f"{'A exploits B':<30} {np.mean(a_expl):>8.1f} {np.std(a_expl,ddof=1):>8.1f}")
    print(f"{'B exploits A':<30} {np.mean(b_expl):>8.1f} {np.std(b_expl,ddof=1):>8.1f}")

    # Asymmetry test
    t, p = stats.ttest_rel(a_e, b_e)
    diff = np.mean(a_e) - np.mean(b_e)
    print(f"\n  A-B earnings diff: {diff:+.1f} (t={t:.3f}, p={p:.4f})")
    return {"a_e": a_e, "b_e": b_e, "eff": eff, "ac": ac, "bc": bc, "mc": mc, "fc": fc, "n": n}

pre_s = describe(pre_rows, "PRE-FIX (sequential act, shared obs)")
post_s = describe(post_rows, "POST-FIX (randomized act, role-relative obs)")

# ── Between-condition comparisons ───────────────────────────────────────
print(f"\n{'='*60}")
print("BETWEEN-CONDITION COMPARISONS (pre vs post)")
print(f"{'='*60}")

# Earnings asymmetry magnitude
pre_asym = [a - b for a, b in zip(pre_s["a_e"], pre_s["b_e"])]
post_asym = [a - b for a, b in zip(post_s["a_e"], post_s["b_e"])]
t_asym, p_asym = stats.ttest_ind(pre_asym, post_asym)
print(f"\nA-B earnings gap:")
print(f"  Pre:  {np.mean(pre_asym):+.1f} (SD={np.std(pre_asym,ddof=1):.1f})")
print(f"  Post: {np.mean(post_asym):+.1f} (SD={np.std(post_asym,ddof=1):.1f})")
print(f"  Difference: t={t_asym:.3f}, p={p_asym:.4f}")

# Cooperation rates
t_ac, p_ac = stats.ttest_ind(pre_s["ac"], post_s["ac"])
t_bc, p_bc = stats.ttest_ind(pre_s["bc"], post_s["bc"])
print(f"\nA coop rate: pre={np.mean(pre_s['ac']):.2f}, post={np.mean(post_s['ac']):.2f}, t={t_ac:.3f}, p={p_ac:.4f}")
print(f"B coop rate: pre={np.mean(pre_s['bc']):.2f}, post={np.mean(post_s['bc']):.2f}, t={t_bc:.3f}, p={p_bc:.4f}")

# Efficiency
t_eff, p_eff = stats.ttest_ind(pre_s["eff"], post_s["eff"])
print(f"\nEfficiency: pre={np.mean(pre_s['eff']):.2f}, post={np.mean(post_s['eff']):.2f}, t={t_eff:.3f}, p={p_eff:.4f}")

# Full cooperation rate (Fisher's exact)
pre_fc = pre_s["fc"]
post_fc = post_s["fc"]
table = [[pre_fc, pre_s["n"] - pre_fc], [post_fc, post_s["n"] - post_fc]]
odds, p_fisher = stats.fisher_exact(table)
print(f"\nFull coop games: pre={pre_fc}/{pre_s['n']}, post={post_fc}/{post_s['n']}, Fisher p={p_fisher:.4f}")

# Round-by-round comparison
print(f"\nROUND-BY-ROUND COOPERATION RATES:")
print(f"{'Round':<8} {'Pre A':>8} {'Post A':>8} {'Pre B':>8} {'Post B':>8}")
for rd in range(10):
    pre_a = sum(1 for r in pre_raw if r["history"][rd]["a_choice"] == "cooperate") / 30
    post_a = sum(1 for r in post_raw if r["history"][rd]["a_choice"] == "cooperate") / 30
    pre_b = sum(1 for r in pre_raw if r["history"][rd]["b_choice"] == "cooperate") / 30
    post_b = sum(1 for r in post_raw if r["history"][rd]["b_choice"] == "cooperate") / 30
    print(f"  {rd+1:<6} {pre_a:>8.0%} {post_a:>8.0%} {pre_b:>8.0%} {post_b:>8.0%}")
