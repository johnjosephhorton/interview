"""Generate causal DAG figure for information-structure bargaining hypothesis."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(10, 5))
ax.set_xlim(-0.5, 10.5)
ax.set_ylim(-1.5, 5.5)
ax.axis('off')
fig.patch.set_facecolor('white')

# --- Node positions ---
nodes = {
    'X': (1.0, 3.0),   # Treatment: Information Structure
    'M': (5.0, 4.2),   # Mediator: Offer Anchoring
    'Y': (9.0, 3.0),   # Outcome: Deal Rate
    'Z': (5.0, 0.8),   # Control: ZOPA Size
}

# --- Node styles ---
styles = {
    'X': dict(boxstyle='round,pad=0.4', facecolor='#2563EB', edgecolor='#1e40af', linewidth=2),
    'M': dict(boxstyle='round,pad=0.4', facecolor='#6B7280', edgecolor='#4B5563', linewidth=1.5),
    'Y': dict(boxstyle='round,pad=0.4', facecolor='#059669', edgecolor='#047857', linewidth=2),
    'Z': dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#9CA3AF', linewidth=1.5, linestyle='dashed'),
}

labels = {
    'X': 'Information\nStructure (X)',
    'M': 'Offer Anchoring\nBehavior (M)',
    'Y': 'Deal Rate (Y)',
    'Z': 'ZOPA Size,\nAI Strategy (Z)',
}

label_colors = {
    'X': 'white',
    'M': 'white',
    'Y': 'white',
    'Z': '#374151',
}

font_weights = {
    'X': 'bold',
    'M': 'normal',
    'Y': 'bold',
    'Z': 'normal',
}

# --- Draw nodes ---
for key, (x, y) in nodes.items():
    s = styles[key]
    ls = s.pop('linestyle', 'solid')
    bbox = FancyBboxPatch((x - 1.3, y - 0.55), 2.6, 1.1, **s, linestyle=ls)
    ax.add_patch(bbox)
    ax.text(x, y, labels[key], ha='center', va='center',
            fontsize=11, fontfamily='serif', color=label_colors[key],
            fontweight=font_weights[key])

# --- Draw edges ---
arrow_kw = dict(arrowstyle='->', mutation_scale=18, shrinkA=0, shrinkB=0)

# X -> M (causal, solid)
ax.annotate('', xy=(3.7, 4.0), xytext=(2.3, 3.4),
            arrowprops=dict(**arrow_kw, connectionstyle='arc3,rad=0.1',
                          color='black', linewidth=1.8))

# M -> Y (causal, solid)
ax.annotate('', xy=(7.7, 3.5), xytext=(6.3, 4.0),
            arrowprops=dict(**arrow_kw, connectionstyle='arc3,rad=0.1',
                          color='black', linewidth=1.8))

# X -> Y (direct effect, dashed)
ax.annotate('', xy=(7.7, 3.0), xytext=(2.3, 3.0),
            arrowprops=dict(**arrow_kw, connectionstyle='arc3,rad=0.0',
                          color='black', linewidth=1.2, linestyle='dashed'))
ax.text(5.0, 2.65, 'direct effect', ha='center', va='top',
        fontsize=8.5, fontfamily='serif', fontstyle='italic', color='#666666')

# Z -> Y (control, thin gray)
ax.annotate('', xy=(7.7, 2.5), xytext=(6.3, 1.1),
            arrowprops=dict(**arrow_kw, connectionstyle='arc3,rad=-0.1',
                          color='#9CA3AF', linewidth=1.0))

# --- Title ---
ax.text(5.0, 5.3,
        'Does revealing the opponent\'s reservation price reduce deal rates\nin bilateral bargaining?',
        ha='center', va='center', fontsize=12, fontfamily='serif',
        fontstyle='italic', color='#374151')

# --- Legend ---
legend_x, legend_y = 8.2, -0.8
legend_items = [
    ('Treatment', '#2563EB', 'white', 'solid', 'bold'),
    ('Mediator', '#6B7280', 'white', 'solid', 'normal'),
    ('Outcome', '#059669', 'white', 'solid', 'bold'),
    ('Control', 'white', '#374151', 'dashed', 'normal'),
]
for i, (lbl, fc, tc, ls, fw) in enumerate(legend_items):
    bx = legend_x
    by = legend_y - i * 0.45
    rect = FancyBboxPatch((bx - 0.3, by - 0.15), 0.6, 0.3,
                          boxstyle='round,pad=0.05', facecolor=fc,
                          edgecolor='#9CA3AF', linewidth=1, linestyle=ls)
    ax.add_patch(rect)
    ax.text(bx + 0.55, by, lbl, ha='left', va='center',
            fontsize=8.5, fontfamily='serif', color='#374151')

# Edge legend
ax.annotate('', xy=(legend_x + 0.3, legend_y - 1.95), xytext=(legend_x - 0.3, legend_y - 1.95),
            arrowprops=dict(**arrow_kw, color='black', linewidth=1.5))
ax.text(legend_x + 0.55, legend_y - 1.95, 'Causal path', ha='left', va='center',
        fontsize=8.5, fontfamily='serif', color='#374151')

ax.annotate('', xy=(legend_x + 0.3, legend_y - 2.4), xytext=(legend_x - 0.3, legend_y - 2.4),
            arrowprops=dict(**arrow_kw, color='black', linewidth=1.2, linestyle='dashed'))
ax.text(legend_x + 0.55, legend_y - 2.4, 'Direct effect', ha='left', va='center',
        fontsize=8.5, fontfamily='serif', color='#374151')

plt.tight_layout()
fig.savefig('/Users/benjaminmanning/interview/writeup/plots/dag_info_bargaining.pdf',
            bbox_inches='tight', dpi=300, facecolor='white')
print('DAG saved to writeup/plots/dag_info_bargaining.pdf')
