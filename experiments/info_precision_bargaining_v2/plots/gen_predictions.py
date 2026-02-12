#!/usr/bin/env python3
"""Predictions figure for info_precision_bargaining v2."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

conditions = ['No Info', 'Range Info', 'Exact Info']
x = np.arange(len(conditions))
colors = ['#4C72B0', '#DD8452', '#55A868']

# Panel A: Deal Rate predictions (the core hypothesis)
# Predicted: Range < No Info < Exact
# Under tight ZOPA ($2): valley should be deepest
# Under moderate tight ($5): valley present but shallower
tight_means = [65, 35, 80]
tight_low = [45, 15, 60]
tight_high = [85, 55, 95]

mod_means = [80, 55, 90]
mod_low = [65, 35, 75]
mod_high = [95, 75, 100]

width = 0.3
# Tight ZOPA bars
for i in range(3):
    ax1.bar(x[i] - width/2, tight_means[i], width, color=colors[i], alpha=0.6, edgecolor='white')
    ax1.plot([x[i] - width/2, x[i] - width/2], [tight_low[i], tight_high[i]],
             color=colors[i], lw=2, solid_capstyle='round')
    ax1.scatter(x[i] - width/2, tight_means[i], color=colors[i], s=40, zorder=5, edgecolors='white')

# Moderate tight bars
for i in range(3):
    ax1.bar(x[i] + width/2, mod_means[i], width, color=colors[i], alpha=0.3, edgecolor='white')
    ax1.plot([x[i] + width/2, x[i] + width/2], [mod_low[i], mod_high[i]],
             color=colors[i], lw=2, alpha=0.5, solid_capstyle='round')
    ax1.scatter(x[i] + width/2, mod_means[i], color=colors[i], s=40, zorder=5, alpha=0.5, edgecolors='white')

# Null hypothesis line
ax1.axhline(y=100, color='gray', linestyle=':', alpha=0.5, linewidth=1)
ax1.text(2.6, 100, 'v1 ceiling', fontsize=7, color='gray', va='bottom')

ax1.set_xticks(x)
ax1.set_xticklabels(conditions, fontsize=10)
ax1.set_ylabel('Predicted Deal Rate (%)', fontsize=11)
ax1.set_title('(A) Deal Rate: Valley Prediction', fontsize=12, fontweight='bold')
ax1.set_ylim(0, 110)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Legend for ZOPA
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='gray', alpha=0.6, label='ZOPA = $2 (tight)'),
                   Patch(facecolor='gray', alpha=0.3, label='ZOPA = $5 (moderate)')]
ax1.legend(handles=legend_elements, fontsize=8, loc='upper left')

# Arrow showing "valley"
ax1.annotate('', xy=(1, 38), xytext=(1, 62),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
ax1.text(1.15, 50, 'valley', fontsize=9, color='red', fontweight='bold')

# Panel B: Deal Price predictions (secondary)
# Expect same monotonic gradient as v1 but compressed
tight_price = [41.5, 41.0, 41.0]
mod_price = [43.5, 42.0, 42.5]

for i in range(3):
    ax2.bar(x[i] - width/2, tight_price[i] - 39, width, bottom=39, color=colors[i], alpha=0.6, edgecolor='white')
    ax2.bar(x[i] + width/2, mod_price[i] - 39, width, bottom=39, color=colors[i], alpha=0.3, edgecolor='white')

ax2.axhline(y=40, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
ax2.text(2.6, 40, 'seller cost', fontsize=7, color='gray', va='bottom')

ax2.set_xticks(x)
ax2.set_xticklabels(conditions, fontsize=10)
ax2.set_ylabel('Predicted Deal Price ($)', fontsize=11)
ax2.set_title('(B) Deal Price (if deal reached)', fontsize=12, fontweight='bold')
ax2.set_ylim(39, 46)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.legend(handles=legend_elements, fontsize=8, loc='upper right')

fig.suptitle('Pre-Data Predictions: Information Precision Valley (v2)', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('writeup/plots/predictions_info_precision_v2.pdf', bbox_inches='tight')
print("Saved: writeup/plots/predictions_info_precision_v2.pdf")
