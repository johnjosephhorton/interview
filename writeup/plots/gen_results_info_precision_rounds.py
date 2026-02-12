#!/usr/bin/env python3
"""Figure 3: Rounds to deal and opening offers by condition."""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

rows = []
with open('writeup/data/info_precision_bargaining_data.csv') as f:
    for r in csv.DictReader(f):
        r['rounds_played'] = int(r['rounds_played'])
        r['ai_opening_offer'] = float(r['ai_opening_offer']) if r['ai_opening_offer'] else None
        r['deal_price'] = float(r['deal_price']) if r['deal_price'] else None
        r['fair_price'] = float(r['fair_price'])
        r['is_deal'] = int(r['is_deal'])
        rows.append(r)

conditions = ['none', 'range', 'exact']
labels = ['No Info', 'Range Info', 'Exact Info']
colors = ['#4C72B0', '#DD8452', '#55A868']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

# Panel A: AI opening offer by condition
opens_data = []
for info in conditions:
    opens = [r['ai_opening_offer'] for r in rows if r['info_precision'] == info and r['ai_opening_offer'] is not None]
    opens_data.append(opens)

bp = ax1.boxplot(opens_data, positions=[1, 2, 3], widths=0.5, patch_artist=True, showmeans=True,
                 meanprops=dict(marker='D', markerfacecolor='white', markeredgecolor='black', markersize=6))
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

np.random.seed(42)
for i, (opens, color) in enumerate(zip(opens_data, colors)):
    jitter = np.random.normal(0, 0.08, len(opens))
    ax1.scatter([i + 1 + j for j in jitter], opens, color=color, alpha=0.7, s=35, zorder=5, edgecolors='white', linewidth=0.5)

ax1.set_xticks([1, 2, 3])
ax1.set_xticklabels(labels, fontsize=10)
ax1.set_ylabel('AI Opening Offer ($)', fontsize=11)
ax1.set_title('(A) AI Opening Offer', fontsize=12, fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Panel B: Rounds to deal (histogram)
for info, label, color in zip(conditions, labels, colors):
    rnds = [r['rounds_played'] for r in rows if r['info_precision'] == info and r['is_deal']]
    # Count rounds
    round_counts = {}
    for rnd in rnds:
        round_counts[rnd] = round_counts.get(rnd, 0) + 1
    all_rounds = sorted(set(rnds))
    counts = [round_counts.get(rnd, 0) for rnd in range(1, 7)]
    ax2.bar([r + (conditions.index(info) - 1) * 0.25 for r in range(1, 7)], counts,
            width=0.25, alpha=0.7, color=color, label=label)

ax2.set_xlabel('Rounds to Deal', fontsize=11)
ax2.set_ylabel('Count', fontsize=11)
ax2.set_title('(B) Rounds to Deal', fontsize=12, fontweight='bold')
ax2.set_xticks(range(1, 7))
ax2.legend(fontsize=9)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('writeup/plots/results_info_precision_dynamics.pdf', bbox_inches='tight')
print("Saved: writeup/plots/results_info_precision_dynamics.pdf")
