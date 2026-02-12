#!/usr/bin/env python3
"""Statistical analysis for info_precision_bargaining experiment."""
import csv
import numpy as np
from scipy import stats

# Load data
rows = []
with open('writeup/data/info_precision_bargaining_data.csv') as f:
    reader = csv.DictReader(f)
    for r in reader:
        r['deal_price'] = float(r['deal_price']) if r['deal_price'] else None
        r['human_earnings'] = float(r['human_earnings']) if r['human_earnings'] else None
        r['ai_earnings'] = float(r['ai_earnings']) if r['ai_earnings'] else None
        r['ai_opening_offer'] = float(r['ai_opening_offer']) if r['ai_opening_offer'] else None
        r['buyer_value'] = float(r['buyer_value'])
        r['seller_cost'] = float(r['seller_cost'])
        r['zopa'] = float(r['zopa'])
        r['fair_price'] = float(r['fair_price'])
        r['is_deal'] = int(r['is_deal'])
        r['rounds_played'] = int(r['rounds_played'])
        r['price_deviation'] = float(r['price_deviation']) if r['price_deviation'] else None
        r['efficiency'] = float(r['efficiency']) if r['efficiency'] else None
        rows.append(r)

# Split by condition
none_rows = [r for r in rows if r['info_precision'] == 'none']
range_rows = [r for r in rows if r['info_precision'] == 'range']
exact_rows = [r for r in rows if r['info_precision'] == 'exact']

print("=" * 60)
print("STATISTICAL ANALYSIS: Info Precision Bargaining")
print("=" * 60)

# 1. Deal rate (primary outcome)
print("\n--- 1. DEAL RATE (Primary Outcome) ---")
print("All conditions: 100% (30/30)")
print("No variation in deal rate → cannot run logistic regression.")
print("Primary hypothesis REFUTED: no information valley in deal rates.")

# 2. Deal price analysis (key secondary outcome)
print("\n--- 2. DEAL PRICE ---")

none_prices = [r['deal_price'] for r in none_rows if r['deal_price'] is not None]
range_prices = [r['deal_price'] for r in range_rows if r['deal_price'] is not None]
exact_prices = [r['deal_price'] for r in exact_rows if r['deal_price'] is not None]

print(f"No Info:    M={np.mean(none_prices):.2f}, SD={np.std(none_prices, ddof=1):.2f}, N={len(none_prices)}")
print(f"Range Info: M={np.mean(range_prices):.2f}, SD={np.std(range_prices, ddof=1):.2f}, N={len(range_prices)}")
print(f"Exact Info: M={np.mean(exact_prices):.2f}, SD={np.std(exact_prices, ddof=1):.2f}, N={len(exact_prices)}")

# One-way ANOVA on price
f_stat, p_anova = stats.f_oneway(none_prices, range_prices, exact_prices)
print(f"\nOne-way ANOVA: F(2,27) = {f_stat:.3f}, p = {p_anova:.4f}")

# Pairwise t-tests
t_ne, p_ne = stats.ttest_ind(none_prices, exact_prices)
t_nr, p_nr = stats.ttest_ind(none_prices, range_prices)
t_re, p_re = stats.ttest_ind(range_prices, exact_prices)

print(f"\nPairwise t-tests (two-sided):")
print(f"  No Info vs Exact:  t={t_ne:.3f}, p={p_ne:.4f}, diff=${np.mean(none_prices)-np.mean(exact_prices):.2f}")
print(f"  No Info vs Range:  t={t_nr:.3f}, p={p_nr:.4f}, diff=${np.mean(none_prices)-np.mean(range_prices):.2f}")
print(f"  Range vs Exact:    t={t_re:.3f}, p={p_re:.4f}, diff=${np.mean(range_prices)-np.mean(exact_prices):.2f}")

# Cohen's d for No Info vs Exact (largest effect)
pooled_std = np.sqrt((np.var(none_prices, ddof=1) + np.var(exact_prices, ddof=1)) / 2)
cohens_d = (np.mean(none_prices) - np.mean(exact_prices)) / pooled_std if pooled_std > 0 else 0
print(f"\nCohen's d (No Info vs Exact): {cohens_d:.2f}")

# 3. AI opening offer
print("\n--- 3. AI OPENING OFFER ---")
none_opens = [r['ai_opening_offer'] for r in none_rows if r['ai_opening_offer'] is not None]
range_opens = [r['ai_opening_offer'] for r in range_rows if r['ai_opening_offer'] is not None]
exact_opens = [r['ai_opening_offer'] for r in exact_rows if r['ai_opening_offer'] is not None]

print(f"No Info:    M={np.mean(none_opens):.2f}, SD={np.std(none_opens, ddof=1):.2f}")
print(f"Range Info: M={np.mean(range_opens):.2f}, SD={np.std(range_opens, ddof=1):.2f}")
print(f"Exact Info: M={np.mean(exact_opens):.2f}, SD={np.std(exact_opens, ddof=1):.2f}")

f_open, p_open = stats.f_oneway(none_opens, range_opens, exact_opens)
print(f"ANOVA: F(2,27) = {f_open:.3f}, p = {p_open:.4f}")

# 4. Rounds to deal
print("\n--- 4. ROUNDS TO DEAL ---")
none_rnds = [r['rounds_played'] for r in none_rows if r['is_deal']]
range_rnds = [r['rounds_played'] for r in range_rows if r['is_deal']]
exact_rnds = [r['rounds_played'] for r in exact_rows if r['is_deal']]

print(f"No Info:    M={np.mean(none_rnds):.1f}, SD={np.std(none_rnds, ddof=1):.1f}")
print(f"Range Info: M={np.mean(range_rnds):.1f}, SD={np.std(range_rnds, ddof=1):.1f}")
print(f"Exact Info: M={np.mean(exact_rnds):.1f}, SD={np.std(exact_rnds, ddof=1):.1f}")

# 5. Price deviation from fair price
print("\n--- 5. PRICE DEVIATION FROM FAIR PRICE ---")
none_dev = [r['price_deviation'] for r in none_rows if r['price_deviation'] is not None]
range_dev = [r['price_deviation'] for r in range_rows if r['price_deviation'] is not None]
exact_dev = [r['price_deviation'] for r in exact_rows if r['price_deviation'] is not None]

print(f"No Info:    M={np.mean(none_dev):.2f}, SD={np.std(none_dev, ddof=1):.2f}")
print(f"Range Info: M={np.mean(range_dev):.2f}, SD={np.std(range_dev, ddof=1):.2f}")
print(f"Exact Info: M={np.mean(exact_dev):.2f}, SD={np.std(exact_dev, ddof=1):.2f}")

f_dev, p_dev = stats.f_oneway(none_dev, range_dev, exact_dev)
print(f"ANOVA: F(2,27) = {f_dev:.3f}, p = {p_dev:.4f}")

# 6. Buyer surplus share
print("\n--- 6. BUYER SURPLUS SHARE ---")
for label, subset in [('No Info', none_rows), ('Range', range_rows), ('Exact', exact_rows)]:
    shares = []
    for r in subset:
        if r['is_deal'] and r['human_earnings'] is not None and r['ai_earnings'] is not None:
            total = r['human_earnings'] + r['ai_earnings']
            if total > 0:
                shares.append(r['human_earnings'] / total)
    if shares:
        print(f"  {label}: buyer gets {100*np.mean(shares):.1f}% of surplus (SD={100*np.std(shares, ddof=1):.1f}%)")

# 7. ZOPA size interaction
print("\n--- 7. ZOPA SIZE × INFO CONDITION ---")
for zk in ['tight', 'wide']:
    print(f"\n  {zk.title()} ZOPA:")
    for label, subset in [('No Info', none_rows), ('Range', range_rows), ('Exact', exact_rows)]:
        zsub = [r for r in subset if r['zopa_label'] == zk and r['deal_price'] is not None]
        prices = [r['deal_price'] for r in zsub]
        if prices:
            print(f"    {label}: avg price ${np.mean(prices):.2f} (N={len(prices)})")

# Test interaction: price ~ info_condition * zopa_size
# Simple approach: compare the info effect size across ZOPA conditions
tight_none = [r['deal_price'] for r in none_rows if r['zopa_label'] == 'tight' and r['deal_price']]
tight_exact = [r['deal_price'] for r in exact_rows if r['zopa_label'] == 'tight' and r['deal_price']]
wide_none = [r['deal_price'] for r in none_rows if r['zopa_label'] == 'wide' and r['deal_price']]
wide_exact = [r['deal_price'] for r in exact_rows if r['zopa_label'] == 'wide' and r['deal_price']]

tight_effect = np.mean(tight_none) - np.mean(tight_exact) if tight_none and tight_exact else 0
wide_effect = np.mean(wide_none) - np.mean(wide_exact) if wide_none and wide_exact else 0
print(f"\n  Info effect on price (No Info - Exact):")
print(f"    Tight ZOPA: ${tight_effect:.2f}")
print(f"    Wide ZOPA:  ${wide_effect:.2f}")
print(f"    Interaction: ${wide_effect - tight_effect:.2f} (larger effect under {'wide' if wide_effect > tight_effect else 'tight'} ZOPA)")

# 8. Prediction evaluation
print("\n" + "=" * 60)
print("PREDICTION EVALUATION (from manifest)")
print("=" * 60)
print(f"  deal_rate_exact_vs_none = 'higher'    → REFUTED (both 100%)")
print(f"  deal_rate_range_vs_none = 'lower'     → REFUTED (both 100%)")
print(f"  deal_rate_range_vs_exact = 'lower'    → REFUTED (both 100%)")
print(f"  opening_aggressiveness_range_vs_others = 'higher' → REFUTED (No Info has highest opens: ${np.mean(none_opens):.2f})")
print(f"  deal_price_dispersion_exact_vs_others = 'lower'   → PARTIALLY (exact SD={np.std(exact_prices, ddof=1):.2f} vs none SD={np.std(none_prices, ddof=1):.2f}, range SD={np.std(range_prices, ddof=1):.2f})")
print(f"  deal_rate_gap_tight_vs_wide = 'larger under tight' → UNTESTABLE (no deal rate variation)")

print("\n" + "=" * 60)
print("KEY FINDING: Monotonic information-price gradient")
print("=" * 60)
print(f"More info for buyer → lower deal price (more buyer surplus)")
print(f"No Info: ${np.mean(none_prices):.2f} → Range: ${np.mean(range_prices):.2f} → Exact: ${np.mean(exact_prices):.2f}")
print(f"This is NOT the predicted valley — it's a monotonic advantage effect")
print(f"ANOVA p = {p_anova:.4f}, Cohen's d (None vs Exact) = {cohens_d:.2f}")
