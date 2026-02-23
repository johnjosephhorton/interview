#!/usr/bin/env python3
"""Figure 3: Bargaining dynamics — offer trajectories and rounds."""
import csv, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = "experiments/bargain_asymmetric/data/data.csv"
OUT  = "experiments/bargain_asymmetric/plots/results_dynamics.pdf"

rows = []
with open(DATA) as f:
    for r in csv.DictReader(f):
        def fv(k): return float(r[k]) if k != "sim_id" and r[k] not in ("","None") else None
        rows.append({k: fv(k) for k in r})

deals = [r for r in rows if r["deal_reached"] == 1.0]

fig, axes = plt.subplots(1, 2, figsize=(9, 4))

# Panel A: first buyer offer vs. final deal price, coloured by ZOPA
ax = axes[0]
x = [r["first_buyer_offer"] for r in deals if r["first_buyer_offer"] and r["deal_price"]]
y = [r["deal_price"]        for r in deals if r["first_buyer_offer"] and r["deal_price"]]
c = [r["zopa"]              for r in deals if r["first_buyer_offer"] and r["deal_price"]]
sc = ax.scatter(x, y, c=c, cmap="viridis", s=60, edgecolors="0.3", linewidths=0.5, zorder=3)
lim = [30, 80]
ax.plot(lim, lim, "--", color="0.5", lw=1.0, label="No concession")
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("Buyer's first offer [$]")
ax.set_ylabel("Final deal price [$]")
ax.set_title("Opening Offer vs. Final Price")
fig.colorbar(sc, ax=ax, label="ZOPA [$]")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.25)

# Panel B: histogram of rounds to deal
ax2 = axes[1]
rds = [r["rounds_to_deal"] for r in rows if r["rounds_to_deal"] is not None]
bins = np.arange(0.5, 7.5, 1)
ax2.hist(rds, bins=bins, color="#4878d0", edgecolor="white", alpha=0.85)
ax2.axvline(np.mean(rds), color="#ee854a", lw=1.5, linestyle="--",
            label=f"Mean = {np.mean(rds):.1f}")
ax2.set_xlabel("Rounds to deal")
ax2.set_ylabel("Count (sessions)")
ax2.set_title("Distribution of Rounds to Deal")
ax2.set_xticks(range(1, 7))
ax2.legend(fontsize=8)
ax2.grid(axis="y", alpha=0.25)

plt.tight_layout()
plt.savefig(OUT)
print(f"Saved {OUT}")
print(f"Mean rounds: {np.mean(rds):.2f}, mode: {max(set(rds), key=rds.count)}")
