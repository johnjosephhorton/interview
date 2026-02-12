"""Generate causal DAG for the information-source bargaining hypothesis."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(12, 6.5))
ax.set_xlim(-0.5, 10.5)
ax.set_ylim(-1.5, 5.5)
ax.axis("off")
fig.patch.set_facecolor("white")

# ── colours ──
blue = "#2563EB"
gray = "#6B7280"
green = "#16A34A"
white = "#FFFFFF"
lightgray = "#F3F4F6"

# ── node positions (x, y) ──
nodes = {
    "X":  (1.0, 2.5),   # Treatment: Information Source
    "M1": (5.0, 4.0),   # Mediator 1: Exploitative Anchoring
    "M2": (5.0, 1.0),   # Mediator 2: Reciprocal Trust
    "Y":  (9.0, 2.5),   # Outcome: Deal Rate
    "Z":  (5.0, -0.5),  # Control: ZOPA size / info content
}

labels = {
    "X":  "Information\nSource (X)",
    "M1": "Exploitative\nAnchoring ($M_1$)",
    "M2": "Reciprocal\nTrust ($M_2$)",
    "Y":  "Deal\nRate (Y)",
    "Z":  "ZOPA Size &\nInfo Content (Z)",
}

sublabels = {
    "X":  "None / Game-disclosed /\nOpponent-claimed",
    "M1": "Informed player anchors\nnear opponent's limit",
    "M2": "Voluntary sharing\ncreates obligation",
    "Y":  "Binary: deal\nreached or not",
    "Z":  "Held constant\nacross conditions",
}

box_w, box_h = 2.2, 1.1

def draw_node(name, color, text_color, dashed=False):
    x, y = nodes[name]
    style = "round,pad=0.15"
    bbox = FancyBboxPatch(
        (x - box_w / 2, y - box_h / 2), box_w, box_h,
        boxstyle=style, facecolor=color, edgecolor="black",
        linewidth=1.5 if not dashed else 1.2,
        linestyle="--" if dashed else "-",
        zorder=3,
    )
    ax.add_patch(bbox)
    ax.text(x, y + 0.12, labels[name], ha="center", va="center",
            fontsize=10, fontfamily="serif", fontweight="bold",
            color=text_color, zorder=4)
    ax.text(x, y - 0.42, sublabels[name], ha="center", va="center",
            fontsize=7, fontfamily="serif", color=text_color,
            alpha=0.85, zorder=4)

draw_node("X",  blue,     white)
draw_node("M1", lightgray, "black")
draw_node("M2", lightgray, "black")
draw_node("Y",  green,    white)
draw_node("Z",  white,    "black", dashed=True)

# ── edges ──
def arrow(start, end, color="black", lw=1.8, style="-", label="", label_offset=(0, 0.18),
          connectionstyle="arc3,rad=0"):
    sx, sy = nodes[start]
    ex, ey = nodes[end]
    # adjust start/end to box edges
    dx = ex - sx
    dy = ey - sy
    dist = (dx**2 + dy**2) ** 0.5
    ux, uy = dx / dist, dy / dist
    sx2 = sx + ux * (box_w / 2 + 0.08)
    sy2 = sy + uy * (box_h / 2 + 0.08)
    ex2 = ex - ux * (box_w / 2 + 0.08)
    ey2 = ey - uy * (box_h / 2 + 0.08)
    ax.annotate(
        "", xy=(ex2, ey2), xytext=(sx2, sy2),
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw,
            linestyle=style, connectionstyle=connectionstyle,
            shrinkA=0, shrinkB=0,
        ),
        zorder=2,
    )
    if label:
        mx = (sx2 + ex2) / 2 + label_offset[0]
        my = (sy2 + ey2) / 2 + label_offset[1]
        ax.text(mx, my, label, fontsize=8, fontfamily="serif",
                ha="center", va="center", color=color,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9),
                zorder=5)

# Causal paths
arrow("X", "M1", color="black", lw=2.0, label="game disclosure\nactivates", label_offset=(0, 0.2))
arrow("X", "M2", color="black", lw=2.0, label="opponent claims\nactivate", label_offset=(0, -0.2))
arrow("M1", "Y", color="#DC2626", lw=2.0, label="$-$ reduces\ndeals", label_offset=(0, 0.2))
arrow("M2", "Y", color="#16A34A", lw=2.0, label="$+$ increases\ndeals", label_offset=(0, -0.2))

# Direct effect (dashed)
arrow("X", "Y", color="black", lw=1.2, style="--", label="direct effect",
      label_offset=(0, 0.0))

# Control path
arrow("Z", "Y", color=gray, lw=1.0, label="", label_offset=(0, 0))

# ── title ──
ax.text(5.25, 5.3,
        "Does the source of partial information (game-disclosed vs. opponent-claimed)\n"
        "have opposite effects on bargaining deal rates?",
        ha="center", va="center", fontsize=11, fontfamily="serif",
        fontstyle="italic", color="#1F2937")

# ── legend ──
legend_elements = [
    mpatches.Patch(facecolor=blue, edgecolor="black", label="Treatment"),
    mpatches.Patch(facecolor=lightgray, edgecolor="black", label="Mediator"),
    mpatches.Patch(facecolor=green, edgecolor="black", label="Outcome"),
    mpatches.Patch(facecolor=white, edgecolor="black", linestyle="--", label="Control"),
    plt.Line2D([0], [0], color="black", lw=1.8, label="Causal path"),
    plt.Line2D([0], [0], color="black", lw=1.2, linestyle="--", label="Direct effect"),
    plt.Line2D([0], [0], color=gray, lw=1.0, label="Control path"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8,
          frameon=True, fancybox=True, framealpha=0.9, edgecolor="#D1D5DB")

plt.tight_layout()
fig.savefig("/Users/benjaminmanning/interview/writeup/plots/dag_info_source_bargaining.pdf",
            bbox_inches="tight", dpi=300)
print("DAG saved.")
