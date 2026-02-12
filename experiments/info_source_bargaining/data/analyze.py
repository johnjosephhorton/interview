"""
Comprehensive statistical analysis of the info_source_bargaining experiment.
Three conditions: bargain_source_none, bargain_source_claimed, bargain_source_verified
"""

import numpy as np
import pandas as pd
from scipy import stats
from itertools import combinations

# --- Load data ----------------------------------------------------------------
df = pd.read_csv("writeup/data/info_source_bargaining_data.csv")
conditions = sorted(df["condition"].unique())
print(f"Loaded {len(df)} observations across {len(conditions)} conditions")
print(f"Conditions: {conditions}")
print(f"Observations per condition: {df['condition'].value_counts().sort_index().to_dict()}")
print(f"Deal rate: {df['deal_reached'].mean():.1%}")
print()

# Only keep deals for price/surplus analyses
deals = df[df["deal_reached"] == True].copy()
print(f"Deals reached: {len(deals)} / {len(df)}")
print()

# Helper: nice condition labels
label = {
    "bargain_source_none": "None",
    "bargain_source_claimed": "Claimed",
    "bargain_source_verified": "Verified",
}

def section(title):
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)

def pairwise_label(c1, c2):
    return f"{label[c1]} vs {label[c2]}"

# ==============================================================================
# A. DEAL PRICE ANALYSIS
# ==============================================================================
section("A. Deal Price Analysis (deal_price ~ condition)")

groups_price = [deals[deals["condition"] == c]["deal_price"].values for c in conditions]

print("\nDescriptive statistics:")
for c, g in zip(conditions, groups_price):
    print(f"  {label[c]:>10s}: n={len(g):3d}, mean={np.mean(g):7.2f}, sd={np.std(g, ddof=1):6.2f}, "
          f"median={np.median(g):7.2f}, range=[{np.min(g):.1f}, {np.max(g):.1f}]")

# One-way ANOVA
F_stat, p_anova = stats.f_oneway(*groups_price)
# Eta-squared
grand_mean = np.mean(np.concatenate(groups_price))
ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups_price)
ss_total = sum(np.sum((g - grand_mean) ** 2) for g in groups_price)
eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
print(f"\nOne-way ANOVA: F({len(conditions)-1}, {sum(len(g) for g in groups_price)-len(conditions)}) = {F_stat:.4f}, p = {p_anova:.6f}")
print(f"Effect size: eta-squared = {eta_sq:.4f}")

# Pairwise t-tests with Bonferroni
print("\nPairwise t-tests (Bonferroni corrected, k=3 comparisons):")
k = len(list(combinations(range(len(conditions)), 2)))
for i, j in combinations(range(len(conditions)), 2):
    t_stat, p_val = stats.ttest_ind(groups_price[i], groups_price[j])
    pooled_var = ((len(groups_price[i]) - 1) * np.var(groups_price[i], ddof=1) +
                  (len(groups_price[j]) - 1) * np.var(groups_price[j], ddof=1)) / \
                 (len(groups_price[i]) + len(groups_price[j]) - 2)
    d = (np.mean(groups_price[i]) - np.mean(groups_price[j])) / np.sqrt(pooled_var) if pooled_var > 0 else 0.0
    p_bonf = min(p_val * k, 1.0)
    print(f"  {pairwise_label(conditions[i], conditions[j]):>25s}: "
          f"t = {t_stat:+7.3f}, p = {p_val:.6f}, p_bonf = {p_bonf:.6f}, Cohen's d = {d:+.3f}")

print()

# ==============================================================================
# B. FIRST-ROUND ACCEPTANCE RATE
# ==============================================================================
section("B. First-Round Acceptance Rate (first_human_response == 'accept')")

df["accepted_r1"] = (df["first_human_response"] == "accept").astype(int)

print("\nAcceptance rates by condition:")
ct_data = {}
for c in conditions:
    sub = df[df["condition"] == c]
    n_accept = sub["accepted_r1"].sum()
    n_total = len(sub)
    ct_data[c] = (n_accept, n_total - n_accept)
    print(f"  {label[c]:>10s}: {n_accept}/{n_total} = {n_accept/n_total:.1%}")

# Contingency table: rows = conditions, cols = [accept, not_accept]
contingency = np.array([ct_data[c] for c in conditions])
print(f"\nContingency table (accept, reject):\n{contingency}")

chi2, p_chi2, dof, expected = stats.chi2_contingency(contingency)
print(f"\nChi-squared test: chi2({dof}) = {chi2:.4f}, p = {p_chi2:.6f}")

# Check if any expected count < 5
if np.any(expected < 5):
    print("WARNING: Some expected counts < 5; consider Fisher's exact test.")
print(f"Expected counts:\n{expected}")

# Pairwise proportion z-tests with Bonferroni
print("\nPairwise proportion tests (Bonferroni corrected):")
for i, j in combinations(range(len(conditions)), 2):
    ci, cj = conditions[i], conditions[j]
    x1, n1 = ct_data[ci][0], sum(ct_data[ci])
    x2, n2 = ct_data[cj][0], sum(ct_data[cj])
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2)) if 0 < p_pool < 1 else 1e-10
    z = (p1 - p2) / se
    p_val = 2 * (1 - stats.norm.cdf(abs(z)))
    p_bonf = min(p_val * k, 1.0)
    # Also Fisher's exact for 2x2
    table_2x2 = np.array([[ct_data[ci][0], ct_data[ci][1]],
                           [ct_data[cj][0], ct_data[cj][1]]])
    _, p_fisher = stats.fisher_exact(table_2x2)
    p_fisher_bonf = min(p_fisher * k, 1.0)
    print(f"  {pairwise_label(ci, cj):>25s}: "
          f"z = {z:+7.3f}, p = {p_val:.6f}, p_bonf = {p_bonf:.6f} | "
          f"Fisher p = {p_fisher:.6f}, Fisher p_bonf = {p_fisher_bonf:.6f}")

print()

# ==============================================================================
# C. ROUNDS TO DEAL
# ==============================================================================
section("C. Rounds to Deal (rounds_played ~ condition)")

groups_rounds = [deals[deals["condition"] == c]["rounds_played"].values for c in conditions]

print("\nDescriptive statistics:")
for c, g in zip(conditions, groups_rounds):
    print(f"  {label[c]:>10s}: n={len(g):3d}, mean={np.mean(g):5.2f}, sd={np.std(g, ddof=1):5.2f}, "
          f"median={np.median(g):4.1f}, range=[{np.min(g)}, {np.max(g)}]")

# Shapiro-Wilk normality test
print("\nShapiro-Wilk normality tests:")
for c, g in zip(conditions, groups_rounds):
    if len(g) >= 3:
        w, p_sw = stats.shapiro(g)
        print(f"  {label[c]:>10s}: W = {w:.4f}, p = {p_sw:.6f} {'***' if p_sw < 0.05 else ''}")

# Kruskal-Wallis
H_stat, p_kw = stats.kruskal(*groups_rounds)
print(f"\nKruskal-Wallis: H({len(conditions)-1}) = {H_stat:.4f}, p = {p_kw:.6f}")

# Effect size: epsilon-squared = H / (n-1)
n_total_rounds = sum(len(g) for g in groups_rounds)
eps_sq = H_stat / (n_total_rounds - 1)
print(f"Effect size: epsilon-squared = {eps_sq:.4f}")

# Pairwise Mann-Whitney U with Bonferroni
print("\nPairwise Mann-Whitney U tests (Bonferroni corrected):")
for i, j in combinations(range(len(conditions)), 2):
    U_stat, p_val = stats.mannwhitneyu(groups_rounds[i], groups_rounds[j], alternative="two-sided")
    p_bonf = min(p_val * k, 1.0)
    # Rank-biserial correlation as effect size
    n1, n2 = len(groups_rounds[i]), len(groups_rounds[j])
    r_rb = 1 - (2 * U_stat) / (n1 * n2)
    print(f"  {pairwise_label(conditions[i], conditions[j]):>25s}: "
          f"U = {U_stat:8.1f}, p = {p_val:.6f}, p_bonf = {p_bonf:.6f}, r_rb = {r_rb:+.3f}")

print()

# ==============================================================================
# D. FIRST COUNTEROFFER ANCHORING
# ==============================================================================
section("D. First Counteroffer Anchoring (among non-accepters)")

# Filter to sessions where buyer counteroffered (not accepted R1) and counteroffer is not NaN
counter = df[(df["first_human_response"] != "accept") &
             (df["first_human_counteroffer"].notna())].copy()

print(f"\nSessions with a first counteroffer: {len(counter)}")

groups_counter = [counter[counter["condition"] == c]["first_human_counteroffer"].values for c in conditions]

print("\nDescriptive statistics:")
for c, g in zip(conditions, groups_counter):
    if len(g) > 0:
        print(f"  {label[c]:>10s}: n={len(g):3d}, mean={np.mean(g):7.2f}, sd={np.std(g, ddof=1):6.2f}, "
              f"median={np.median(g):7.2f}, range=[{np.min(g):.1f}, {np.max(g):.1f}]")
    else:
        print(f"  {label[c]:>10s}: n=  0 (no counteroffers)")

# Only run tests if we have data in at least 2 groups
valid_groups = [g for g in groups_counter if len(g) >= 2]
F_co = p_co = eta_sq_co = None
if len(valid_groups) >= 2:
    # Shapiro-Wilk
    print("\nShapiro-Wilk normality tests:")
    for c, g in zip(conditions, groups_counter):
        if len(g) >= 3:
            w, p_sw = stats.shapiro(g)
            print(f"  {label[c]:>10s}: W = {w:.4f}, p = {p_sw:.6f} {'***' if p_sw < 0.05 else ''}")

    # Try ANOVA
    non_empty = [(c, g) for c, g in zip(conditions, groups_counter) if len(g) >= 2]
    if len(non_empty) >= 2:
        F_co, p_co = stats.f_oneway(*[g for _, g in non_empty])
        grand_mean_co = np.mean(np.concatenate([g for _, g in non_empty]))
        ss_bet_co = sum(len(g) * (np.mean(g) - grand_mean_co) ** 2 for _, g in non_empty)
        ss_tot_co = sum(np.sum((g - grand_mean_co) ** 2) for _, g in non_empty)
        eta_sq_co = ss_bet_co / ss_tot_co if ss_tot_co > 0 else 0.0
        df_between = len(non_empty) - 1
        df_within = sum(len(g) for _, g in non_empty) - len(non_empty)
        print(f"\nOne-way ANOVA: F({df_between}, {df_within}) = {F_co:.4f}, p = {p_co:.6f}")
        print(f"Effect size: eta-squared = {eta_sq_co:.4f}")

    # Kruskal-Wallis as robustness check
    if len(non_empty) >= 2:
        H_co, p_kw_co = stats.kruskal(*[g for _, g in non_empty])
        print(f"Kruskal-Wallis: H = {H_co:.4f}, p = {p_kw_co:.6f}")

    # Pairwise tests
    print("\nPairwise t-tests (Bonferroni corrected):")
    pairs = list(combinations(range(len(conditions)), 2))
    k_co = len(pairs)
    for i, j in pairs:
        gi, gj = groups_counter[i], groups_counter[j]
        if len(gi) >= 2 and len(gj) >= 2:
            t_stat, p_val = stats.ttest_ind(gi, gj)
            p_bonf = min(p_val * k_co, 1.0)
            pooled_var = ((len(gi) - 1) * np.var(gi, ddof=1) +
                          (len(gj) - 1) * np.var(gj, ddof=1)) / \
                         (len(gi) + len(gj) - 2)
            d = (np.mean(gi) - np.mean(gj)) / np.sqrt(pooled_var) if pooled_var > 0 else 0.0
            print(f"  {pairwise_label(conditions[i], conditions[j]):>25s}: "
                  f"t = {t_stat:+7.3f}, p = {p_val:.6f}, p_bonf = {p_bonf:.6f}, Cohen's d = {d:+.3f}")
        else:
            print(f"  {pairwise_label(conditions[i], conditions[j]):>25s}: insufficient data")
else:
    print("\nInsufficient data for inferential tests on counteroffers.")

print()

# ==============================================================================
# E. BUYER'S SHARE OF SURPLUS
# ==============================================================================
section("E. Buyer's Share of Surplus (buyer_share ~ condition)")

# buyer_share is already in the data; recompute to be safe
deals["buyer_share_calc"] = deals["human_earnings"] / (deals["human_earnings"] + deals["ai_earnings"])

groups_share = [deals[deals["condition"] == c]["buyer_share_calc"].values for c in conditions]

print("\nDescriptive statistics:")
for c, g in zip(conditions, groups_share):
    print(f"  {label[c]:>10s}: n={len(g):3d}, mean={np.mean(g):6.4f}, sd={np.std(g, ddof=1):6.4f}, "
          f"median={np.median(g):6.4f}, range=[{np.min(g):.4f}, {np.max(g):.4f}]")

# One-way ANOVA
F_share, p_share = stats.f_oneway(*groups_share)
grand_mean_share = np.mean(np.concatenate(groups_share))
ss_bet_share = sum(len(g) * (np.mean(g) - grand_mean_share) ** 2 for g in groups_share)
ss_tot_share = sum(np.sum((g - grand_mean_share) ** 2) for g in groups_share)
eta_sq_share = ss_bet_share / ss_tot_share if ss_tot_share > 0 else 0.0
df_between_share = len(conditions) - 1
df_within_share = sum(len(g) for g in groups_share) - len(conditions)
print(f"\nOne-way ANOVA: F({df_between_share}, {df_within_share}) = {F_share:.4f}, p = {p_share:.6f}")
print(f"Effect size: eta-squared = {eta_sq_share:.4f}")

# Pairwise t-tests with Bonferroni
print("\nPairwise t-tests (Bonferroni corrected):")
for i, j in combinations(range(len(conditions)), 2):
    t_stat, p_val = stats.ttest_ind(groups_share[i], groups_share[j])
    pooled_var = ((len(groups_share[i]) - 1) * np.var(groups_share[i], ddof=1) +
                  (len(groups_share[j]) - 1) * np.var(groups_share[j], ddof=1)) / \
                 (len(groups_share[i]) + len(groups_share[j]) - 2)
    d = (np.mean(groups_share[i]) - np.mean(groups_share[j])) / np.sqrt(pooled_var) if pooled_var > 0 else 0.0
    p_bonf = min(p_val * k, 1.0)
    print(f"  {pairwise_label(conditions[i], conditions[j]):>25s}: "
          f"t = {t_stat:+7.3f}, p = {p_val:.6f}, p_bonf = {p_bonf:.6f}, Cohen's d = {d:+.3f}")

print()

# ==============================================================================
# SUMMARY
# ==============================================================================
section("SUMMARY OF KEY FINDINGS")

sig = lambda p: "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."

summary_d = f"  D. Counteroffer ANOVA:      F = {F_co:7.3f}, p = {p_co:.4f} {sig(p_co)}   eta2 = {eta_sq_co:.4f}" if F_co is not None else "  D. Counteroffer ANOVA:      insufficient data"

print(f"""
  A. Deal Price ANOVA:        F = {F_stat:7.3f}, p = {p_anova:.4f} {sig(p_anova)}   eta2 = {eta_sq:.4f}
  B. R1 Accept Chi-squared:   X2 = {chi2:6.3f}, p = {p_chi2:.4f} {sig(p_chi2)}
  C. Rounds Kruskal-Wallis:   H = {H_stat:7.3f}, p = {p_kw:.4f} {sig(p_kw)}   eps2 = {eps_sq:.4f}
{summary_d}
  E. Buyer Share ANOVA:       F = {F_share:7.3f}, p = {p_share:.4f} {sig(p_share)}   eta2 = {eta_sq_share:.4f}

  Significance: *** p<.001, ** p<.01, * p<.05, n.s. not significant
""")
