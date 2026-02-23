#!/usr/bin/env python3
"""Generate figures for pd_concordia analysis."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

PLOT_DIR = Path("experiments/pd_concordia/plots")
DATA_FILE = Path("transcripts/pd_concordia/2026-02-17_results.json")

with open(DATA_FILE) as f:
    results = json.load(f)

n = len(results)

# ── Figure 1: Round-by-round cooperation rates ──────────────────────────
rounds = list(range(1, 11))
a_coop_by_round = []
b_coop_by_round = []
mutual_coop_by_round = []
mutual_def_by_round = []

for rd in range(10):
    a_c = sum(1 for r in results if r["history"][rd]["a_choice"] == "cooperate") / n
    b_c = sum(1 for r in results if r["history"][rd]["b_choice"] == "cooperate") / n
    mc = sum(1 for r in results
             if r["history"][rd]["a_choice"] == "cooperate"
             and r["history"][rd]["b_choice"] == "cooperate") / n
    md = sum(1 for r in results
             if r["history"][rd]["a_choice"] == "defect"
             and r["history"][rd]["b_choice"] == "defect") / n
    a_coop_by_round.append(a_c)
    b_coop_by_round.append(b_c)
    mutual_coop_by_round.append(mc)
    mutual_def_by_round.append(md)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(rounds, a_coop_by_round, "o-", label="Player A coop rate", color="#2196F3", linewidth=2)
ax.plot(rounds, b_coop_by_round, "s-", label="Player B coop rate", color="#FF9800", linewidth=2)
ax.plot(rounds, mutual_coop_by_round, "^--", label="Mutual cooperation", color="#4CAF50", linewidth=1.5, alpha=0.7)
ax.plot(rounds, mutual_def_by_round, "v--", label="Mutual defection", color="#F44336", linewidth=1.5, alpha=0.7)
ax.set_xlabel("Round", fontsize=12)
ax.set_ylabel("Rate", fontsize=12)
ax.set_title("Cooperation Dynamics Over 10 Rounds (N=30)", fontsize=13)
ax.set_xticks(rounds)
ax.set_ylim(-0.05, 1.05)
ax.legend(loc="lower left", fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(PLOT_DIR / "results_cooperation_dynamics.pdf")
plt.close()
print("Saved: results_cooperation_dynamics.pdf")

# ── Figure 2: Earnings distribution ─────────────────────────────────────
a_earn = [r["a_total_earnings"] for r in results]
b_earn = [r["b_total_earnings"] for r in results]
eff = [r["efficiency"] for r in results]

fig, axes = plt.subplots(1, 3, figsize=(12, 4))

# Panel A: Earnings histograms
bins = np.arange(0, 52, 2)
axes[0].hist(a_earn, bins=bins, alpha=0.6, label="Player A", color="#2196F3", edgecolor="white")
axes[0].hist(b_earn, bins=bins, alpha=0.6, label="Player B", color="#FF9800", edgecolor="white")
axes[0].axvline(np.mean(a_earn), color="#2196F3", linestyle="--", linewidth=1.5)
axes[0].axvline(np.mean(b_earn), color="#FF9800", linestyle="--", linewidth=1.5)
axes[0].set_xlabel("Total Earnings ($)")
axes[0].set_ylabel("Count")
axes[0].set_title("Earnings Distribution")
axes[0].legend(fontsize=9)

# Panel B: Joint earnings / efficiency
axes[1].hist(eff, bins=np.arange(0.3, 1.05, 0.05), color="#4CAF50", edgecolor="white", alpha=0.7)
axes[1].axvline(np.mean(eff), color="#4CAF50", linestyle="--", linewidth=2)
axes[1].axvline(1/3, color="#F44336", linestyle=":", linewidth=1.5, label="Mutual defection")
axes[1].axvline(1.0, color="#2196F3", linestyle=":", linewidth=1.5, label="Full cooperation")
axes[1].set_xlabel("Efficiency (joint / max)")
axes[1].set_ylabel("Count")
axes[1].set_title("Efficiency Distribution")
axes[1].legend(fontsize=9)

# Panel C: A vs B scatter
axes[2].scatter(a_earn, b_earn, alpha=0.6, color="#9C27B0", s=60, edgecolor="white", zorder=3)
axes[2].plot([0, 50], [0, 50], "k--", alpha=0.3, label="Equal earnings")
axes[2].axhline(30, color="gray", linestyle=":", alpha=0.3)
axes[2].axvline(30, color="gray", linestyle=":", alpha=0.3)
axes[2].set_xlabel("Player A Earnings ($)")
axes[2].set_ylabel("Player B Earnings ($)")
axes[2].set_title("A vs B Earnings")
axes[2].set_xlim(0, 52)
axes[2].set_ylim(0, 52)
axes[2].legend(fontsize=9)

plt.tight_layout()
fig.savefig(PLOT_DIR / "results_earnings.pdf")
plt.close()
print("Saved: results_earnings.pdf")

# ── Figure 3: Game outcome typology ─────────────────────────────────────
# Heatmap showing choice sequences across all 30 games
fig, axes = plt.subplots(1, 2, figsize=(12, 8))

# Build choice matrices (1 = cooperate, 0 = defect)
a_matrix = np.zeros((n, 10))
b_matrix = np.zeros((n, 10))
for i, r in enumerate(results):
    for j, h in enumerate(r["history"]):
        a_matrix[i, j] = 1 if h["a_choice"] == "cooperate" else 0
        b_matrix[i, j] = 1 if h["b_choice"] == "cooperate" else 0

# Sort by total cooperation (most cooperative at top)
a_order = np.argsort(-a_matrix.sum(axis=1))
b_order = np.argsort(-b_matrix.sum(axis=1))

cmap = matplotlib.colors.ListedColormap(["#F44336", "#4CAF50"])

im_a = axes[0].imshow(a_matrix[a_order], cmap=cmap, aspect="auto", interpolation="nearest")
axes[0].set_xlabel("Round")
axes[0].set_ylabel("Simulation (sorted)")
axes[0].set_title("Player A Choices")
axes[0].set_xticks(range(10))
axes[0].set_xticklabels(range(1, 11))

im_b = axes[1].imshow(b_matrix[b_order], cmap=cmap, aspect="auto", interpolation="nearest")
axes[1].set_xlabel("Round")
axes[1].set_ylabel("Simulation (sorted)")
axes[1].set_title("Player B Choices")
axes[1].set_xticks(range(10))
axes[1].set_xticklabels(range(1, 11))

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor="#4CAF50", label="Cooperate"),
                   Patch(facecolor="#F44336", label="Defect")]
fig.legend(handles=legend_elements, loc="lower center", ncol=2, fontsize=11, frameon=False)
plt.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig(PLOT_DIR / "results_choice_heatmap.pdf")
plt.close()
print("Saved: results_choice_heatmap.pdf")
