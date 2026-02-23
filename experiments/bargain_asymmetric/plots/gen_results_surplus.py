#!/usr/bin/env python3
"""Figure 2: Surplus split — buyer vs AI earnings."""
import csv, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = "experiments/bargain_asymmetric/data/data.csv"
OUT  = "experiments/bargain_asymmetric/plots/results_surplus.pdf"

rows = []
with open(DATA) as f:
    for r in csv.DictReader(f):
        def fv(k): return float(r[k]) if k != "sim_id" and r[k] not in ("","None") else None
        rows.append({k: fv(k) for k in r})

deals = [r for r in rows if r["deal_reached"] == 1.0]
human = np.array([r["human_earnings"] for r in deals if r["human_earnings"] is not None])
ai    = np.array([r["ai_earnings"]    for r in deals if r["ai_earnings"]    is not None])
zopa  = np.array([r["zopa"]           for r in deals if r["zopa"]           is not None])

fig, axes = plt.subplots(1, 2, figsize=(9, 4))

# Panel A: scatter human vs AI earnings
ax = axes[0]
sc = ax.scatter(human, ai, c=zopa, cmap="viridis", s=60, edgecolors="0.3", linewidths=0.5, zorder=3)
lim = [0, 60]
ax.plot(lim, lim, "--", color="0.5", lw=1.2, label="Equal split", zorder=2)
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("Human (buyer) earnings [$]")
ax.set_ylabel("AI (seller) earnings [$]")
ax.set_title("Surplus Split per Session")
fig.colorbar(sc, ax=ax, label="ZOPA [$]")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.25)

# Panel B: stacked bar of mean earnings by seller_cost bin
ax2 = axes[1]
costs = sorted(set(r["seller_cost"] for r in deals if r["seller_cost"] is not None))
mean_h = [np.mean([r["human_earnings"] for r in deals if r["seller_cost"] == c]) for c in costs]
mean_a = [np.mean([r["ai_earnings"]    for r in deals if r["seller_cost"] == c]) for c in costs]
x = np.arange(len(costs))
w = 0.55
b1 = ax2.bar(x, mean_h, w, color="#4878d0", label="Human (buyer)", edgecolor="white")
b2 = ax2.bar(x, mean_a, w, bottom=mean_h, color="#ee854a", label="AI (seller)", edgecolor="white")
ax2.set_xticks(x)
ax2.set_xticklabels([f"${int(c)}" for c in costs])
ax2.set_xlabel("Seller cost")
ax2.set_ylabel("Mean earnings [$]")
ax2.set_title("Mean Earnings by Seller Cost")
ax2.legend(fontsize=8)
ax2.grid(axis="y", alpha=0.25)

plt.tight_layout()
plt.savefig(OUT)
print(f"Saved {OUT}")
print(f"Human mean=${np.mean(human):.2f}, AI mean=${np.mean(ai):.2f}")
print(f"AI earns more in {np.sum(ai>human)}/{len(ai)} sessions")
