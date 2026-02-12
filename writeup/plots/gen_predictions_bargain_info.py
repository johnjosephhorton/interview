"""Generate prediction space figure for bargaining info experiment."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
fig.patch.set_facecolor("white")

conditions = ["Full\nInfo", "One-\nSided", "Two-\nSided"]
x_pos = [0, 1, 2]

# --- Panel A: Deal Rate ---
ax = axes[0]
# Exploratory: show uncertainty ranges
centers = [0.85, 0.70, 0.55]  # possible direction
low = [0.75, 0.50, 0.35]
high = [0.95, 0.90, 0.75]

for i, (c, lo, hi) in enumerate(zip(centers, low, high)):
    ax.plot([i, i], [lo, hi], color="#4A90D9", lw=3, alpha=0.4, solid_capstyle="round")
    ax.plot(i, c, "o", color="#4A90D9", markersize=10, zorder=3)
    ax.text(i, hi + 0.04, "?", ha="center", va="bottom", fontsize=14,
            fontweight="bold", color="#4A90D9", fontfamily="serif")

ax.axhline(y=0.70, color="#999999", linestyle=":", lw=1, alpha=0.6)
ax.text(2.35, 0.70, "null", fontsize=8, color="#999999", va="center", fontfamily="serif")

ax.set_xticks(x_pos)
ax.set_xticklabels(conditions, fontsize=9, fontfamily="serif")
ax.set_ylabel("Deal Rate", fontsize=11, fontfamily="serif")
ax.set_title("A. Deal Rate by Condition", fontsize=11, fontfamily="serif", fontweight="bold")
ax.set_ylim(0.1, 1.05)
ax.set_xlim(-0.5, 2.7)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(axis="y", labelsize=9)
for label in ax.get_yticklabels():
    label.set_fontfamily("serif")

# --- Panel B: Efficiency ---
ax = axes[1]
centers2 = [0.90, 0.65, 0.50]
low2 = [0.80, 0.40, 0.25]
high2 = [0.98, 0.85, 0.75]

for i, (c, lo, hi) in enumerate(zip(centers2, low2, high2)):
    ax.plot([i, i], [lo, hi], color="#5CB85C", lw=3, alpha=0.4, solid_capstyle="round")
    ax.plot(i, c, "s", color="#5CB85C", markersize=10, zorder=3)
    ax.text(i, hi + 0.04, "?", ha="center", va="bottom", fontsize=14,
            fontweight="bold", color="#5CB85C", fontfamily="serif")

ax.axhline(y=0.70, color="#999999", linestyle=":", lw=1, alpha=0.6)
ax.text(2.35, 0.70, "null", fontsize=8, color="#999999", va="center", fontfamily="serif")

ax.set_xticks(x_pos)
ax.set_xticklabels(conditions, fontsize=9, fontfamily="serif")
ax.set_ylabel("Efficiency (Surplus / Max)", fontsize=11, fontfamily="serif")
ax.set_title("B. Efficiency by Condition", fontsize=11, fontfamily="serif", fontweight="bold")
ax.set_ylim(0.1, 1.1)
ax.set_xlim(-0.5, 2.7)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(axis="y", labelsize=9)
for label in ax.get_yticklabels():
    label.set_fontfamily("serif")

# Suptitle
fig.suptitle("Predicted Outcome Space (Exploratory — No Directional Hypothesis)",
             fontsize=12, fontfamily="serif", fontweight="bold", y=1.02, color="#222222")

# Footnote
fig.text(0.5, -0.04,
         "Circles/squares = plausible center; bars = range of plausible outcomes; ? = direction unknown",
         ha="center", fontsize=8.5, fontfamily="serif", fontstyle="italic", color="#888888")

plt.tight_layout()
plt.savefig("/Users/benjaminmanning/interview/writeup/plots/predictions_bargain_info.pdf",
            bbox_inches="tight", dpi=300)
print("Saved predictions_bargain_info.pdf")
