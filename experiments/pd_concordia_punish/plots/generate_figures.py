#!/usr/bin/env python3
"""Generate figures for baseline vs punishment PD experiment."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = ROOT / "transcripts/pd_concordia/2026-02-18_post_fix_results.json"
PUNISH = ROOT / "transcripts/pd_concordia_punish/2026-02-21_results.json"
OUT = Path(__file__).resolve().parent

with open(BASELINE) as f:
    base = json.load(f)
with open(PUNISH) as f:
    pun = json.load(f)

# ── Figure 1: Main outcome — cooperation rate and full coop bar chart ──
fig, axes = plt.subplots(1, 3, figsize=(14, 5))

# Panel 1: Average cooperation rate
base_coop = [(r["a_cooperation_rate"] + r["b_cooperation_rate"]) / 2 for r in base]
pun_coop = [(r["a_cooperation_rate"] + r["b_cooperation_rate"]) / 2 for r in pun]

bp = axes[0].boxplot([base_coop, pun_coop], tick_labels=["Baseline\n(no punishment)", "Punishment\n(available)"],
                      patch_artist=True, widths=0.5)
bp["boxes"][0].set_facecolor("#e74c3c")
bp["boxes"][0].set_alpha(0.6)
bp["boxes"][1].set_facecolor("#2ecc71")
bp["boxes"][1].set_alpha(0.6)
axes[0].set_ylabel("Average Cooperation Rate")
axes[0].set_title("Cooperation Rate by Condition")
axes[0].set_ylim(0, 1.1)
axes[0].annotate(f"p < 0.0001", xy=(0.5, 0.02), xycoords="axes fraction",
                 ha="center", fontsize=10, fontstyle="italic")

# Panel 2: Full cooperation rate
base_fc = sum(1 for r in base if all(h["a_choice"] == "cooperate" and h["b_choice"] == "cooperate" for h in r["history"]))
pun_fc = sum(1 for r in pun if all(h["a_choice"] == "cooperate" and h["b_choice"] == "cooperate" for h in r["history"]))
bars = axes[1].bar(["Baseline", "Punishment"], [base_fc / 30 * 100, pun_fc / 30 * 100],
                    color=["#e74c3c", "#2ecc71"], alpha=0.7, edgecolor="black", width=0.5)
axes[1].set_ylabel("Full Cooperation Games (%)")
axes[1].set_title("Full Cooperation Rate")
axes[1].set_ylim(0, 110)
for bar, n in zip(bars, [base_fc, pun_fc]):
    axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                 f"{n}/30", ha="center", fontsize=12, fontweight="bold")
axes[1].annotate("Fisher p < 0.0001", xy=(0.5, 0.85), xycoords="axes fraction",
                 ha="center", fontsize=10, fontstyle="italic")

# Panel 3: Efficiency
base_eff = [r["efficiency"] for r in base]
pun_eff = [(r["a_total_earnings"] + r["b_total_earnings"]) / 60 for r in pun]
bp3 = axes[2].boxplot([base_eff, pun_eff], tick_labels=["Baseline", "Punishment"],
                       patch_artist=True, widths=0.5)
bp3["boxes"][0].set_facecolor("#e74c3c")
bp3["boxes"][0].set_alpha(0.6)
bp3["boxes"][1].set_facecolor("#2ecc71")
bp3["boxes"][1].set_alpha(0.6)
axes[2].set_ylabel("Efficiency (joint / max)")
axes[2].set_title("Efficiency Distribution")
axes[2].set_ylim(0, 1.1)
axes[2].axhline(1.0, color="gray", linestyle="--", alpha=0.5)
axes[2].annotate(f"p < 0.0001", xy=(0.5, 0.02), xycoords="axes fraction",
                 ha="center", fontsize=10, fontstyle="italic")

fig.suptitle("Baseline vs Punishment: Primary Outcomes", fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(OUT / "results_main_outcomes.pdf", bbox_inches="tight")
plt.close()
print("Saved results_main_outcomes.pdf")

# ── Figure 2: Round-by-round cooperation comparison ──────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
rounds = range(1, 11)

for ax, label, key in [(axes[0], "Player A", "a_choice"), (axes[1], "Player B", "b_choice")]:
    base_rates = [sum(1 for r in base if r["history"][rd][key] == "cooperate") / 30 for rd in range(10)]
    pun_rates = [sum(1 for r in pun if r["history"][rd][key] == "cooperate") / 30 for rd in range(10)]
    ax.plot(rounds, base_rates, "o-", color="#e74c3c", label="Baseline", linewidth=2, markersize=6)
    ax.plot(rounds, pun_rates, "s-", color="#2ecc71", label="Punishment", linewidth=2, markersize=6)
    ax.fill_between(rounds, base_rates, pun_rates, alpha=0.1, color="#2ecc71")
    ax.set_title(label, fontsize=13)
    ax.set_xlabel("Round")
    ax.set_ylabel("Cooperation Rate")
    ax.set_ylim(0, 1.08)
    ax.set_xticks(range(1, 11))
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)

fig.suptitle("Round-by-Round Cooperation: Baseline vs Punishment", fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(OUT / "results_round_by_round.pdf", bbox_inches="tight")
plt.close()
print("Saved results_round_by_round.pdf")

# ── Figure 3: Earnings scatter + distribution ────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 5))

# Panel 1: A vs B earnings scatter
base_a = [r["a_total_earnings"] for r in base]
base_b = [r["b_total_earnings"] for r in base]
pun_a = [r["a_total_earnings"] for r in pun]
pun_b = [r["b_total_earnings"] for r in pun]

# Jitter for punishment since almost all are at (30,30)
np.random.seed(42)
pun_a_j = [a + np.random.uniform(-0.5, 0.5) for a in pun_a]
pun_b_j = [b + np.random.uniform(-0.5, 0.5) for b in pun_b]

axes[0].scatter(base_a, base_b, c="#e74c3c", alpha=0.6, s=50, label="Baseline", edgecolors="black", linewidths=0.5)
axes[0].scatter(pun_a_j, pun_b_j, c="#2ecc71", alpha=0.6, s=50, label="Punishment", edgecolors="black", linewidths=0.5, marker="s")
axes[0].plot([0, 35], [0, 35], "k--", alpha=0.3, label="A = B")
axes[0].set_xlabel("Player A Earnings ($)")
axes[0].set_ylabel("Player B Earnings ($)")
axes[0].set_title("Earnings: A vs B")
axes[0].legend(fontsize=9)
axes[0].set_xlim(-5, 35)
axes[0].set_ylim(-5, 35)

# Panel 2: Joint earnings distribution
axes[1].hist([r["joint_earnings"] for r in base], bins=range(20, 65, 4), alpha=0.6,
             color="#e74c3c", label="Baseline", edgecolor="black")
axes[1].hist([r["a_total_earnings"] + r["b_total_earnings"] for r in pun], bins=range(20, 65, 4), alpha=0.6,
             color="#2ecc71", label="Punishment", edgecolor="black")
axes[1].axvline(60, color="gray", linestyle="--", alpha=0.5, label="Max ($60)")
axes[1].set_xlabel("Joint Earnings ($)")
axes[1].set_ylabel("Count")
axes[1].set_title("Joint Earnings Distribution")
axes[1].legend(fontsize=9)

fig.suptitle("Earnings Comparison", fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(OUT / "results_earnings.pdf", bbox_inches="tight")
plt.close()
print("Saved results_earnings.pdf")

# ── Figure 4: The one interesting game (sim 27) ──────────────────────
sim27 = [r for r in pun if r["sim_id"] == 26][0]  # 0-indexed
fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

rounds = range(1, 11)
h = sim27["history"]
a_choices = [1 if x["a_choice"] == "cooperate" else 0 for x in h]
b_choices = [1 if x["b_choice"] == "cooperate" else 0 for x in h]
a_punish = [1 if x["a_punish"] == "punish" else 0 for x in h]
b_punish = [1 if x["b_punish"] == "punish" else 0 for x in h]
a_earn = [x["a_round_earned"] for x in h]
b_earn = [x["b_round_earned"] for x in h]

# Top: choices
axes[0].step(rounds, a_choices, where="mid", color="#3498db", linewidth=2, label="A cooperates")
axes[0].step(rounds, b_choices, where="mid", color="#e67e22", linewidth=2, label="B cooperates")
# Mark punishment rounds
for rd, (ap, bp) in enumerate(zip(a_punish, b_punish), 1):
    if ap:
        axes[0].annotate("A punish", xy=(rd, 0.5), fontsize=7, ha="center", color="#3498db",
                         fontweight="bold")
    if bp:
        axes[0].annotate("B punish", xy=(rd, 0.4), fontsize=7, ha="center", color="#e67e22",
                         fontweight="bold")
axes[0].set_ylabel("Cooperated?")
axes[0].set_yticks([0, 1])
axes[0].set_yticklabels(["Defect", "Cooperate"])
axes[0].legend(loc="upper right", fontsize=9)
axes[0].set_title("Simulation 27: Punishment Restores Cooperation", fontsize=13)
axes[0].grid(alpha=0.3)

# Bottom: round earnings
axes[1].bar([r - 0.15 for r in rounds], a_earn, width=0.3, color="#3498db", alpha=0.7, label="A earnings")
axes[1].bar([r + 0.15 for r in rounds], b_earn, width=0.3, color="#e67e22", alpha=0.7, label="B earnings")
axes[1].axhline(0, color="black", linewidth=0.5)
axes[1].set_xlabel("Round")
axes[1].set_ylabel("Round Earnings ($)")
axes[1].set_xticks(range(1, 11))
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.3)

fig.tight_layout()
fig.savefig(OUT / "results_sim27_detail.pdf", bbox_inches="tight")
plt.close()
print("Saved results_sim27_detail.pdf")
