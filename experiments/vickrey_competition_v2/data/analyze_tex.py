"""Statistical analysis for vickrey_competition_v2 — reproduces all stats for the LaTeX memo."""
import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv("data/data.csv")

# --- Bid/Valuation Ratio by condition ---
g = df.groupby("condition")["bid_valuation_ratio"]
print("=== Bid/Valuation Ratio ===")
for cond, grp in g:
    print(f"  {cond}: mean={grp.mean():.4f}, std={grp.std():.4f}, N={len(grp)}")

b2 = df[df["condition"] == "auction_2bidder"]["bid_valuation_ratio"]
b3 = df[df["condition"] == "auction_3bidder"]["bid_valuation_ratio"]
t_ratio, p_ratio = stats.ttest_ind(b2, b3, equal_var=False)
print(f"  Welch's t = {t_ratio:.2f}, p = {p_ratio:.4f}")

# --- Overbidding Gap ---
print("\n=== Overbidding Gap ===")
g2 = df.groupby("condition")["overbid_gap"]
for cond, grp in g2:
    print(f"  {cond}: mean={grp.mean():.4f}, std={grp.std():.4f}, N={len(grp)}")

gap2 = df[df["condition"] == "auction_2bidder"]["overbid_gap"]
gap3 = df[df["condition"] == "auction_3bidder"]["overbid_gap"]
t_gap, p_gap = stats.ttest_ind(gap2, gap3, equal_var=False)
print(f"  Welch's t (gap) = {t_gap:.2f}, p = {p_gap:.4f}")

# One-sample t-tests: gap > 0?
t_2b, p_2b = stats.ttest_1samp(gap2, 0)
t_3b, p_3b = stats.ttest_1samp(gap3, 0)
print(f"  2-bidder gap vs 0: t={t_2b:.2f}, p={p_2b:.4f}")
print(f"  3-bidder gap vs 0: t={t_3b:.2f}, p={p_3b:.4f}")

# --- Interaction: Competition x Valuation Level ---
print("\n=== Interaction: Competition x Valuation ===")
for cond in ["auction_2bidder", "auction_3bidder"]:
    for cat in ["low", "high"]:
        sub = df[(df["condition"] == cond) & (df["valuation_category"] == cat)]
        print(f"  {cond} / {cat}: gap mean={sub['overbid_gap'].mean():.4f}, N={len(sub)}")

# 2x2 interaction via OLS
from scipy.stats import f_oneway
low2 = df[(df["condition"] == "auction_2bidder") & (df["valuation_category"] == "low")]["overbid_gap"]
high2 = df[(df["condition"] == "auction_2bidder") & (df["valuation_category"] == "high")]["overbid_gap"]
low3 = df[(df["condition"] == "auction_3bidder") & (df["valuation_category"] == "low")]["overbid_gap"]
high3 = df[(df["condition"] == "auction_3bidder") & (df["valuation_category"] == "high")]["overbid_gap"]
interaction = (low3.mean() - high3.mean()) - (low2.mean() - high2.mean())
print(f"  Interaction (val_effect_3b - val_effect_2b) = {interaction:.4f}")

# --- Earnings ---
print("\n=== Total Earnings by Simulation ===")
earn = df.groupby(["condition", "sim_id"])["human_earned"].sum().reset_index()
for cond in ["auction_2bidder", "auction_3bidder"]:
    sub = earn[earn["condition"] == cond]["human_earned"]
    print(f"  {cond}: mean=${sub.mean():.2f}, std=${sub.std():.2f}, N={len(sub)}")

# --- Win Rates ---
print("\n=== Win Rates ===")
for cond in ["auction_2bidder", "auction_3bidder"]:
    sub = df[df["condition"] == cond]
    wins = (sub["winner"] == "Human").sum()
    total = len(sub)
    print(f"  {cond}: {wins}/{total} = {wins/total:.1%}")

# --- AI Bid Correctness ---
print("\n=== AI Bid Correctness ===")
for cond in ["auction_2bidder", "auction_3bidder"]:
    sub = df[df["condition"] == cond]
    correct = sub["ai_bid_correct"].sum()
    total = len(sub)
    print(f"  {cond}: {correct}/{total} = {correct/total:.0%}")

# --- Round-by-round ---
print("\n=== Round-by-Round Means ===")
for rnd in range(1, 7):
    r = df[df["round"] == rnd]
    r2 = r[r["condition"] == "auction_2bidder"]
    r3 = r[r["condition"] == "auction_3bidder"]
    val = r2["human_valuation"].iloc[0] if len(r2) > 0 else "?"
    cat = r2["valuation_category"].iloc[0] if len(r2) > 0 else "?"
    print(f"  Rnd {rnd} (${val}, {cat}): 2b ratio={r2['bid_valuation_ratio'].mean():.4f}, "
          f"2b gap={r2['overbid_gap'].mean():.4f}, "
          f"3b ratio={r3['bid_valuation_ratio'].mean():.4f}, "
          f"3b gap={r3['overbid_gap'].mean():.4f}")

print("\nDone.")
