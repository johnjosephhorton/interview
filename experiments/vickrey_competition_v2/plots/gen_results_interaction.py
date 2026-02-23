"""Figure 2: Interaction — overbidding gap by condition x valuation level."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data/data.csv")

# Compute means and SEs
cells = {}
for cond in ["auction_2bidder", "auction_3bidder"]:
    for cat in ["low", "high"]:
        sub = df[(df["condition"] == cond) & (df["valuation_category"] == cat)]["overbid_gap"]
        cells[(cond, cat)] = (sub.mean(), sub.std() / np.sqrt(len(sub)))

fig, ax = plt.subplots(figsize=(5, 4))

x = np.array([0, 1])
width = 0.3

# 2-bidder bars
means_2b = [cells[("auction_2bidder", "low")][0], cells[("auction_2bidder", "high")][0]]
errs_2b = [cells[("auction_2bidder", "low")][1], cells[("auction_2bidder", "high")][1]]
bars1 = ax.bar(x - width/2, means_2b, width, yerr=errs_2b, label="2 Bidders",
               color="#c6dbef", edgecolor="#2171b5", capsize=4)

# 3-bidder bars
means_3b = [cells[("auction_3bidder", "low")][0], cells[("auction_3bidder", "high")][0]]
errs_3b = [cells[("auction_3bidder", "low")][1], cells[("auction_3bidder", "high")][1]]
bars2 = ax.bar(x + width/2, means_3b, width, yerr=errs_3b, label="3 Bidders",
               color="#fdd0a2", edgecolor="#e6550d", capsize=4)

ax.axhline(y=0, color="red", linestyle="--", linewidth=1, alpha=0.5)
ax.set_xticks(x)
ax.set_xticklabels(["Low Valuation\n(\\$3--\\$4)", "High Valuation\n(\\$7--\\$9)"])
ax.set_ylabel("Mean Overbidding Gap")
ax.set_title("Competition $\\times$ Valuation Interaction")
ax.legend()

plt.tight_layout()
plt.savefig("plots/results_interaction.pdf", bbox_inches="tight")
print("Saved plots/results_interaction.pdf")
