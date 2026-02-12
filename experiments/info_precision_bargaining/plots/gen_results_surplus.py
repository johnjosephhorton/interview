#!/usr/bin/env python3
"""Figure 2: Surplus split by condition × ZOPA size."""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

rows = []
with open('writeup/data/info_precision_bargaining_data.csv') as f:
    for r in csv.DictReader(f):
        r['human_earnings'] = float(r['human_earnings']) if r['human_earnings'] else 0
        r['ai_earnings'] = float(r['ai_earnings']) if r['ai_earnings'] else 0
        r['is_deal'] = int(r['is_deal'])
        rows.append(r)

conditions = ['none', 'range', 'exact']
labels = ['No Info', 'Range Info', 'Exact Info']
zopas = ['tight', 'wide']
zopa_labels = ['Tight ZOPA ($10)', 'Wide ZOPA ($25)']

fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)

for ax, zk, zlabel in zip(axes, zopas, zopa_labels):
    human_means = []
    ai_means = []
    for info in conditions:
        subset = [r for r in rows if r['info_precision'] == info and r['zopa_label'] == zk and r['is_deal']]
        h_earn = [r['human_earnings'] for r in subset]
        a_earn = [r['ai_earnings'] for r in subset]
        human_means.append(np.mean(h_earn) if h_earn else 0)
        ai_means.append(np.mean(a_earn) if a_earn else 0)

    x = np.arange(len(conditions))
    width = 0.35

    bars1 = ax.bar(x - width/2, human_means, width, label='Buyer (Human)', color='#4C72B0', alpha=0.8)
    bars2 = ax.bar(x + width/2, ai_means, width, label='Seller (AI)', color='#DD8452', alpha=0.8)

    # Add value labels
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.3, f'${h:.1f}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.3, f'${h:.1f}', ha='center', va='bottom', fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title(zlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Earnings ($)' if zk == 'tight' else '')
    ax.set_ylim(0, 22)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=9, loc='upper right')

fig.suptitle('Surplus Split by Information Condition and ZOPA Size', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('writeup/plots/results_info_precision_surplus_split.pdf', bbox_inches='tight')
print("Saved: writeup/plots/results_info_precision_surplus_split.pdf")
