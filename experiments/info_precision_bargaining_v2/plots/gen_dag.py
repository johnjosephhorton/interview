#!/usr/bin/env python3
"""Causal DAG for info_precision_bargaining v2 hypothesis."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(11, 5.5))
ax.set_xlim(-0.5, 10.5)
ax.set_ylim(-1.5, 4.5)
ax.axis('off')

# Title
ax.text(5.25, 4.2,
        'Does range information reduce deal rates under tight bargaining\nby creating uncertainty about deal feasibility?',
        fontsize=11, fontfamily='serif', ha='center', va='center', style='italic')

def draw_node(ax, x, y, text, color, textcolor='white', style='round', width=2.2, height=0.7):
    if style == 'dashed':
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                             boxstyle="round,pad=0.15", facecolor='white',
                             edgecolor='#555555', linewidth=1.5, linestyle='--')
    else:
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                             boxstyle="round,pad=0.15", facecolor=color,
                             edgecolor='#333333', linewidth=1.5)
    ax.add_patch(box)
    ax.text(x, y, text, fontsize=10, fontfamily='serif', fontweight='bold',
            ha='center', va='center', color=textcolor)

# Nodes
draw_node(ax, 1.0, 2.5, 'Info Precision\n(X)', '#2166AC')                    # Treatment
draw_node(ax, 4.5, 3.5, 'Feasibility\nUncertainty (M1)', '#888888', 'white') # Mediator 1
draw_node(ax, 4.5, 1.5, 'Opening Offer\nAggressiveness (M2)', '#888888', 'white') # Mediator 2
draw_node(ax, 8.0, 2.5, 'Deal Rate &\nDeal Price (Y)', '#2CA02C')            # Outcome
draw_node(ax, 1.0, 0.0, 'ZOPA Size\n(Z)', 'white', '#333333', 'dashed')      # Control
draw_node(ax, 8.0, 0.0, 'Rounds\nAvailable', 'white', '#333333', 'dashed', width=1.8) # Control 2

def draw_arrow(ax, x1, y1, x2, y2, style='->', color='black', lw=1.5, ls='-'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, linestyle=ls,
                                connectionstyle='arc3,rad=0.0'))

# Causal paths (solid)
draw_arrow(ax, 2.1, 2.8, 3.35, 3.3)     # X → M1
draw_arrow(ax, 2.1, 2.2, 3.35, 1.7)     # X → M2
draw_arrow(ax, 5.6, 3.2, 6.85, 2.8)     # M1 → Y
draw_arrow(ax, 5.6, 1.8, 6.85, 2.2)     # M2 → Y

# Direct effect (dashed)
draw_arrow(ax, 2.1, 2.5, 6.85, 2.5, color='#333333', ls='--') # X → Y direct

# Control paths (thin gray)
draw_arrow(ax, 2.1, 0.0, 6.9, 2.2, color='gray', lw=1.0)     # Z → Y
draw_arrow(ax, 8.0, 0.35, 8.0, 2.1, color='gray', lw=1.0)     # Rounds → Y

# Interaction arrow (Z moderates X→M1)
ax.annotate('', xy=(2.7, 2.0), xytext=(1.5, 0.35),
            arrowprops=dict(arrowstyle='->', color='#CC4400', lw=1.2, linestyle=':',
                            connectionstyle='arc3,rad=-0.2'))
ax.text(1.4, 1.2, 'moderates', fontsize=8, fontfamily='serif', color='#CC4400',
        ha='center', rotation=55)

# Legend
legend_items = [
    mpatches.Patch(facecolor='#2166AC', edgecolor='#333', label='Treatment (X)'),
    mpatches.Patch(facecolor='#888888', edgecolor='#333', label='Mediator (M)'),
    mpatches.Patch(facecolor='#2CA02C', edgecolor='#333', label='Outcome (Y)'),
    mpatches.Patch(facecolor='white', edgecolor='#555', linestyle='--', label='Control (Z)'),
]
ax.legend(handles=legend_items, loc='lower right', fontsize=8, framealpha=0.9,
          edgecolor='#cccccc')

# Path labels
ax.text(2.8, 3.4, 'range spans\ninfeasible values', fontsize=7.5, fontfamily='serif',
        ha='center', color='#555', style='italic')
ax.text(2.8, 1.6, 'anchoring on\nrange extremes', fontsize=7.5, fontfamily='serif',
        ha='center', color='#555', style='italic')
ax.text(4.5, 2.5, 'focal point\n(direct)', fontsize=7.5, fontfamily='serif',
        ha='center', color='#555', style='italic')

plt.tight_layout()
plt.savefig('writeup/plots/dag_info_precision_bargaining_v2.pdf', bbox_inches='tight')
print("Saved: writeup/plots/dag_info_precision_bargaining_v2.pdf")
