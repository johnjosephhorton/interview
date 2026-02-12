"""Generate causal DAG for the Information Precision Valley hypothesis."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(10, 5.5))
ax.set_xlim(-0.5, 10.5)
ax.set_ylim(-1.0, 5.5)
ax.axis('off')
fig.patch.set_facecolor('white')

# --- Node positions ---
nodes = {
    'X':  (1.0, 3.0),   # Info Precision (Treatment)
    'M1': (4.5, 4.2),   # Aspiration Inflation (Mediator 1)
    'M2': (4.5, 1.8),   # Focal Point Availability (Mediator 2)
    'Y':  (8.5, 3.0),   # Deal Rate (Outcome)
    'Z':  (5.5, 0.0),   # ZOPA Size (Moderator)
}

labels = {
    'X':  'Information\nPrecision',
    'M1': 'Aspiration\nInflation',
    'M2': 'Focal Point\nAvailability',
    'Y':  'Deal Rate',
    'Z':  'ZOPA Size',
}

# Node colors by type
colors = {
    'X':  ('#2563EB', 'white'),    # blue, white text (treatment)
    'M1': ('#6B7280', 'white'),    # gray (mediator)
    'M2': ('#6B7280', 'white'),    # gray (mediator)
    'Y':  ('#059669', 'white'),    # green, white text (outcome)
    'Z':  ('white', '#374151'),    # white, dark text (control)
}

box_w, box_h = 1.8, 0.9

for key, (cx, cy) in nodes.items():
    bg, fg = colors[key]
    ls = '--' if key == 'Z' else '-'
    lw = 1.5 if key == 'Z' else 2
    ec = '#9CA3AF' if key == 'Z' else '#1F2937'
    bbox = FancyBboxPatch(
        (cx - box_w/2, cy - box_h/2), box_w, box_h,
        boxstyle="round,pad=0.15",
        facecolor=bg, edgecolor=ec, linewidth=lw, linestyle=ls,
        zorder=3
    )
    ax.add_patch(bbox)
    fontweight = 'bold' if key in ('X', 'Y') else 'normal'
    ax.text(cx, cy, labels[key], ha='center', va='center',
            fontsize=11, fontfamily='serif', color=fg,
            fontweight=fontweight, zorder=4)

# --- Edges ---
arrow_kw = dict(arrowstyle='->', mutation_scale=18, zorder=2)

def draw_arrow(start_key, end_key, style='solid', color='#1F2937', lw=2.0,
               start_offset=(0, 0), end_offset=(0, 0), connectionstyle=None):
    sx, sy = nodes[start_key]
    ex, ey = nodes[end_key]
    sx += start_offset[0]; sy += start_offset[1]
    ex += end_offset[0]; ey += end_offset[1]
    kw = dict(arrow_kw)
    if connectionstyle:
        kw['connectionstyle'] = connectionstyle
    arrow = FancyArrowPatch(
        (sx, sy), (ex, ey),
        linestyle=style, color=color, linewidth=lw, **kw
    )
    ax.add_patch(arrow)

# X → M1 (causal)
draw_arrow('X', 'M1', start_offset=(box_w/2, 0.2), end_offset=(-box_w/2, 0))
# X → M2 (causal)
draw_arrow('X', 'M2', start_offset=(box_w/2, -0.2), end_offset=(-box_w/2, 0))
# M1 → Y (causal, negative label)
draw_arrow('M1', 'Y', start_offset=(box_w/2, 0), end_offset=(-box_w/2, 0.2))
# M2 → Y (causal, positive label)
draw_arrow('M2', 'Y', start_offset=(box_w/2, 0), end_offset=(-box_w/2, -0.2))
# Z → Y (control, thin gray)
draw_arrow('Z', 'Y', color='#9CA3AF', lw=1.2, start_offset=(box_w/2, 0.2),
           end_offset=(-0.3, -box_h/2), connectionstyle='arc3,rad=-0.2')
# Z moderates M1 (thin gray dashed)
draw_arrow('Z', 'M1', style='dashed', color='#9CA3AF', lw=1.2,
           start_offset=(-0.2, box_h/2), end_offset=(0.2, -box_h/2),
           connectionstyle='arc3,rad=0.15')

# Edge labels
ax.text(2.8, 4.05, '(+) range', fontsize=8.5, fontfamily='serif', color='#DC2626',
        fontstyle='italic', ha='center', rotation=14)
ax.text(2.8, 2.05, '(+) exact', fontsize=8.5, fontfamily='serif', color='#059669',
        fontstyle='italic', ha='center', rotation=-14)
ax.text(6.8, 4.0, '(−)', fontsize=9, fontfamily='serif', color='#DC2626',
        fontweight='bold', ha='center')
ax.text(6.8, 2.1, '(+)', fontsize=9, fontfamily='serif', color='#059669',
        fontweight='bold', ha='center')

# Title
ax.text(5.25, 5.3,
        'Does partial information create an "information valley" in bargaining deal rates?',
        ha='center', va='center', fontsize=11.5, fontfamily='serif',
        fontstyle='italic', color='#374151')

# Legend
legend_items = [
    mpatches.Patch(facecolor='#2563EB', edgecolor='#1F2937', label='Treatment'),
    mpatches.Patch(facecolor='#6B7280', edgecolor='#1F2937', label='Mediator'),
    mpatches.Patch(facecolor='#059669', edgecolor='#1F2937', label='Outcome'),
    mpatches.Patch(facecolor='white', edgecolor='#9CA3AF', linestyle='--', label='Moderator'),
]
ax.legend(handles=legend_items, loc='lower right', fontsize=9,
          framealpha=0.9, edgecolor='#D1D5DB', prop={'family': 'serif'})

plt.tight_layout()
fig.savefig('/Users/benjaminmanning/interview/writeup/plots/dag_info_precision_bargaining.pdf',
            bbox_inches='tight', dpi=300)
print("DAG saved to writeup/plots/dag_info_precision_bargaining.pdf")
