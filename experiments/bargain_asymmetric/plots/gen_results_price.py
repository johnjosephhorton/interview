#!/usr/bin/env python3
"""Figure 1: Deal price vs. fair price midpoint."""
import csv, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DATA = "experiments/bargain_asymmetric/data/data.csv"
OUT  = "experiments/bargain_asymmetric/plots/results_price.pdf"

rows = []
with open(DATA) as f:
    for r in csv.DictReader(f):
        def fv(k): return float(r[k]) if k != "sim_id" and r[k] not in ("","None") else None
        rows.append({k: fv(k) for k in r})

deals = [r for r in rows if r["deal_reached"] == 1.0]
prices     = np.array([r["deal_price"] for r in deals if r["deal_price"] is not None])
fair       = np.array([r["fair_price"]  for r in deals if r["fair_price"]  is not None])
zopa       = np.array([r["zopa"]        for r in deals if r["zopa"]        is not None])

# Scatter: deal_price vs fair_price, coloured by ZOPA
fig, ax = plt.subplots(figsize=(5.5, 4.5))
sc = ax.scatter(fair, prices, c=zopa, cmap="viridis", s=60, edgecolors="0.3", linewidths=0.5, zorder=3)
lims = [40, 75]
ax.plot(lims, lims, "--", color="0.5", lw=1.2, label="Price = Fair price", zorder=2)
ax.set_xlim(lims); ax.set_ylim(lims)
ax.set_xlabel("Fair price (midpoint of ZOPA) [$]")
ax.set_ylabel("Agreed deal price [$]")
ax.set_title("Deal Price vs. Fair Price\n(bilateral asymmetric info bargaining)")
cb = fig.colorbar(sc, ax=ax, label="ZOPA [$]")
ax.legend(loc="upper left", fontsize=8)
ax.grid(True, alpha=0.25)
plt.tight_layout()
plt.savefig(OUT)
print(f"Saved {OUT}")

# Stats annotation
dev = prices - fair
print(f"Mean deviation from fair price: {np.mean(dev):+.2f}")
print(f"Points above diagonal: {np.sum(prices > fair)}/{len(prices)}")
