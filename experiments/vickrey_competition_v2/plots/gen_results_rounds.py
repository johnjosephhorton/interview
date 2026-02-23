"""Figure 3: Round-by-round bid ratio trajectories."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data/data.csv")

fig, ax = plt.subplots(figsize=(6, 4))

for cond, color, marker, label, nash in [
    ("auction_2bidder", "#2171b5", "o", "2 Bidders", 0.50),
    ("auction_3bidder", "#e6550d", "s", "3 Bidders", 0.6667),
]:
    sub = df[df["condition"] == cond]
    means = sub.groupby("round")["bid_valuation_ratio"].mean()
    sems = sub.groupby("round")["bid_valuation_ratio"].sem()
    ax.errorbar(means.index, means.values, yerr=sems.values,
                marker=marker, color=color, label=f"{label} (observed)", capsize=3, linewidth=1.5)
    ax.axhline(y=nash, color=color, linestyle="--", alpha=0.5, linewidth=1,
               label=f"{label} Nash = {nash:.2f}")

# Valuation annotations
vals = [3, 8, 4, 9, 3, 7]
for rnd, val in enumerate(vals, 1):
    ax.annotate(f"${val}", (rnd, 0.38), fontsize=7, ha="center", color="gray")

ax.set_xlabel("Round")
ax.set_ylabel("Bid / Valuation Ratio")
ax.set_title("Bidding Trajectories Across Rounds")
ax.set_xticks(range(1, 7))
ax.set_ylim(0.35, 1.0)
ax.legend(fontsize=7, loc="upper left")

plt.tight_layout()
plt.savefig("plots/results_rounds.pdf", bbox_inches="tight")
print("Saved plots/results_rounds.pdf")
