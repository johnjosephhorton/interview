#!/usr/bin/env python3
"""Generate 3 publication-quality figures for info_source_bargaining experiment."""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import Patch

# -- Global style --------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "Georgia"],
    "font.size": 11,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})

# -- Colors --------------------------------------------------------------------
COLORS = {
    "bargain_source_none":     "#4C72B0",
    "bargain_source_verified": "#55A868",
    "bargain_source_claimed":  "#C44E52",
}
COLOR_LIST = ["#4C72B0", "#55A868", "#C44E52"]

LABELS = {
    "bargain_source_none":     "No Info\n(Baseline)",
    "bargain_source_verified": "Game-Disclosed\n(Verified)",
    "bargain_source_claimed":  "Opponent-Claimed\n(Unverified)",
}
CONDITION_ORDER = ["bargain_source_none", "bargain_source_verified", "bargain_source_claimed"]

# -- Load data -----------------------------------------------------------------
DATA_PATH = "writeup/data/info_source_bargaining_data.csv"
PLOT_DIR = "writeup/plots"

df = pd.read_csv(DATA_PATH)
df_deals = df[df["deal_reached"] == True].copy()

# ==============================================================================
# Figure 1: Deal Price by Condition
# ==============================================================================

fig1, ax1 = plt.subplots(figsize=(7, 4))

means, cis_lo, cis_hi = [], [], []
for cond in CONDITION_ORDER:
    prices = df_deals.loc[df_deals["condition"] == cond, "deal_price"]
    m = prices.mean()
    se = prices.std(ddof=1) / np.sqrt(len(prices))
    ci = 1.96 * se
    means.append(m)
    cis_lo.append(ci)
    cis_hi.append(ci)

x = np.arange(len(CONDITION_ORDER))
bar_width = 0.55

bars = ax1.bar(
    x, means, width=bar_width,
    color=[COLORS[c] for c in CONDITION_ORDER],
    edgecolor="white", linewidth=0.5, alpha=0.85, zorder=2,
)
ax1.errorbar(
    x, means, yerr=[cis_lo, cis_hi],
    fmt="none", ecolor="black", elinewidth=1.2, capsize=4, capthick=1.2, zorder=3,
)

# Jittered individual points
rng = np.random.default_rng(42)
for i, cond in enumerate(CONDITION_ORDER):
    prices = df_deals.loc[df_deals["condition"] == cond, "deal_price"].values
    jitter = rng.uniform(-0.15, 0.15, size=len(prices))
    ax1.scatter(
        np.full_like(prices, i, dtype=float) + jitter, prices,
        color=COLORS[cond], edgecolor="white", linewidth=0.4,
        s=28, alpha=0.7, zorder=4,
    )

# ZOPA reference lines
ax1.axhline(50, color="gray", linestyle="--", linewidth=0.9, alpha=0.6, zorder=1)
ax1.axhline(80, color="gray", linestyle="--", linewidth=0.9, alpha=0.6, zorder=1)
ax1.text(2.42, 50.5, "Seller cost ($50)", fontsize=8, color="gray", va="bottom", ha="right")
ax1.text(2.42, 80.5, "Buyer value ($80)", fontsize=8, color="gray", va="bottom", ha="right")

ax1.set_xticks(x)
ax1.set_xticklabels([LABELS[c] for c in CONDITION_ORDER])
ax1.set_ylabel("Deal Price ($)")
ax1.set_ylim(40, 85)
ax1.set_xlim(-0.6, 2.6)

fig1.tight_layout()
fig1.savefig(f"{PLOT_DIR}/results_info_source_price_by_condition.pdf")
plt.close(fig1)
print("Saved: results_info_source_price_by_condition.pdf")


# ==============================================================================
# Figure 2: Bargaining Dynamics (two panels)
# ==============================================================================

fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(10, 4))

# -- Panel A: Stacked bar - first-round accept vs counteroffer -----------------
accept_props, counter_props = [], []
for cond in CONDITION_ORDER:
    sub = df_deals[df_deals["condition"] == cond]
    n = len(sub)
    n_accept = (sub["first_human_response"] == "accept").sum()
    n_counter = (sub["first_human_response"] == "counteroffer").sum()
    accept_props.append(n_accept / n)
    counter_props.append(n_counter / n)

bar_w = 0.55
ax2a.bar(
    x, accept_props, width=bar_w,
    color=[COLORS[c] for c in CONDITION_ORDER],
    edgecolor="white", linewidth=0.5, alpha=0.9,
    label="Accept",
)
ax2a.bar(
    x, counter_props, width=bar_w, bottom=accept_props,
    color=[COLORS[c] for c in CONDITION_ORDER],
    edgecolor="white", linewidth=0.5, alpha=0.45,
    label="Counteroffer",
    hatch="///",
)

# Percentage labels inside each segment
for i, cond in enumerate(CONDITION_ORDER):
    if accept_props[i] > 0.05:
        ax2a.text(i, accept_props[i] / 2, f"{accept_props[i]:.0%}",
                  ha="center", va="center", fontsize=9, fontweight="bold", color="white")
    if counter_props[i] > 0.05:
        ax2a.text(i, accept_props[i] + counter_props[i] / 2, f"{counter_props[i]:.0%}",
                  ha="center", va="center", fontsize=9, fontweight="bold", color="black", alpha=0.7)

ax2a.set_xticks(x)
ax2a.set_xticklabels([LABELS[c] for c in CONDITION_ORDER], fontsize=9)
ax2a.set_ylabel("Proportion of Sessions")
ax2a.set_ylim(0, 1.05)
ax2a.set_title("A.  First-Round Response", fontsize=11, fontweight="bold", loc="left")

legend_elements = [
    Patch(facecolor="gray", alpha=0.9, edgecolor="white", label="Accept"),
    Patch(facecolor="gray", alpha=0.45, edgecolor="white", hatch="///", label="Counteroffer"),
]
ax2a.legend(handles=legend_elements, loc="upper right", frameon=False, fontsize=9)

# -- Panel B: Box plot of first counteroffer -----------------------------------
counter_data = []
counter_labels = []
counter_colors = []
for cond in CONDITION_ORDER:
    sub = df_deals[(df_deals["condition"] == cond) & (df_deals["first_human_response"] == "counteroffer")]
    vals = sub["first_human_counteroffer"].dropna().values
    if len(vals) > 0:
        counter_data.append(vals)
        counter_labels.append(LABELS[cond])
        counter_colors.append(COLORS[cond])

bp = ax2b.boxplot(
    counter_data, widths=0.5, patch_artist=True,
    medianprops=dict(color="black", linewidth=1.5),
    whiskerprops=dict(linewidth=0.8),
    capprops=dict(linewidth=0.8),
    flierprops=dict(marker="o", markersize=4, alpha=0.5),
)
for patch, color in zip(bp["boxes"], counter_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
    patch.set_edgecolor("white")
    patch.set_linewidth(0.5)

# Overlay individual points
rng2 = np.random.default_rng(99)
for i, vals in enumerate(counter_data):
    jitter = rng2.uniform(-0.12, 0.12, size=len(vals))
    ax2b.scatter(
        np.full_like(vals, i + 1, dtype=float) + jitter, vals,
        color=counter_colors[i], edgecolor="white", linewidth=0.4,
        s=28, alpha=0.7, zorder=5,
    )

ax2b.set_xticklabels(counter_labels, fontsize=9)
ax2b.set_ylabel("First Counteroffer ($)")
ax2b.set_title("B.  First Counteroffer Amount", fontsize=11, fontweight="bold", loc="left")

fig2.suptitle("Bargaining Dynamics by Information Condition", fontsize=12, fontweight="bold", y=1.02)
fig2.tight_layout()
fig2.savefig(f"{PLOT_DIR}/results_info_source_dynamics.pdf")
plt.close(fig2)
print("Saved: results_info_source_dynamics.pdf")


# ==============================================================================
# Figure 3: Rounds to Deal
# ==============================================================================

fig3, ax3 = plt.subplots(figsize=(7, 4))

round_vals = sorted(df_deals["rounds_played"].unique())
bar_w = 0.25
offsets = np.array([-bar_w, 0, bar_w])

for j, cond in enumerate(CONDITION_ORDER):
    sub = df_deals[df_deals["condition"] == cond]
    counts = []
    for r in round_vals:
        counts.append((sub["rounds_played"] == r).sum())
    counts = np.array(counts)
    ax3.bar(
        np.arange(len(round_vals)) + offsets[j],
        counts, width=bar_w,
        color=COLORS[cond], edgecolor="white", linewidth=0.5,
        alpha=0.85, label=LABELS[cond].replace("\n", " "),
    )

ax3.set_xticks(np.arange(len(round_vals)))
ax3.set_xticklabels([str(r) for r in round_vals])
ax3.set_xlabel("Rounds to Agreement")
ax3.set_ylabel("Number of Sessions")
ax3.yaxis.set_major_locator(MaxNLocator(integer=True))
ax3.legend(frameon=False, fontsize=9)

fig3.tight_layout()
fig3.savefig(f"{PLOT_DIR}/results_info_source_rounds.pdf")
plt.close(fig3)
print("Saved: results_info_source_rounds.pdf")

print("\nAll 3 figures generated successfully.")
