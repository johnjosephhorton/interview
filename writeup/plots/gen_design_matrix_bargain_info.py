"""Generate design matrix comparison table for bargaining info experiment."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 5))
ax.axis("off")
fig.patch.set_facecolor("white")

# Data
row_labels = [
    "Information\nstructure",
    "Human knows\nabout AI",
    "AI knows\nabout human",
    "Payoff\nformulas",
    "Rounds",
    "AI strategy",
    "Turn\nstructure",
]

col_labels = ["Full Info\n(Control)", "One-Sided\n(Treatment 1)", "Two-Sided\n(Treatment 2)"]

cells = [
    ["Both valuations\npublic", "AI valuation\nprivate", "Both valuations\nprivate"],
    ["AI value = $6.00\n(exact)", "AI value ∈ [$4, $8]\n(range only)", "AI value ∈ [$4, $8]\n(range only)"],
    ["Human value = $8.00\n(exact)", "Human value = $8.00\n(exact, public)", "Human value ∈ [$6, $10]\n(range only)"],
    ["Deal: H=$8−P, AI=P−$6\nNo deal: both $0", "Deal: H=$8−P, AI=P−$6\nNo deal: both $0", "Deal: H=$8−P, AI=P−$6\nNo deal: both $0"],
    ["6", "6", "6"],
    ["Concession Ladder\n(identical)", "Concession Ladder\n(identical)", "Concession Ladder\n(identical)"],
    ["Alternating\n(AI first)", "Alternating\n(AI first)", "Alternating\n(AI first)"],
]

# Which cells differ across conditions (row indices)
differs = {0, 1, 2}  # info structure, human knows, AI knows

nrows = len(row_labels)
ncols = len(col_labels)

# Table dimensions
cell_w = 2.6
cell_h = 0.65
row_label_w = 1.6
header_h = 0.55
x0 = 0.5
y0 = 0.2

# Draw header
for j, label in enumerate(col_labels):
    x = x0 + row_label_w + j * cell_w
    y = y0 + nrows * cell_h
    rect = plt.Rectangle((x, y), cell_w, header_h, facecolor="#4A90D9",
                          edgecolor="#2C5F8A", linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x + cell_w / 2, y + header_h / 2, label, ha="center", va="center",
            fontsize=9, fontfamily="serif", fontweight="bold", color="white")

# Draw row labels
for i, label in enumerate(row_labels):
    x = x0
    y = y0 + (nrows - 1 - i) * cell_h
    rect = plt.Rectangle((x, y), row_label_w, cell_h, facecolor="#F5F5F5",
                          edgecolor="#CCCCCC", linewidth=0.8)
    ax.add_patch(rect)
    ax.text(x + row_label_w / 2, y + cell_h / 2, label, ha="center", va="center",
            fontsize=8.5, fontfamily="serif", fontweight="bold", color="#333333")

# Draw cells
for i in range(nrows):
    for j in range(ncols):
        x = x0 + row_label_w + j * cell_w
        y = y0 + (nrows - 1 - i) * cell_h
        if i in differs:
            fc = "#FFF3CD" if j > 0 else "#FFFFFF"
            ec = "#D4A843" if j > 0 else "#CCCCCC"
        else:
            fc = "#FFFFFF"
            ec = "#CCCCCC"
        rect = plt.Rectangle((x, y), cell_w, cell_h, facecolor=fc,
                              edgecolor=ec, linewidth=0.8)
        ax.add_patch(rect)
        ax.text(x + cell_w / 2, y + cell_h / 2, cells[i][j], ha="center", va="center",
                fontsize=7.5, fontfamily="serif", color="#333333")

# Title
ax.text(x0 + (row_label_w + ncols * cell_w) / 2, y0 + nrows * cell_h + header_h + 0.3,
        "Experimental Design Matrix: Information Structure in Bargaining",
        ha="center", va="center", fontsize=12, fontfamily="serif", fontweight="bold",
        color="#222222")

# Legend note
ax.text(x0 + (row_label_w + ncols * cell_w) / 2, y0 - 0.25,
        "Yellow cells = treatment manipulation (differs across conditions)",
        ha="center", va="center", fontsize=8.5, fontfamily="serif",
        fontstyle="italic", color="#888888")

ax.set_xlim(0, x0 + row_label_w + ncols * cell_w + 0.5)
ax.set_ylim(y0 - 0.5, y0 + nrows * cell_h + header_h + 0.7)
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig("/Users/benjaminmanning/interview/writeup/plots/design_matrix_bargain_info.pdf",
            bbox_inches="tight", dpi=300)
print("Saved design_matrix_bargain_info.pdf")
