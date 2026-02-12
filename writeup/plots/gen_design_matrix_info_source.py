"""Design matrix figure: 3 conditions side by side, yellow = differs, white = constant."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(12, 7))
ax.axis("off")
fig.patch.set_facecolor("white")

# ── data ──
conditions = ["Condition A:\nNo Information\n(Baseline)", "Condition B:\nGame-Disclosed\n(Verified)", "Condition C:\nOpponent-Claimed\n(Unverified)"]
rows = [
    "Info about opponent's cost",
    "Source of information",
    "Pre-offer chat phase",
    "Chat content",
    "Buyer's valuation",
    "Seller's cost",
    "ZOPA size",
    "Rounds",
    "Turn structure",
    "AI strategy",
    "Payoff formula",
]

cells = [
    # row: [condA, condB, condC]
    ["None", "\"Seller's cost is\\napprox. $45–$55\"", "\"Seller's cost is\\napprox. $45–$55\""],
    ["N/A", "Game rules\\n(verified, certain)", "AI opponent's claim\\n(unverified, uncertain)"],
    ["No", "No", "Yes (1 message\\nfrom AI, then offers)"],
    ["N/A", "N/A", "AI voluntarily\\nshares cost range"],
    ["$80 (known)", "$80 (known)", "$80 (known)"],
    ["$50 (hidden)", "$50 (hidden)", "$50 (hidden)"],
    ["$30", "$30", "$30"],
    ["6 (3 per player)", "6 (3 per player)", "6 (3 per player)"],
    ["Alternating\\n(AI odd, Human even)", "Alternating\\n(AI odd, Human even)", "Alternating\\n(AI odd, Human even)"],
    ["Anchored concession\\n(identical)", "Anchored concession\\n(identical)", "Anchored concession\\n(identical)"],
    ["Deal@P: Buyer=$80-P\\nSeller=P-$50; else $0", "Deal@P: Buyer=$80-P\\nSeller=P-$50; else $0", "Deal@P: Buyer=$80-P\\nSeller=P-$50; else $0"],
]

# Which cells differ (row_idx, col_idx) — yellow highlight
differs = {
    (0, 0), (0, 1), (0, 2),  # info about opponent
    (1, 0), (1, 1), (1, 2),  # source
    (2, 0), (2, 1), (2, 2),  # chat phase
    (3, 0), (3, 1), (3, 2),  # chat content
}

n_rows = len(rows)
n_cols = len(conditions)
col_w = 2.8
row_h = 0.55
label_w = 2.5
x0 = 0.5
y0 = 0.5

# ── header ──
header_color = "#2563EB"
for j, cond in enumerate(conditions):
    x = x0 + label_w + j * col_w
    rect = plt.Rectangle((x, y0 + n_rows * row_h), col_w, row_h * 1.3,
                          facecolor=header_color, edgecolor="white", lw=1)
    ax.add_patch(rect)
    ax.text(x + col_w / 2, y0 + n_rows * row_h + row_h * 0.65, cond,
            ha="center", va="center", fontsize=8.5, fontfamily="serif",
            fontweight="bold", color="white")

# ── row label header ──
rect = plt.Rectangle((x0, y0 + n_rows * row_h), label_w, row_h * 1.3,
                      facecolor="#1F2937", edgecolor="white", lw=1)
ax.add_patch(rect)
ax.text(x0 + label_w / 2, y0 + n_rows * row_h + row_h * 0.65, "Design\nElement",
        ha="center", va="center", fontsize=9, fontfamily="serif",
        fontweight="bold", color="white")

# ── body cells ──
yellow = "#FEF3C7"
white = "#FFFFFF"
light_yellow = "#FDE68A"

for i in range(n_rows):
    y = y0 + (n_rows - 1 - i) * row_h

    # row label
    rect = plt.Rectangle((x0, y), label_w, row_h,
                          facecolor="#F9FAFB", edgecolor="#D1D5DB", lw=0.5)
    ax.add_patch(rect)
    ax.text(x0 + label_w / 2, y + row_h / 2, rows[i],
            ha="center", va="center", fontsize=8, fontfamily="serif",
            fontweight="bold", color="#1F2937")

    for j in range(n_cols):
        x = x0 + label_w + j * col_w
        bg = light_yellow if (i, j) in differs else white
        rect = plt.Rectangle((x, y), col_w, row_h,
                              facecolor=bg, edgecolor="#D1D5DB", lw=0.5)
        ax.add_patch(rect)
        text = cells[i][j].replace("\\n", "\n")
        ax.text(x + col_w / 2, y + row_h / 2, text,
                ha="center", va="center", fontsize=7, fontfamily="serif",
                color="#1F2937")

# ── legend ──
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=light_yellow, edgecolor="#D1D5DB", label="Varies across conditions (treatment)"),
    Patch(facecolor=white, edgecolor="#D1D5DB", label="Held constant (control)"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8,
          frameon=True, fancybox=True, framealpha=0.9, edgecolor="#D1D5DB",
          bbox_to_anchor=(0.95, -0.02))

# ── title ──
total_w = label_w + n_cols * col_w
ax.text(x0 + total_w / 2, y0 + n_rows * row_h + row_h * 2.0,
        "Experimental Design: Information Source in Bilateral Bargaining",
        ha="center", va="center", fontsize=12, fontfamily="serif",
        fontweight="bold", color="#1F2937")

ax.set_xlim(0, x0 + total_w + 0.5)
ax.set_ylim(-0.3, y0 + n_rows * row_h + row_h * 2.5)
ax.set_aspect("equal")

plt.tight_layout()
fig.savefig("/Users/benjaminmanning/interview/writeup/plots/design_matrix_info_source.pdf",
            bbox_inches="tight", dpi=300)
print("Design matrix saved.")
