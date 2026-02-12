"""Figure 2: AI Opening Offers and Convergence — two-panel bar chart."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pathlib

# ── Data ──────────────────────────────────────────────────────────────────────
DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "info_precision_bargaining_v2_data.csv"
OUT  = pathlib.Path(__file__).resolve().parent / "results_info_precision_v2_dynamics.pdf"

df = pd.read_csv(DATA)

cond_order = ["none", "range", "exact"]
cond_labels = {"none": "No Info", "range": "Range Info", "exact": "Exact Info"}
cond_colors = {"none": "#3274A1", "range": "#E1812C", "exact": "#3A923A"}
zopa_vals = [2, 5]
zopa_alpha = {2: 1.0, 5: 0.55}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.0))

bar_width = 0.32
x_positions = np.arange(len(cond_order))

# ── Helper ────────────────────────────────────────────────────────────────────
def grouped_bars(ax, col, ylabel, title):
    for j, zopa in enumerate(zopa_vals):
        means = []
        sems = []
        colors = []
        for cond in cond_order:
            subset = df[(df["condition"] == cond) & (df["zopa"] == zopa)]
            vals = subset[col].values
            means.append(np.mean(vals))
            sems.append(np.std(vals, ddof=1) / np.sqrt(len(vals)) if len(vals) > 1 else 0)
            colors.append(cond_colors[cond])

        offset = (j - 0.5) * bar_width
        bars = ax.bar(
            x_positions + offset,
            means,
            width=bar_width * 0.9,
            yerr=sems,
            capsize=3,
            color=colors,
            alpha=zopa_alpha[zopa],
            edgecolor="black",
            linewidth=0.6,
            error_kw=dict(lw=1, capthick=0.8, color="black"),
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels([cond_labels[c] for c in cond_order], fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# ── Panel A: AI Opening Offer ────────────────────────────────────────────────
grouped_bars(ax1, "ai_opening_offer", "AI Opening Offer ($)", "(A) AI Opening Offer")
ax1.axhline(40, color="gray", ls="--", lw=0.9, label="Seller cost (\\$40)")
ax1.legend(fontsize=8, frameon=False, loc="upper right")

# ── Panel B: Rounds to Deal ──────────────────────────────────────────────────
grouped_bars(ax2, "rounds_to_deal", "Rounds to Deal", "(B) Rounds to Agreement")

# ── Shared legend for ZOPA ───────────────────────────────────────────────────
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="gray", alpha=1.0, edgecolor="black", label="ZOPA = \\$2"),
    Patch(facecolor="gray", alpha=0.55, edgecolor="black", label="ZOPA = \\$5"),
]
fig.legend(
    handles=legend_elements,
    loc="lower center",
    ncol=2,
    fontsize=9,
    frameon=False,
    bbox_to_anchor=(0.5, -0.02),
)

fig.tight_layout(rect=[0, 0.05, 1, 1])
fig.savefig(OUT, bbox_inches="tight")
print(f"Saved: {OUT}")
