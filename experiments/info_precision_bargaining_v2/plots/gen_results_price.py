"""Figure 1: Deal Price by Condition x ZOPA — box + strip plot."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
import pathlib

# ── Data ──────────────────────────────────────────────────────────────────────
DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "info_precision_bargaining_v2_data.csv"
OUT  = pathlib.Path(__file__).resolve().parent / "results_info_precision_v2_price.pdf"

df = pd.read_csv(DATA)

# Condition ordering and labels
cond_order = ["none", "range", "exact"]
cond_labels = {"none": "No Info", "range": "Range Info", "exact": "Exact Info"}
cond_colors = {"none": "#3274A1", "range": "#E1812C", "exact": "#3A923A"}
# Dark / light shading for ZOPA
zopa_alpha = {2: 1.0, 5: 0.55}

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.5, 4.2))
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
})

bar_width = 0.35
positions = []  # (x_center, condition, zopa)

for i, cond in enumerate(cond_order):
    x_base = i * 1.2
    for j, zopa in enumerate([2, 5]):
        x = x_base + (j - 0.5) * bar_width
        subset = df[(df["condition"] == cond) & (df["zopa"] == zopa)]
        vals = subset["deal_price"].values

        color = cond_colors[cond]
        alpha = zopa_alpha[zopa]

        bp = ax.boxplot(
            vals,
            positions=[x],
            widths=bar_width * 0.8,
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color="black", linewidth=1.2),
            whiskerprops=dict(color="gray"),
            capprops=dict(color="gray"),
        )
        for patch in bp["boxes"]:
            patch.set_facecolor(color)
            patch.set_alpha(alpha)
            patch.set_edgecolor("black")
            patch.set_linewidth(0.7)

        # Jittered strip
        jitter = np.random.default_rng(42).uniform(-0.06, 0.06, size=len(vals))
        ax.scatter(
            x + jitter, vals,
            color=color, alpha=min(alpha + 0.1, 1.0),
            edgecolors="white", linewidths=0.4,
            s=28, zorder=5,
        )
        positions.append((x, cond, zopa))

# Reference lines
ax.axhline(40, color="gray", ls="--", lw=0.9, label="Seller cost ($40)")
# Fair prices
# ZOPA=$2 fair = $41, ZOPA=$5 fair = $42.50
ax.axhline(41, color="#888888", ls=":", lw=0.8, label="Fair price (ZOPA=\\$2): \\$41")
ax.axhline(42.5, color="#555555", ls="-.", lw=0.8, label="Fair price (ZOPA=\\$5): \\$42.50")

# X-axis
tick_positions = [i * 1.2 for i in range(3)]
ax.set_xticks(tick_positions)
ax.set_xticklabels([cond_labels[c] for c in cond_order], fontsize=10)

ax.set_ylabel("Deal Price ($)", fontsize=10)
ax.set_title("(A) Deal Price by Information Condition and ZOPA", fontsize=11, fontweight="bold", pad=10)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Y-axis range
ax.set_ylim(39.2, 45.3)
ax.yaxis.set_major_locator(mticker.MultipleLocator(1))

# Legend: custom entries for ZOPA shading
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="gray", alpha=1.0, edgecolor="black", label="ZOPA = \\$2"),
    Patch(facecolor="gray", alpha=0.55, edgecolor="black", label="ZOPA = \\$5"),
    plt.Line2D([0], [0], color="gray", ls="--", lw=0.9, label="Seller cost (\\$40)"),
    plt.Line2D([0], [0], color="#888888", ls=":", lw=0.8, label="Fair price, ZOPA=\\$2 (\\$41)"),
    plt.Line2D([0], [0], color="#555555", ls="-.", lw=0.8, label="Fair price, ZOPA=\\$5 (\\$42.50)"),
]
ax.legend(handles=legend_elements, fontsize=8, loc="upper right", frameon=False)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print(f"Saved: {OUT}")
