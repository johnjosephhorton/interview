"""Prediction space figure: expected deal rates and anchoring index by condition."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
fig.patch.set_facecolor("white")

conditions = ["No Info\n(Baseline)", "Game-\nDisclosed", "Opponent-\nClaimed"]
colors = ["#6B7280", "#2563EB", "#16A34A"]
x = np.arange(len(conditions))

# ── Panel 1: Deal Rate ──
ax1 = axes[0]
means = [0.60, 0.45, 0.75]
lows =  [0.45, 0.30, 0.60]
highs = [0.75, 0.60, 0.88]
yerr_low = [m - l for m, l in zip(means, lows)]
yerr_high = [h - m for m, h in zip(means, highs)]

bars = ax1.bar(x, means, color=colors, alpha=0.35, width=0.6, edgecolor=colors, linewidth=1.5)
ax1.errorbar(x, means, yerr=[yerr_low, yerr_high], fmt="o", color="black",
             markersize=6, capsize=8, capthick=1.5, linewidth=1.5, zorder=5)
ax1.axhline(y=0.60, color="#9CA3AF", linestyle=":", linewidth=1, label="Baseline mean")
ax1.set_ylabel("Deal Rate", fontsize=10, fontfamily="serif")
ax1.set_title("Primary: Deal Rate", fontsize=11, fontfamily="serif", fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels(conditions, fontsize=8, fontfamily="serif")
ax1.set_ylim(0, 1.0)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.tick_params(axis="y", labelsize=8)
# Annotations
ax1.annotate("", xy=(1, 0.46), xytext=(0, 0.61),
             arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.5, linestyle="--"))
ax1.text(0.5, 0.57, "info\ncurse", ha="center", fontsize=7, color="#DC2626", fontfamily="serif")
ax1.annotate("", xy=(2, 0.76), xytext=(0, 0.61),
             arrowprops=dict(arrowstyle="->", color="#16A34A", lw=1.5, linestyle="--"))
ax1.text(1.0, 0.72, "reciprocity\nboost", ha="center", fontsize=7, color="#16A34A", fontfamily="serif")

# ── Panel 2: Anchoring Index ──
ax2 = axes[1]
means2 = [0.50, 0.25, 0.55]
lows2 =  [0.35, 0.12, 0.40]
highs2 = [0.65, 0.40, 0.68]
yerr_low2 = [m - l for m, l in zip(means2, lows2)]
yerr_high2 = [h - m for m, h in zip(means2, highs2)]

bars2 = ax2.bar(x, means2, color=colors, alpha=0.35, width=0.6, edgecolor=colors, linewidth=1.5)
ax2.errorbar(x, means2, yerr=[yerr_low2, yerr_high2], fmt="o", color="black",
             markersize=6, capsize=8, capthick=1.5, linewidth=1.5, zorder=5)
ax2.axhline(y=0.50, color="#9CA3AF", linestyle=":", linewidth=1)
ax2.set_ylabel("Anchoring Index\n(higher = more cooperative)", fontsize=9, fontfamily="serif")
ax2.set_title("Mechanism: First-Offer Anchoring", fontsize=11, fontfamily="serif", fontweight="bold")
ax2.set_xticks(x)
ax2.set_xticklabels(conditions, fontsize=8, fontfamily="serif")
ax2.set_ylim(0, 1.0)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.tick_params(axis="y", labelsize=8)
ax2.text(1, 0.15, "exploitative\nanchoring", ha="center", fontsize=7, color="#2563EB",
         fontfamily="serif", fontstyle="italic")

# ── Panel 3: Concession Speed ──
ax3 = axes[2]
means3 = [3.5, 4.2, 2.5]
lows3 =  [2.5, 3.2, 1.5]
highs3 = [4.5, 5.2, 3.5]
yerr_low3 = [m - l for m, l in zip(means3, lows3)]
yerr_high3 = [h - m for m, h in zip(means3, highs3)]

bars3 = ax3.bar(x, means3, color=colors, alpha=0.35, width=0.6, edgecolor=colors, linewidth=1.5)
ax3.errorbar(x, means3, yerr=[yerr_low3, yerr_high3], fmt="o", color="black",
             markersize=6, capsize=8, capthick=1.5, linewidth=1.5, zorder=5)
ax3.axhline(y=3.5, color="#9CA3AF", linestyle=":", linewidth=1)
ax3.set_ylabel("Rounds to Deal\n(lower = faster convergence)", fontsize=9, fontfamily="serif")
ax3.set_title("Mechanism: Concession Speed", fontsize=11, fontfamily="serif", fontweight="bold")
ax3.set_xticks(x)
ax3.set_xticklabels(conditions, fontsize=8, fontfamily="serif")
ax3.set_ylim(0, 6.5)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
ax3.tick_params(axis="y", labelsize=8)
ax3.text(2, 1.8, "faster\nconvergence", ha="center", fontsize=7, color="#16A34A",
         fontfamily="serif", fontstyle="italic")

# ── Suptitle ──
fig.suptitle("Pre-Data Predictions: Information Source Effects on Bargaining",
             fontsize=13, fontfamily="serif", fontweight="bold", y=1.02)

# ── Note ──
fig.text(0.5, -0.04,
         "Bars show plausible ranges (not data). Center dots = point predictions. "
         "Dotted lines = baseline. These are directional hypotheses, not simulated results.",
         ha="center", fontsize=8, fontfamily="serif", color="#6B7280", fontstyle="italic")

plt.tight_layout()
fig.savefig("/Users/benjaminmanning/interview/writeup/plots/predictions_info_source.pdf",
            bbox_inches="tight", dpi=300)
print("Predictions figure saved.")
