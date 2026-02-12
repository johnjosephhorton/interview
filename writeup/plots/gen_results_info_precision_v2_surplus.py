"""Figure 3: Surplus Split — stacked horizontal bar chart."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pathlib

# ── Data ──────────────────────────────────────────────────────────────────────
DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "info_precision_bargaining_v2_data.csv"
OUT  = pathlib.Path(__file__).resolve().parent / "results_info_precision_v2_surplus.pdf"

df = pd.read_csv(DATA)

cond_order = ["none", "range", "exact"]
cond_labels = {"none": "No Info", "range": "Range Info", "exact": "Exact Info"}
zopa_vals = [2, 5]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
})

# Build row data: condition x ZOPA
rows = []
for cond in cond_order:
    for zopa in zopa_vals:
        subset = df[(df["condition"] == cond) & (df["zopa"] == zopa)]
        buyer_mean = subset["human_earnings"].mean()
        seller_mean = subset["ai_earnings"].mean()
        label = f"{cond_labels[cond]}, ZOPA=\\${zopa}"
        rows.append({
            "label": label,
            "buyer": buyer_mean,
            "seller": seller_mean,
            "zopa": zopa,
        })

labels = [r["label"] for r in rows]
buyer_vals = [r["buyer"] for r in rows]
seller_vals = [r["seller"] for r in rows]
zopa_maxes = [r["zopa"] for r in rows]

y_pos = np.arange(len(rows))

fig, ax = plt.subplots(figsize=(7, 3.8))

# Stacked bars
bars_buyer = ax.barh(
    y_pos, buyer_vals,
    height=0.55,
    color="#4C72B0",
    edgecolor="white",
    linewidth=0.5,
    label="Buyer (Human) Earnings",
)
bars_seller = ax.barh(
    y_pos, seller_vals,
    height=0.55,
    left=buyer_vals,
    color="#DD8452",
    edgecolor="white",
    linewidth=0.5,
    label="Seller (AI) Earnings",
)

# Maximum surplus outline
for i, zopa in enumerate(zopa_maxes):
    ax.barh(
        y_pos[i], zopa,
        height=0.55,
        fill=False,
        edgecolor="black",
        linewidth=1.2,
        linestyle="-",
    )

# Labels inside bars
for i in range(len(rows)):
    # Buyer label
    if buyer_vals[i] > 0.3:
        ax.text(
            buyer_vals[i] / 2, y_pos[i],
            f"${buyer_vals[i]:.2f}",
            ha="center", va="center",
            fontsize=8, color="white", fontweight="bold",
        )
    # Seller label
    if seller_vals[i] > 0.3:
        ax.text(
            buyer_vals[i] + seller_vals[i] / 2, y_pos[i],
            f"${seller_vals[i]:.2f}",
            ha="center", va="center",
            fontsize=8, color="white", fontweight="bold",
        )

ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=9.5)
ax.set_xlabel("Earnings ($)", fontsize=10)
ax.set_title("(C) Surplus Distribution", fontsize=11, fontweight="bold", pad=10)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.set_xlim(0, max(zopa_maxes) + 0.5)

ax.legend(fontsize=9, frameon=False, loc="lower right")

# Invert y so first row is on top
ax.invert_yaxis()

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print(f"Saved: {OUT}")
