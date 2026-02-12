"""Prediction space figure for the Information Precision Valley experiment."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=False)
fig.patch.set_facecolor('white')

conditions = ['No Info', 'Range\nInfo', 'Exact\nInfo']
x_pos = np.array([0, 1, 2])
bar_width = 0.5

colors_tight = '#DC2626'
colors_wide = '#2563EB'

# --- Panel 1: Deal Rate (the valley) ---
ax = axes[0]

# Predicted deal rates (conceptual, not fake data)
# Tight ZOPA: valley is deep
tight_centers = [0.65, 0.35, 0.80]
tight_lo = [0.50, 0.20, 0.65]
tight_hi = [0.80, 0.50, 0.90]

# Wide ZOPA: valley is shallow (ceiling effect)
wide_centers = [0.85, 0.75, 0.95]
wide_lo = [0.75, 0.60, 0.85]
wide_hi = [0.95, 0.85, 0.99]

offset = 0.15
for i in range(3):
    # Tight ZOPA bars
    ax.bar(x_pos[i] - offset, tight_centers[i], bar_width * 0.7,
           color=colors_tight, alpha=0.25, edgecolor=colors_tight, linewidth=1.5)
    ax.plot([x_pos[i] - offset, x_pos[i] - offset],
            [tight_lo[i], tight_hi[i]], color=colors_tight, linewidth=2.5, zorder=3)
    ax.plot(x_pos[i] - offset, tight_centers[i], 'o', color=colors_tight,
            markersize=8, zorder=4)

    # Wide ZOPA bars
    ax.bar(x_pos[i] + offset, wide_centers[i], bar_width * 0.7,
           color=colors_wide, alpha=0.25, edgecolor=colors_wide, linewidth=1.5)
    ax.plot([x_pos[i] + offset, x_pos[i] + offset],
            [wide_lo[i], wide_hi[i]], color=colors_wide, linewidth=2.5, zorder=3)
    ax.plot(x_pos[i] + offset, wide_centers[i], 'o', color=colors_wide,
            markersize=8, zorder=4)

# Valley annotation
ax.annotate('', xy=(1 - offset, 0.32), xytext=(0.5, 0.55),
            arrowprops=dict(arrowstyle='->', color=colors_tight, lw=1.5, ls='--'))
ax.text(0.15, 0.53, 'The\n"valley"', fontsize=8.5, fontfamily='serif',
        color=colors_tight, fontstyle='italic', ha='center')

ax.axhline(y=0.5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
ax.text(2.4, 0.505, 'null', fontsize=7, color='gray', fontfamily='serif', fontstyle='italic')

ax.set_xticks(x_pos)
ax.set_xticklabels(conditions, fontfamily='serif', fontsize=10)
ax.set_ylabel('Deal Rate', fontfamily='serif', fontsize=11)
ax.set_title('Primary: Deal Rate by Condition', fontfamily='serif', fontsize=11, fontweight='bold')
ax.set_ylim(0, 1.05)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# --- Panel 2: Opening Offer Aggressiveness ---
ax = axes[1]

# Aggressiveness = |opening offer - fair_price| / ZOPA
# Higher = more aggressive anchoring
tight_agg = [0.30, 0.55, 0.20]
tight_agg_lo = [0.15, 0.40, 0.10]
tight_agg_hi = [0.45, 0.70, 0.35]

wide_agg = [0.25, 0.45, 0.15]
wide_agg_lo = [0.10, 0.30, 0.05]
wide_agg_hi = [0.40, 0.60, 0.30]

for i in range(3):
    ax.bar(x_pos[i] - offset, tight_agg[i], bar_width * 0.7,
           color=colors_tight, alpha=0.25, edgecolor=colors_tight, linewidth=1.5)
    ax.plot([x_pos[i] - offset, x_pos[i] - offset],
            [tight_agg_lo[i], tight_agg_hi[i]], color=colors_tight, linewidth=2.5, zorder=3)
    ax.plot(x_pos[i] - offset, tight_agg[i], 'o', color=colors_tight,
            markersize=8, zorder=4)

    ax.bar(x_pos[i] + offset, wide_agg[i], bar_width * 0.7,
           color=colors_wide, alpha=0.25, edgecolor=colors_wide, linewidth=1.5)
    ax.plot([x_pos[i] + offset, x_pos[i] + offset],
            [wide_agg_lo[i], wide_agg_hi[i]], color=colors_wide, linewidth=2.5, zorder=3)
    ax.plot(x_pos[i] + offset, wide_agg[i], 'o', color=colors_wide,
            markersize=8, zorder=4)

# Aspiration inflation annotation
ax.annotate('', xy=(1 + offset, 0.48), xytext=(0.6, 0.38),
            arrowprops=dict(arrowstyle='->', color='#6B7280', lw=1.5, ls='--'))
ax.text(0.2, 0.37, 'Aspiration\ninflation', fontsize=8.5, fontfamily='serif',
        color='#6B7280', fontstyle='italic', ha='center')

ax.set_xticks(x_pos)
ax.set_xticklabels(conditions, fontfamily='serif', fontsize=10)
ax.set_ylabel('Opening Offer Distance from Fair Price\n(fraction of ZOPA)',
              fontfamily='serif', fontsize=9.5)
ax.set_title('Mechanism: Aspiration Inflation', fontfamily='serif', fontsize=11, fontweight='bold')
ax.set_ylim(0, 0.85)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Shared legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color=colors_tight, markerfacecolor=colors_tight,
           markersize=8, label='Tight ZOPA ($10)', linewidth=0),
    Line2D([0], [0], marker='o', color=colors_wide, markerfacecolor=colors_wide,
           markersize=8, label='Wide ZOPA ($25)', linewidth=0),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=2, fontsize=10,
           framealpha=0.9, edgecolor='#D1D5DB', prop={'family': 'serif'},
           bbox_to_anchor=(0.5, -0.02))

fig.suptitle('Predicted Outcomes (Pre-Data Conceptual — Not Simulated)',
             fontsize=9, fontfamily='serif', fontstyle='italic', color='#6B7280',
             y=1.02)

plt.tight_layout()
fig.savefig('/Users/benjaminmanning/interview/writeup/plots/predictions_info_precision.pdf',
            bbox_inches='tight', dpi=300)
print("Predictions figure saved.")
