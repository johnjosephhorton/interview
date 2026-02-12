#!/usr/bin/env python3
"""Design matrix figure for info_precision_bargaining v2."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(9, 6))
ax.axis('off')

# Table data
rows = [
    'Buyer info\nabout seller',
    'Seller info\nabout buyer',
    'Seller cost',
    'Buyer value',
    'ZOPA',
    'Max rounds',
    'AI goal',
    'Valid prices',
]

cols = ['No Info', 'Range Info', 'Exact Info']

data = [
    ['Nothing', 'Cost is $35–$50', 'Cost is exactly $40'],
    ['Nothing', 'Value is $38–$55', 'Value is exactly $X'],
    ['$40 (fixed)', '$40 (fixed)', '$40 (fixed)'],
    ['$42 or $45', '$42 or $45', '$42 or $45'],
    ['$2 or $5', '$2 or $5', '$2 or $5'],
    ['3', '3', '3'],
    ['Max earnings', 'Max earnings', 'Max earnings'],
    ['$0–$100', '$0–$100', '$0–$100'],
]

# Which cells differ (row indices where treatment varies)
diff_rows = {0, 1}  # info about seller, info about buyer

n_rows = len(rows)
n_cols = len(cols)
cell_w = 2.2
cell_h = 0.6
row_label_w = 2.0
x0 = 0.5
y0 = 0.5

# Draw header
for j, col in enumerate(cols):
    x = x0 + row_label_w + j * cell_w
    rect = plt.Rectangle((x, y0 + n_rows * cell_h), cell_w, cell_h,
                          facecolor='#2166AC', edgecolor='white', linewidth=1)
    ax.add_patch(rect)
    ax.text(x + cell_w/2, y0 + n_rows * cell_h + cell_h/2, col,
            ha='center', va='center', fontsize=10, fontweight='bold', color='white', fontfamily='serif')

# Draw rows
for i, (row_label, row_data) in enumerate(zip(reversed(rows), reversed(data))):
    y = y0 + i * cell_h
    # Row label
    ax.text(x0 + row_label_w - 0.1, y + cell_h/2, row_label,
            ha='right', va='center', fontsize=9, fontfamily='serif')

    row_idx = n_rows - 1 - i
    for j, val in enumerate(row_data):
        x = x0 + row_label_w + j * cell_w
        color = '#FFF3CD' if row_idx in diff_rows else 'white'
        rect = plt.Rectangle((x, y), cell_w, cell_h,
                              facecolor=color, edgecolor='#cccccc', linewidth=0.5)
        ax.add_patch(rect)
        ax.text(x + cell_w/2, y + cell_h/2, val,
                ha='center', va='center', fontsize=8.5, fontfamily='serif')

ax.set_xlim(-0.2, x0 + row_label_w + n_cols * cell_w + 0.3)
ax.set_ylim(y0 - 0.3, y0 + (n_rows + 1) * cell_h + 0.3)
ax.set_aspect('equal')

# Legend
ax.text(x0 + row_label_w, y0 - 0.2,
        'Yellow = treatment manipulation (differs across conditions)',
        fontsize=8, fontfamily='serif', color='#666666')

plt.tight_layout()
plt.savefig('writeup/plots/design_matrix_info_precision_v2.pdf', bbox_inches='tight')
print("Saved: writeup/plots/design_matrix_info_precision_v2.pdf")
