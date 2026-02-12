"""Generate causal DAG for bargaining information structure experiment."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.set_xlim(-0.5, 10.5)
ax.set_ylim(-1, 6.5)
ax.axis("off")
fig.patch.set_facecolor("white")

# --- Node positions (left to right flow) ---
positions = {
    "Info\nStructure\n(X)": (1, 3.5),
    "Strategic\nPosturing\n(M1)": (5, 4.8),
    "First-Offer\nAnchoring\n(M2)": (5, 2.2),
    "Deal Rate &\nEfficiency\n(Y)": (9, 3.5),
    "Payoff\nStructure\n(Z1)": (1, 0.5),
    "AI\nStrategy\n(Z2)": (3.5, 0.5),
}

node_types = {
    "Info\nStructure\n(X)": "treatment",
    "Strategic\nPosturing\n(M1)": "mediator",
    "First-Offer\nAnchoring\n(M2)": "mediator",
    "Deal Rate &\nEfficiency\n(Y)": "outcome",
    "Payoff\nStructure\n(Z1)": "control",
    "AI\nStrategy\n(Z2)": "control",
}

style = {
    "treatment": dict(boxstyle="round,pad=0.4", facecolor="#4A90D9", edgecolor="#2C5F8A", linewidth=2, alpha=0.9),
    "mediator": dict(boxstyle="round,pad=0.4", facecolor="#E8E8E8", edgecolor="#888888", linewidth=1.5, alpha=0.9),
    "outcome": dict(boxstyle="round,pad=0.4", facecolor="#5CB85C", edgecolor="#3D7A3D", linewidth=2, alpha=0.9),
    "control": dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#888888", linewidth=1.5, linestyle="dashed"),
}

font_colors = {
    "treatment": "white",
    "mediator": "#333333",
    "outcome": "white",
    "control": "#555555",
}

# Draw nodes
for label, (x, y) in positions.items():
    ntype = node_types[label]
    bbox = style[ntype].copy()
    fontweight = "bold" if ntype in ("treatment", "outcome") else "normal"
    ax.text(x, y, label, ha="center", va="center", fontsize=10,
            fontfamily="serif", fontweight=fontweight,
            color=font_colors[ntype],
            bbox=bbox, zorder=3)

# --- Edges ---
def draw_arrow(ax, start, end, style="solid", color="black", lw=1.5, shrink=35):
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                linestyle=style, shrinkA=shrink, shrinkB=shrink),
                zorder=2)

# Causal paths (solid)
draw_arrow(ax, positions["Info\nStructure\n(X)"], positions["Strategic\nPosturing\n(M1)"])
draw_arrow(ax, positions["Info\nStructure\n(X)"], positions["First-Offer\nAnchoring\n(M2)"])
draw_arrow(ax, positions["Strategic\nPosturing\n(M1)"], positions["Deal Rate &\nEfficiency\n(Y)"])
draw_arrow(ax, positions["First-Offer\nAnchoring\n(M2)"], positions["Deal Rate &\nEfficiency\n(Y)"])

# Direct effect (dashed)
draw_arrow(ax, positions["Info\nStructure\n(X)"], positions["Deal Rate &\nEfficiency\n(Y)"],
           style="dashed", color="#666666")

# Control paths (thin gray)
draw_arrow(ax, positions["Payoff\nStructure\n(Z1)"], positions["Deal Rate &\nEfficiency\n(Y)"],
           color="#AAAAAA", lw=1.0)
draw_arrow(ax, positions["AI\nStrategy\n(Z2)"], positions["Deal Rate &\nEfficiency\n(Y)"],
           color="#AAAAAA", lw=1.0)

# Title
ax.text(5.25, 6.2, "How does information structure affect bargaining outcomes?",
        ha="center", va="center", fontsize=13, fontfamily="serif", fontweight="bold",
        color="#222222")

# Legend
legend_items = [
    mpatches.Patch(facecolor="#4A90D9", edgecolor="#2C5F8A", label="Treatment"),
    mpatches.Patch(facecolor="#E8E8E8", edgecolor="#888888", label="Mediator"),
    mpatches.Patch(facecolor="#5CB85C", edgecolor="#3D7A3D", label="Outcome"),
    mpatches.Patch(facecolor="white", edgecolor="#888888", linestyle="dashed", label="Control (held constant)"),
]
ax.legend(handles=legend_items, loc="lower right", fontsize=9, frameon=True,
          edgecolor="#CCCCCC", fancybox=True, prop={"family": "serif"})

plt.tight_layout()
plt.savefig("/Users/benjaminmanning/interview/writeup/plots/dag_bargain_info.pdf",
            bbox_inches="tight", dpi=300)
print("Saved dag_bargain_info.pdf")
