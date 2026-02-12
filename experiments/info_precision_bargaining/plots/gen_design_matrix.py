"""Design matrix figure for the Information Precision Valley experiment."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6.5))
ax.axis('off')
fig.patch.set_facecolor('white')

# Design matrix data
rows = [
    'Info about opponent',
    'Buyer told about seller',
    'Seller told about buyer',
    'Rounds',
    'Turn structure',
    'Payoffs',
    'AI goal',
    'Sim human goal',
    'seller_cost',
    'buyer_value (ZOPA)',
]

cols = ['No Info', 'Range Info', 'Exact Info']

cells = [
    # Info about opponent
    ['Nothing', 'Truthful range', 'Exact values'],
    # Buyer told about seller
    ['—', '"Cost is $30–$50"', '"Cost is $40"'],
    # Seller told about buyer
    ['—', '"Value is $45–$75"', '"Value is ${{buyer_value}}"'],
    # Rounds
    ['6', '6', '6'],
    # Turn structure
    ['Alternating (AI first)', 'Alternating (AI first)', 'Alternating (AI first)'],
    # Payoffs
    ['Buyer: value − price\nSeller: price − cost\nNo deal: $0', 'Same', 'Same'],
    # AI goal
    ['Max earnings\n(never < cost)', 'Same', 'Same'],
    # Sim human goal
    ['Max earnings\n(never > value)', 'Same', 'Same'],
    # seller_cost
    ['Fixed $40', 'Fixed $40', 'Fixed $40'],
    # buyer_value
    ['$50 (tight) / $65 (wide)', '$50 (tight) / $65 (wide)', '$50 (tight) / $65 (wide)'],
]

# Which cells differ (row_idx, col_idx) — treatment rows
differs = set()
for col_idx in range(3):
    for row_idx in [0, 1, 2]:  # Info rows differ
        differs.add((row_idx, col_idx))

n_rows = len(rows)
n_cols = len(cols)

cell_h = 0.08
cell_w = 0.25
label_w = 0.18
x_start = 0.05
y_start = 0.92

# Header row
for j, col_name in enumerate(cols):
    x = x_start + label_w + j * cell_w
    rect = mpatches.FancyBboxPatch(
        (x, y_start), cell_w - 0.005, cell_h,
        boxstyle="round,pad=0.003",
        facecolor='#2563EB', edgecolor='#1E40AF', linewidth=1.5,
        transform=ax.transAxes, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x + cell_w/2, y_start + cell_h/2, col_name,
            transform=ax.transAxes, ha='center', va='center',
            fontsize=11, fontweight='bold', color='white', fontfamily='serif')

# Data rows
for i in range(n_rows):
    y = y_start - (i + 1) * cell_h - 0.005 * (i + 1)

    # Row label
    ax.text(x_start + label_w - 0.01, y + cell_h/2, rows[i],
            transform=ax.transAxes, ha='right', va='center',
            fontsize=9, fontfamily='serif', fontweight='bold' if i < 3 else 'normal',
            color='#374151')

    for j in range(n_cols):
        x = x_start + label_w + j * cell_w
        bg = '#FEF3C7' if (i, j) in differs else '#F9FAFB'
        ec = '#D97706' if (i, j) in differs else '#D1D5DB'

        rect = mpatches.FancyBboxPatch(
            (x, y), cell_w - 0.005, cell_h,
            boxstyle="round,pad=0.003",
            facecolor=bg, edgecolor=ec, linewidth=1.0,
            transform=ax.transAxes, zorder=2
        )
        ax.add_patch(rect)

        text = cells[i][j]
        fontsize = 7.5 if '\n' in text else 8.5
        ax.text(x + cell_w/2, y + cell_h/2, text,
                transform=ax.transAxes, ha='center', va='center',
                fontsize=fontsize, fontfamily='serif', color='#1F2937',
                linespacing=1.2)

# Legend
ax.text(x_start + label_w, y - 0.03,
        'Yellow = treatment manipulation (differs across conditions)  |  White = held constant',
        transform=ax.transAxes, fontsize=8, fontfamily='serif', color='#6B7280',
        fontstyle='italic')

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

plt.tight_layout()
fig.savefig('/Users/benjaminmanning/interview/writeup/plots/design_matrix_info_precision.pdf',
            bbox_inches='tight', dpi=300)
print("Design matrix saved.")
