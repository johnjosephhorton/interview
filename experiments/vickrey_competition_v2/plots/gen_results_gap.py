"""Figure 1: Overbidding gap by condition (box plot with individual points)."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data/data.csv")

fig, ax = plt.subplots(figsize=(5, 4))

data_2b = df[df["condition"] == "auction_2bidder"]["overbid_gap"]
data_3b = df[df["condition"] == "auction_3bidder"]["overbid_gap"]

bp = ax.boxplot([data_2b, data_3b], labels=["2 Bidders", "3 Bidders"],
                widths=0.5, patch_artist=True,
                boxprops=dict(facecolor="#c6dbef", edgecolor="#2171b5"),
                medianprops=dict(color="#08519c", linewidth=2),
                whiskerprops=dict(color="#2171b5"),
                capprops=dict(color="#2171b5"))

# Scatter individual points
for i, d in enumerate([data_2b, data_3b], 1):
    jitter = np.random.normal(0, 0.04, size=len(d))
    ax.scatter(np.full(len(d), i) + jitter, d, alpha=0.4, s=20, color="#2171b5", zorder=3)

# Nash reference line
ax.axhline(y=0, color="red", linestyle="--", linewidth=1, label="Nash equilibrium (gap = 0)")

ax.set_ylabel("Overbidding Gap (bid ratio $-$ Nash ratio)")
ax.set_title("Overbidding Relative to Nash Equilibrium")
ax.legend(loc="upper right", fontsize=8)
ax.set_ylim(-0.15, 0.45)

plt.tight_layout()
plt.savefig("plots/results_overbid_gap.pdf", bbox_inches="tight")
print("Saved plots/results_overbid_gap.pdf")
