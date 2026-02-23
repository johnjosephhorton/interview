#!/usr/bin/env python3
"""Generate comparison figures for pre-fix vs post-fix PD Concordia results."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
PRE = ROOT / "transcripts/pd_concordia/2026-02-17_results.json"
POST = ROOT / "transcripts/pd_concordia/2026-02-18_post_fix_results.json"
OUT = Path(__file__).resolve().parent

with open(PRE) as f:
    pre = json.load(f)
with open(POST) as f:
    post = json.load(f)

# ── Figure 1: Round-by-round cooperation (pre vs post, 4 lines) ─────
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
rounds = range(1, 11)

for ax, label, data_pre, data_post in [
    (axes[0], "Player A", "a_choice", "a_choice"),
    (axes[1], "Player B", "b_choice", "b_choice"),
]:
    pre_rates = [sum(1 for r in pre if r["history"][rd][data_pre] == "cooperate") / 30 for rd in range(10)]
    post_rates = [sum(1 for r in post if r["history"][rd][data_post] == "cooperate") / 30 for rd in range(10)]
    ax.plot(rounds, pre_rates, "o-", color="#e74c3c", label="Pre-fix", linewidth=2)
    ax.plot(rounds, post_rates, "s-", color="#2ecc71", label="Post-fix", linewidth=2)
    ax.set_title(label, fontsize=13)
    ax.set_xlabel("Round")
    ax.set_ylabel("Cooperation Rate")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(range(1, 11))
    ax.legend()
    ax.grid(alpha=0.3)

fig.suptitle("Round-by-Round Cooperation: Pre-fix vs Post-fix", fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(OUT / "v2_cooperation_comparison.pdf", bbox_inches="tight")
plt.close()
print("Saved v2_cooperation_comparison.pdf")

# ── Figure 2: Earnings comparison (box plots + asymmetry) ────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 5))

# Panel 1: A earnings
pre_a = [r["a_total_earnings"] for r in pre]
post_a = [r["a_total_earnings"] for r in post]
pre_b = [r["b_total_earnings"] for r in pre]
post_b = [r["b_total_earnings"] for r in post]

bp = axes[0].boxplot([pre_a, post_a, pre_b, post_b],
                      labels=["Pre A", "Post A", "Pre B", "Post B"],
                      patch_artist=True)
colors = ["#e74c3c", "#2ecc71", "#e74c3c", "#2ecc71"]
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
axes[0].set_ylabel("Total Earnings ($)")
axes[0].set_title("Earnings by Player & Condition")
axes[0].axhline(30, color="gray", linestyle="--", alpha=0.5, label="Max ($30)")
axes[0].axhline(10, color="gray", linestyle=":", alpha=0.5, label="Min ($10)")
axes[0].legend(fontsize=8)

# Panel 2: A-B earnings gap
pre_gap = [a - b for a, b in zip(pre_a, pre_b)]
post_gap = [a - b for a, b in zip(post_a, post_b)]
bp2 = axes[1].boxplot([pre_gap, post_gap], labels=["Pre-fix", "Post-fix"], patch_artist=True)
bp2["boxes"][0].set_facecolor("#e74c3c")
bp2["boxes"][0].set_alpha(0.6)
bp2["boxes"][1].set_facecolor("#2ecc71")
bp2["boxes"][1].set_alpha(0.6)
axes[1].axhline(0, color="black", linestyle="-", linewidth=0.8)
axes[1].set_ylabel("A − B Earnings ($)")
axes[1].set_title("Earnings Asymmetry (A − B)")

# Panel 3: Efficiency
pre_eff = [r["efficiency"] for r in pre]
post_eff = [r["efficiency"] for r in post]
bp3 = axes[2].boxplot([pre_eff, post_eff], labels=["Pre-fix", "Post-fix"], patch_artist=True)
bp3["boxes"][0].set_facecolor("#e74c3c")
bp3["boxes"][0].set_alpha(0.6)
bp3["boxes"][1].set_facecolor("#2ecc71")
bp3["boxes"][1].set_alpha(0.6)
axes[2].set_ylabel("Efficiency")
axes[2].set_title("Efficiency Distribution")
axes[2].axhline(1.0, color="gray", linestyle="--", alpha=0.5)

fig.suptitle("Pre-fix vs Post-fix: Earnings & Efficiency", fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(OUT / "v2_earnings_comparison.pdf", bbox_inches="tight")
plt.close()
print("Saved v2_earnings_comparison.pdf")

# ── Figure 3: Choice heatmaps (2x2: pre-A, post-A, pre-B, post-B) ──
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

datasets = [
    (pre, "a_choice", "Pre-fix: Player A", axes[0, 0]),
    (post, "a_choice", "Post-fix: Player A", axes[0, 1]),
    (pre, "b_choice", "Pre-fix: Player B", axes[1, 0]),
    (post, "b_choice", "Post-fix: Player B", axes[1, 1]),
]

from matplotlib.colors import ListedColormap
cmap = ListedColormap(["#e74c3c", "#2ecc71"])

for data, key, title, ax in datasets:
    # Sort by total cooperation
    sims = sorted(data, key=lambda r: sum(1 for h in r["history"] if h[key] == "cooperate"))
    matrix = np.array([[1 if h[key] == "cooperate" else 0 for h in r["history"]] for r in sims])
    ax.imshow(matrix, aspect="auto", cmap=cmap, interpolation="nearest")
    ax.set_xlabel("Round")
    ax.set_ylabel("Simulation (sorted)")
    ax.set_xticks(range(10))
    ax.set_xticklabels(range(1, 11))
    ax.set_title(title, fontsize=12)

fig.suptitle("Choice Heatmaps: Pre-fix vs Post-fix", fontsize=14, y=1.01)
fig.tight_layout()
fig.savefig(OUT / "v2_choice_heatmap.pdf", bbox_inches="tight")
plt.close()
print("Saved v2_choice_heatmap.pdf")

# ── Figure 4: Full cooperation rate comparison (bar chart) ───────────
fig, ax = plt.subplots(figsize=(6, 4))
pre_fc = sum(1 for r in pre if all(h["a_choice"] == "cooperate" and h["b_choice"] == "cooperate" for h in r["history"]))
post_fc = sum(1 for r in post if all(h["a_choice"] == "cooperate" and h["b_choice"] == "cooperate" for h in r["history"]))
bars = ax.bar(["Pre-fix\n(sequential, shared obs)", "Post-fix\n(randomized, role-relative)"],
              [pre_fc / 30 * 100, post_fc / 30 * 100],
              color=["#e74c3c", "#2ecc71"], alpha=0.7, edgecolor="black")
ax.set_ylabel("Full Cooperation Games (%)")
ax.set_title("Full Cooperation Rate: Pre vs Post")
ax.set_ylim(0, 100)
for bar, n in zip(bars, [pre_fc, post_fc]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
            f"{n}/30", ha="center", fontsize=12, fontweight="bold")
ax.annotate("Fisher p = 0.015", xy=(0.5, 0.85), xycoords="axes fraction",
            ha="center", fontsize=11, fontstyle="italic")
fig.tight_layout()
fig.savefig(OUT / "v2_full_coop_rate.pdf", bbox_inches="tight")
plt.close()
print("Saved v2_full_coop_rate.pdf")
