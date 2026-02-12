#!/usr/bin/env python3
"""Figure 1: Deal price by information condition (box plot + strip)."""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Load data
rows = []
with open('writeup/data/info_precision_bargaining_data.csv') as f:
    for r in csv.DictReader(f):
        r['deal_price'] = float(r['deal_price']) if r['deal_price'] else None
        r['fair_price'] = float(r['fair_price'])
        r['seller_cost'] = float(r['seller_cost'])
        rows.append(r)

conditions = ['none', 'range', 'exact']
labels = ['No Info', 'Range Info', 'Exact Info']
colors = ['#4C72B0', '#DD8452', '#55A868']

fig, ax = plt.subplots(figsize=(7, 5))

# Collect prices per condition
price_data = []
for info in conditions:
    prices = [r['deal_price'] for r in rows if r['info_precision'] == info and r['deal_price'] is not None]
    price_data.append(prices)

# Box plot
bp = ax.boxplot(price_data, positions=[1, 2, 3], widths=0.5, patch_artist=True,
                showmeans=True, meanprops=dict(marker='D', markerfacecolor='white', markeredgecolor='black', markersize=7))

for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

# Strip plot (jittered points)
np.random.seed(42)
for i, (prices, color) in enumerate(zip(price_data, colors)):
    jitter = np.random.normal(0, 0.08, len(prices))
    ax.scatter([i + 1 + j for j in jitter], prices, color=color, alpha=0.7, s=40, zorder=5, edgecolors='white', linewidth=0.5)

# Reference lines
ax.axhline(y=40, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
ax.text(3.6, 40, 'Seller cost ($40)', fontsize=8, color='gray', va='center')

ax.set_xticks([1, 2, 3])
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel('Deal Price ($)', fontsize=12)
ax.set_title('Deal Price by Information Condition', fontsize=13, fontweight='bold')
ax.set_ylim(35, 70)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('writeup/plots/results_info_precision_price_by_condition.pdf', bbox_inches='tight')
print("Saved: writeup/plots/results_info_precision_price_by_condition.pdf")
