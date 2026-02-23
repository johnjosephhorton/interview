#!/usr/bin/env python3
"""Compute planned metrics from raw_sessions.csv per analysis_plan.md.

Production run: N=30 per cell (360 total), gpt-4o model.
Implements: logistic regression, Fisher exact tests, confidence intervals,
Holm-Bonferroni correction, holdout validation.
"""

import csv
import os
import warnings
from collections import defaultdict

import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")

ANALYSIS_DIR = os.path.dirname(__file__)

# Holdout conditions (per manifest.toml)
HOLDOUT = {"C10", "C12"}


def load_data():
    rows = []
    with open(os.path.join(ANALYSIS_DIR, "raw_sessions.csv")) as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["deal"] = int(row["deal"])
            row["feasible"] = int(row["feasible"])
            row["buyer_wtp"] = float(row["buyer_wtp"])
            row["seller_wta"] = float(row["seller_wta"])
            row["gains_from_trade"] = float(row["gains_from_trade"])
            row["buyer_earnings"] = float(row["buyer_earnings"])
            row["seller_earnings"] = float(row["seller_earnings"])
            row["bargain_rounds_played"] = int(row["bargain_rounds_played"])
            row["n_comm_messages"] = int(row["n_comm_messages"])
            row["guardrail_triggered"] = int(row["guardrail_triggered"])
            row["final_price"] = float(row["final_price"]) if row["final_price"] else None
            row["surplus_captured"] = float(row["surplus_captured"]) if row["surplus_captured"] else None
            row["price_split_ratio"] = float(row["price_split_ratio"]) if row["price_split_ratio"] else None
            row["rounds_to_agreement"] = int(row["rounds_to_agreement"]) if row["rounds_to_agreement"] else None
            rows.append(row)
    return rows


def wilson_ci(successes, n, alpha=0.05):
    """Wilson score interval for binomial proportion."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = successes / n
    z = stats.norm.ppf(1 - alpha / 2)
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, max(0, centre - margin), min(1, centre + margin)


def holm_bonferroni(p_values, alpha=0.05):
    """Return adjusted p-values using Holm-Bonferroni."""
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n
    for rank, (orig_idx, p) in enumerate(indexed):
        adj_p = min(1.0, p * (n - rank))
        adjusted[orig_idx] = adj_p
    # Enforce monotonicity
    for rank in range(1, n):
        orig_idx = indexed[rank][0]
        prev_idx = indexed[rank - 1][0]
        adjusted[orig_idx] = max(adjusted[orig_idx], adjusted[prev_idx])
    return adjusted


def summary_by_condition(data):
    """Compute summary statistics by condition."""
    groups = defaultdict(list)
    for r in data:
        groups[r["condition_short"]].append(r)

    rows_out = []
    for cid in sorted(groups.keys()):
        g = groups[cid]
        n = len(g)
        comm = g[0]["communication"]
        vgap = g[0]["value_gap"]
        info = g[0]["info_asymmetry"]

        deals = [r["deal"] for r in g]
        deal_rate = np.mean(deals)
        deal_se = np.std(deals, ddof=1) / np.sqrt(n) if n > 1 else 0

        feasible_n = sum(r["feasible"] for r in g)
        feasible_deals = [r for r in g if r["feasible"] and r["deal"]]
        feasible_deal_rate = len(feasible_deals) / feasible_n if feasible_n > 0 else None

        prices = [r["final_price"] for r in g if r["final_price"] is not None]
        avg_price = np.mean(prices) if prices else None
        sd_price = np.std(prices, ddof=1) if len(prices) > 1 else None

        surplus_vals = [r["surplus_captured"] for r in g if r["surplus_captured"] is not None and r["deal"]]
        avg_surplus = np.mean(surplus_vals) if surplus_vals else None

        split_vals = [r["price_split_ratio"] for r in g if r["price_split_ratio"] is not None]
        avg_split = np.mean(split_vals) if split_vals else None
        sd_split = np.std(split_vals, ddof=1) if len(split_vals) > 1 else None

        buyer_e = [r["buyer_earnings"] for r in g]
        seller_e = [r["seller_earnings"] for r in g]

        guardrails = sum(r["guardrail_triggered"] for r in g)

        # Wilson CI for deal rate
        _, dl, du = wilson_ci(sum(deals), n)

        rows_out.append({
            "condition_id": cid,
            "communication": comm,
            "value_gap": vgap,
            "info_asymmetry": info,
            "n_sessions": n,
            "n_feasible": feasible_n,
            "n_deals": sum(deals),
            "deal_rate": f"{deal_rate:.3f}",
            "deal_rate_se": f"{deal_se:.3f}",
            "deal_rate_ci_lo": f"{dl:.3f}",
            "deal_rate_ci_hi": f"{du:.3f}",
            "feasible_deal_rate": f"{feasible_deal_rate:.3f}" if feasible_deal_rate is not None else "",
            "avg_price": f"{avg_price:.2f}" if avg_price is not None else "",
            "sd_price": f"{sd_price:.2f}" if sd_price is not None else "",
            "avg_surplus_captured": f"{avg_surplus:.3f}" if avg_surplus is not None else "",
            "avg_price_split": f"{avg_split:.3f}" if avg_split is not None else "",
            "sd_price_split": f"{sd_split:.3f}" if sd_split is not None else "",
            "avg_buyer_earnings": f"{np.mean(buyer_e):.2f}",
            "avg_seller_earnings": f"{np.mean(seller_e):.2f}",
            "avg_gains_from_trade": f"{np.mean([r['gains_from_trade'] for r in g]):.2f}",
            "n_guardrail_triggers": guardrails,
        })

    outpath = os.path.join(ANALYSIS_DIR, "summary_by_condition.csv")
    with open(outpath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"Wrote {len(rows_out)} conditions to {outpath}")
    return rows_out


def logistic_regression_simple(X, y):
    """Simple logistic regression via iteratively reweighted least squares.

    Returns coefficients and standard errors. X should include intercept column.
    """
    X = np.array(X, dtype=float)
    y = np.array(y, dtype=float)
    n, p = X.shape
    beta = np.zeros(p)

    for _ in range(50):
        mu = 1 / (1 + np.exp(-X @ beta))
        mu = np.clip(mu, 1e-8, 1 - 1e-8)
        W = np.diag(mu * (1 - mu))
        z = X @ beta + np.linalg.solve(W + 1e-10 * np.eye(n), y - mu)
        try:
            beta = np.linalg.solve(X.T @ W @ X + 1e-10 * np.eye(p), X.T @ W @ z)
        except np.linalg.LinAlgError:
            break

    mu = 1 / (1 + np.exp(-X @ beta))
    mu = np.clip(mu, 1e-8, 1 - 1e-8)
    W = np.diag(mu * (1 - mu))
    try:
        cov = np.linalg.inv(X.T @ W @ X)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)

    return beta, se


def compute_model_results(data):
    """Compute treatment effects per analysis_plan.md with proper inference."""
    results = []

    # Exclude holdout conditions for primary analysis
    train = [r for r in data if r["condition_short"] not in HOLDOUT]
    all_data = data  # keep full data for descriptives

    # =========================================================================
    # H1: Cheap talk increases deal rate (logistic + Fisher)
    # =========================================================================
    none_deals = [r["deal"] for r in train if r["communication"] == "none"]
    talk_deals = [r["deal"] for r in train if r["communication"] in ("cheap_talk", "extended_talk")]
    none_rate = np.mean(none_deals)
    talk_rate = np.mean(talk_deals)
    diff_h1 = talk_rate - none_rate

    # Fisher exact test
    a, b = sum(talk_deals), len(talk_deals) - sum(talk_deals)
    c, d = sum(none_deals), len(none_deals) - sum(none_deals)
    _, p_h1 = stats.fisher_exact([[a, b], [c, d]], alternative="two-sided")

    # Logistic regression: deal ~ talk + value_gap + info_asymmetry
    y = np.array([r["deal"] for r in train])
    X = []
    for r in train:
        talk = 1 if r["communication"] != "none" else 0
        wide = 1 if r["value_gap"] == "wide" else 0
        onesided = 1 if r["info_asymmetry"] == "one_sided_buyer_known" else 0
        X.append([1, talk, wide, onesided])
    X = np.array(X)
    beta_h1, se_h1 = logistic_regression_simple(X, y)

    # Wald test on talk coefficient
    z_h1 = beta_h1[1] / se_h1[1] if se_h1[1] > 0 else 0
    p_h1_wald = 2 * (1 - stats.norm.cdf(abs(z_h1)))

    # CI for coefficient (log-odds)
    ci_lo_logit = beta_h1[1] - 1.96 * se_h1[1]
    ci_hi_logit = beta_h1[1] + 1.96 * se_h1[1]

    # Convert to odds ratio
    or_h1 = np.exp(beta_h1[1])
    or_lo = np.exp(ci_lo_logit)
    or_hi = np.exp(ci_hi_logit)

    # CI for rate difference (normal approximation)
    se_diff = np.sqrt(talk_rate * (1 - talk_rate) / len(talk_deals) +
                      none_rate * (1 - none_rate) / len(none_deals))
    ci_lo_diff = diff_h1 - 1.96 * se_diff
    ci_hi_diff = diff_h1 + 1.96 * se_diff

    results.append({
        "hypothesis": "H1",
        "test": "Cheap talk increases deal rate",
        "estimand": "P(deal|talk) - P(deal|none)",
        "effect_size": f"{diff_h1:+.3f}",
        "ci_lower": f"{ci_lo_diff:.3f}",
        "ci_upper": f"{ci_hi_diff:.3f}",
        "p_value": f"{p_h1:.4f}",
        "p_value_wald": f"{p_h1_wald:.4f}",
        "odds_ratio": f"{or_h1:.2f}",
        "or_ci": f"[{or_lo:.2f}, {or_hi:.2f}]",
        "direction": "CONFIRMED" if diff_h1 > 0 and p_h1 < 0.10 else ("REFUTED" if diff_h1 < 0 else "UNCLEAR"),
        "confidence": "MODERATE" if p_h1 < 0.05 else "LOW",
        "note": f"none={none_rate:.3f} (n={len(none_deals)}), talk={talk_rate:.3f} (n={len(talk_deals)}), Fisher p={p_h1:.4f}, Wald p={p_h1_wald:.4f}",
    })

    # =========================================================================
    # H1a: Cheap talk (1-round) vs none
    # =========================================================================
    ct_deals = [r["deal"] for r in train if r["communication"] == "cheap_talk"]
    ct_rate = np.mean(ct_deals)
    ct_diff = ct_rate - none_rate
    a2, b2 = sum(ct_deals), len(ct_deals) - sum(ct_deals)
    _, p_h1a = stats.fisher_exact([[a2, b2], [c, d]], alternative="two-sided")

    results.append({
        "hypothesis": "H1a",
        "test": "Cheap talk (1-round) vs none",
        "estimand": "P(deal|cheap_talk) - P(deal|none)",
        "effect_size": f"{ct_diff:+.3f}",
        "ci_lower": "",
        "ci_upper": "",
        "p_value": f"{p_h1a:.4f}",
        "p_value_wald": "",
        "odds_ratio": "",
        "or_ci": "",
        "direction": "CONFIRMED" if ct_diff > 0 and p_h1a < 0.10 else "UNCLEAR",
        "confidence": "MODERATE" if p_h1a < 0.05 else "LOW",
        "note": f"cheap_talk={ct_rate:.3f} (n={len(ct_deals)}), none={none_rate:.3f}",
    })

    # =========================================================================
    # H1b: Extended talk vs none
    # =========================================================================
    et_deals = [r["deal"] for r in train if r["communication"] == "extended_talk"]
    et_rate = np.mean(et_deals)
    et_diff = et_rate - none_rate
    a3, b3 = sum(et_deals), len(et_deals) - sum(et_deals)
    _, p_h1b = stats.fisher_exact([[a3, b3], [c, d]], alternative="two-sided")

    results.append({
        "hypothesis": "H1b",
        "test": "Extended talk vs none",
        "estimand": "P(deal|extended_talk) - P(deal|none)",
        "effect_size": f"{et_diff:+.3f}",
        "ci_lower": "",
        "ci_upper": "",
        "p_value": f"{p_h1b:.4f}",
        "p_value_wald": "",
        "odds_ratio": "",
        "or_ci": "",
        "direction": "CONFIRMED" if et_diff > 0 and p_h1b < 0.10 else ("REFUTED" if et_diff < -0.05 else "UNCLEAR"),
        "confidence": "MODERATE" if p_h1b < 0.05 else "LOW",
        "note": f"extended_talk={et_rate:.3f} (n={len(et_deals)}), none={none_rate:.3f}",
    })

    # =========================================================================
    # H2: Communication × value_gap interaction
    # =========================================================================
    cells = defaultdict(list)
    for r in train:
        talk_any = "talk" if r["communication"] != "none" else "none"
        cells[(talk_any, r["value_gap"])].append(r["deal"])

    narrow_effect = np.mean(cells[("talk", "narrow")]) - np.mean(cells[("none", "narrow")])
    wide_effect = np.mean(cells[("talk", "wide")]) - np.mean(cells[("none", "wide")])
    interaction_h2 = narrow_effect - wide_effect

    # Logistic with interaction
    y2 = np.array([r["deal"] for r in train])
    X2 = []
    for r in train:
        talk = 1 if r["communication"] != "none" else 0
        wide = 1 if r["value_gap"] == "wide" else 0
        onesided = 1 if r["info_asymmetry"] == "one_sided_buyer_known" else 0
        X2.append([1, talk, wide, onesided, talk * wide])
    X2 = np.array(X2)
    beta_h2, se_h2 = logistic_regression_simple(X2, y2)
    z_h2 = beta_h2[4] / se_h2[4] if se_h2[4] > 0 else 0
    p_h2_wald = 2 * (1 - stats.norm.cdf(abs(z_h2)))

    results.append({
        "hypothesis": "H2",
        "test": "Communication × value_gap interaction on deal rate",
        "estimand": "(talk_narrow - none_narrow) - (talk_wide - none_wide)",
        "effect_size": f"{interaction_h2:+.3f}",
        "ci_lower": "",
        "ci_upper": "",
        "p_value": f"{p_h2_wald:.4f}",
        "p_value_wald": f"{p_h2_wald:.4f}",
        "odds_ratio": f"{np.exp(beta_h2[4]):.2f}",
        "or_ci": "",
        "direction": "CONFIRMED" if interaction_h2 > 0.05 and p_h2_wald < 0.10 else ("REFUTED" if interaction_h2 < -0.05 else "UNCLEAR"),
        "confidence": "MODERATE" if p_h2_wald < 0.05 else "LOW",
        "note": f"narrow_effect={narrow_effect:+.3f}, wide_effect={wide_effect:+.3f}, interaction_coef={beta_h2[4]:+.3f}",
    })

    # =========================================================================
    # H3: Cheap talk improves surplus capture (feasible trades)
    # =========================================================================
    feasible = [r for r in train if r["feasible"]]
    none_feas_deals = [r["deal"] for r in feasible if r["communication"] == "none"]
    talk_feas_deals = [r["deal"] for r in feasible if r["communication"] != "none"]
    none_feas_rate = np.mean(none_feas_deals)
    talk_feas_rate = np.mean(talk_feas_deals)
    surplus_diff = talk_feas_rate - none_feas_rate

    # Fisher exact on feasible subgroup
    af = sum(talk_feas_deals)
    bf = len(talk_feas_deals) - af
    cf = sum(none_feas_deals)
    df_ = len(none_feas_deals) - cf
    _, p_h3 = stats.fisher_exact([[af, bf], [cf, df_]], alternative="two-sided")

    se_diff_h3 = np.sqrt(talk_feas_rate * (1 - talk_feas_rate) / len(talk_feas_deals) +
                          none_feas_rate * (1 - none_feas_rate) / len(none_feas_deals))

    results.append({
        "hypothesis": "H3",
        "test": "Cheap talk improves surplus capture (feasible trades)",
        "estimand": "P(deal|talk,feasible) - P(deal|none,feasible)",
        "effect_size": f"{surplus_diff:+.3f}",
        "ci_lower": f"{surplus_diff - 1.96 * se_diff_h3:.3f}",
        "ci_upper": f"{surplus_diff + 1.96 * se_diff_h3:.3f}",
        "p_value": f"{p_h3:.4f}",
        "p_value_wald": "",
        "odds_ratio": "",
        "or_ci": "",
        "direction": "CONFIRMED" if surplus_diff > 0 and p_h3 < 0.10 else "UNCLEAR",
        "confidence": "MODERATE" if p_h3 < 0.05 else "LOW",
        "note": f"none_feasible={none_feas_rate:.3f} (n={len(none_feas_deals)}), talk_feasible={talk_feas_rate:.3f} (n={len(talk_feas_deals)})",
    })

    # =========================================================================
    # Holm-Bonferroni correction for H1, H2, H3
    # =========================================================================
    primary_ps = [p_h1, p_h2_wald, p_h3]
    adjusted_ps = holm_bonferroni(primary_ps)
    results.append({
        "hypothesis": "Holm-Bonferroni",
        "test": "Family-wise correction for H1, H2, H3",
        "estimand": "Adjusted p-values",
        "effect_size": "",
        "ci_lower": "",
        "ci_upper": "",
        "p_value": f"H1={adjusted_ps[0]:.4f}, H2={adjusted_ps[1]:.4f}, H3={adjusted_ps[2]:.4f}",
        "p_value_wald": "",
        "odds_ratio": "",
        "or_ci": "",
        "direction": "",
        "confidence": "",
        "note": f"Raw: H1={p_h1:.4f}, H2={p_h2_wald:.4f}, H3={p_h3:.4f}",
    })

    # =========================================================================
    # H4: One-sided info amplifies cheap talk (exploratory)
    # =========================================================================
    info_cells = defaultdict(list)
    for r in train:
        talk_any = "talk" if r["communication"] != "none" else "none"
        info_cells[(talk_any, r["info_asymmetry"])].append(r["deal"])

    twosided_effect = np.mean(info_cells[("talk", "two_sided_private")]) - np.mean(info_cells[("none", "two_sided_private")])
    onesided_effect = np.mean(info_cells[("talk", "one_sided_buyer_known")]) - np.mean(info_cells[("none", "one_sided_buyer_known")])
    info_interaction = onesided_effect - twosided_effect

    # Logistic with info interaction
    y4 = np.array([r["deal"] for r in train])
    X4 = []
    for r in train:
        talk = 1 if r["communication"] != "none" else 0
        wide = 1 if r["value_gap"] == "wide" else 0
        onesided = 1 if r["info_asymmetry"] == "one_sided_buyer_known" else 0
        X4.append([1, talk, wide, onesided, talk * onesided])
    X4 = np.array(X4)
    beta_h4, se_h4 = logistic_regression_simple(X4, y4)
    z_h4 = beta_h4[4] / se_h4[4] if se_h4[4] > 0 else 0
    p_h4 = 2 * (1 - stats.norm.cdf(abs(z_h4)))

    results.append({
        "hypothesis": "H4",
        "test": "One-sided info amplifies cheap talk (exploratory)",
        "estimand": "(talk_onesided - none_onesided) - (talk_twosided - none_twosided)",
        "effect_size": f"{info_interaction:+.3f}",
        "ci_lower": "",
        "ci_upper": "",
        "p_value": f"{p_h4:.4f}",
        "p_value_wald": f"{p_h4:.4f}",
        "odds_ratio": f"{np.exp(beta_h4[4]):.2f}",
        "or_ci": "",
        "direction": "CONFIRMED" if info_interaction > 0.05 and p_h4 < 0.10 else ("REFUTED" if info_interaction < -0.05 else "UNCLEAR"),
        "confidence": "Exploratory",
        "note": f"onesided_effect={onesided_effect:+.3f}, twosided_effect={twosided_effect:+.3f}",
    })

    # =========================================================================
    # H5: Extended talk more informative (proxy: message volume + deal rate)
    # =========================================================================
    cheap_msgs = [r["n_comm_messages"] for r in all_data if r["communication"] == "cheap_talk"]
    ext_msgs = [r["n_comm_messages"] for r in all_data if r["communication"] == "extended_talk"]
    _, p_h5 = stats.mannwhitneyu(ext_msgs, cheap_msgs, alternative="greater")

    # Also compare deal rates: extended vs cheap_talk
    ct_all = [r["deal"] for r in train if r["communication"] == "cheap_talk"]
    et_all = [r["deal"] for r in train if r["communication"] == "extended_talk"]
    ct_vs_et_diff = np.mean(et_all) - np.mean(ct_all)

    results.append({
        "hypothesis": "H5",
        "test": "Extended talk more informative than single-round",
        "estimand": "Communication volume + deal rate comparison",
        "effect_size": f"cheap_talk_msgs={np.mean(cheap_msgs):.1f}, extended_msgs={np.mean(ext_msgs):.1f}",
        "ci_lower": "",
        "ci_upper": "",
        "p_value": f"{p_h5:.4f}",
        "p_value_wald": "",
        "odds_ratio": "",
        "or_ci": "",
        "direction": "CONFIRMED" if np.mean(ext_msgs) > np.mean(cheap_msgs) else "UNCLEAR",
        "confidence": "Exploratory (proxy)",
        "note": f"Volume: confirmed. Deal rate: extended={np.mean(et_all):.3f} vs cheap_talk={np.mean(ct_all):.3f} (diff={ct_vs_et_diff:+.3f})",
    })

    # =========================================================================
    # H6: Price split closer to 50-50 with cheap talk (exploratory)
    # =========================================================================
    none_splits = [r["price_split_ratio"] for r in train if r["communication"] == "none" and r["price_split_ratio"] is not None]
    talk_splits = [r["price_split_ratio"] for r in train if r["communication"] != "none" and r["price_split_ratio"] is not None]

    none_mean_split = np.mean(none_splits) if none_splits else None
    talk_mean_split = np.mean(talk_splits) if talk_splits else None
    none_var_split = np.var(none_splits, ddof=1) if len(none_splits) > 1 else None
    talk_var_split = np.var(talk_splits, ddof=1) if len(talk_splits) > 1 else None

    # Levene's test
    if len(none_splits) > 1 and len(talk_splits) > 1:
        stat_lev, p_h6 = stats.levene(none_splits, talk_splits)
    else:
        p_h6 = 1.0

    # Distance from 0.5 (50-50 split)
    none_dist = np.mean([abs(s - 0.5) for s in none_splits]) if none_splits else None
    talk_dist = np.mean([abs(s - 0.5) for s in talk_splits]) if talk_splits else None

    results.append({
        "hypothesis": "H6",
        "test": "Price split closer to 50-50 with cheap talk (exploratory)",
        "estimand": "Mean |split - 0.5| comparison + Levene test",
        "effect_size": f"none_dist={none_dist:.3f}, talk_dist={talk_dist:.3f}" if none_dist and talk_dist else "insufficient data",
        "ci_lower": "",
        "ci_upper": "",
        "p_value": f"{p_h6:.4f}",
        "p_value_wald": "",
        "odds_ratio": "",
        "or_ci": "",
        "direction": "CONFIRMED" if talk_dist and none_dist and talk_dist < none_dist else "UNCLEAR",
        "confidence": "Exploratory",
        "note": f"none: mean={none_mean_split:.3f}, var={none_var_split:.3f}, n={len(none_splits)}; talk: mean={talk_mean_split:.3f}, var={talk_var_split:.3f}, n={len(talk_splits)}",
    })

    # =========================================================================
    # Information asymmetry main effect
    # =========================================================================
    twosided_deals = [r["deal"] for r in train if r["info_asymmetry"] == "two_sided_private"]
    onesided_deals_all = [r["deal"] for r in train if r["info_asymmetry"] == "one_sided_buyer_known"]
    info_diff = np.mean(onesided_deals_all) - np.mean(twosided_deals)
    ai, bi = sum(onesided_deals_all), len(onesided_deals_all) - sum(onesided_deals_all)
    ci_, di_ = sum(twosided_deals), len(twosided_deals) - sum(twosided_deals)
    _, p_info = stats.fisher_exact([[ai, bi], [ci_, di_]], alternative="two-sided")

    results.append({
        "hypothesis": "Info Main Effect",
        "test": "One-sided info increases deal rate",
        "estimand": "P(deal|onesided) - P(deal|twosided)",
        "effect_size": f"{info_diff:+.3f}",
        "ci_lower": "",
        "ci_upper": "",
        "p_value": f"{p_info:.4f}",
        "p_value_wald": "",
        "odds_ratio": "",
        "or_ci": "",
        "direction": "CONFIRMED" if info_diff > 0 and p_info < 0.05 else "UNCLEAR",
        "confidence": "HIGH" if p_info < 0.001 else "MODERATE",
        "note": f"twosided={np.mean(twosided_deals):.3f}, onesided={np.mean(onesided_deals_all):.3f}",
    })

    # =========================================================================
    # Holdout validation: C10 and C12
    # =========================================================================
    holdout_data = [r for r in all_data if r["condition_short"] in HOLDOUT]
    for cid in sorted(HOLDOUT):
        h = [r for r in holdout_data if r["condition_short"] == cid]
        if not h:
            continue
        observed_rate = np.mean([r["deal"] for r in h])
        n_h = len(h)

        # Predict from non-holdout model
        comm = h[0]["communication"]
        vgap = h[0]["value_gap"]
        info = h[0]["info_asymmetry"]
        talk = 1 if comm != "none" else 0
        wide = 1 if vgap == "wide" else 0
        onesided = 1 if info == "one_sided_buyer_known" else 0
        x_pred = np.array([1, talk, wide, onesided])
        logit_pred = x_pred @ beta_h1
        predicted_rate = 1 / (1 + np.exp(-logit_pred))

        results.append({
            "hypothesis": f"Holdout {cid}",
            "test": f"Out-of-sample prediction for {cid}",
            "estimand": f"Predicted vs observed deal rate",
            "effect_size": f"predicted={predicted_rate:.3f}, observed={observed_rate:.3f}",
            "ci_lower": "",
            "ci_upper": "",
            "p_value": "",
            "p_value_wald": "",
            "odds_ratio": "",
            "or_ci": "",
            "direction": "CALIBRATED" if abs(predicted_rate - observed_rate) < 0.15 else "MISCALIBRATED",
            "confidence": "",
            "note": f"Residual={observed_rate - predicted_rate:+.3f}, n={n_h}",
        })

    # =========================================================================
    # Treatment-level descriptives (full data including holdout)
    # =========================================================================
    for dim_name, dim_key in [("Communication", "communication"), ("Value Gap", "value_gap"), ("Info", "info_asymmetry")]:
        levels = defaultdict(list)
        for r in all_data:
            levels[r[dim_key]].append(r["deal"])
        for lev, deals in sorted(levels.items()):
            rate, lo, hi = wilson_ci(sum(deals), len(deals))
            results.append({
                "hypothesis": f"Descriptive: {dim_name}",
                "test": f"Deal rate for {dim_name}={lev}",
                "estimand": f"P(deal|{dim_key}={lev})",
                "effect_size": f"{rate:.3f}",
                "ci_lower": f"{lo:.3f}",
                "ci_upper": f"{hi:.3f}",
                "p_value": "",
                "p_value_wald": "",
                "odds_ratio": "",
                "or_ci": "",
                "direction": "",
                "confidence": "Descriptive",
                "note": f"n={len(deals)}, deals={sum(deals)}, 95% Wilson CI",
            })

    outpath = os.path.join(ANALYSIS_DIR, "model_results.csv")
    with open(outpath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {len(results)} results to {outpath}")
    return results


def main():
    data = load_data()
    print(f"Loaded {len(data)} sessions")
    n_prod = len([r for r in data if "prod" in r.get("session_id", "")])
    print(f"  Production sessions: {n_prod if n_prod > 0 else len(data)}")
    print()

    cond_summary = summary_by_condition(data)
    print()

    # Print condition summary table
    print(f"{'Cond':<6} {'Comm':<14} {'VGap':<8} {'Info':<24} {'N':>3} {'Feas':>5} {'Deals':>6} {'Rate':>6} {'95%CI':>14} {'AvgP':>7} {'BuyE':>6} {'SelE':>6}")
    print("-" * 110)
    for c in cond_summary:
        ci_str = f"[{c['deal_rate_ci_lo']},{c['deal_rate_ci_hi']}]"
        print(f"{c['condition_id']:<6} {c['communication']:<14} {c['value_gap']:<8} {c['info_asymmetry']:<24} "
              f"{c['n_sessions']:>3} {c['n_feasible']:>5} {c['n_deals']:>6} {c['deal_rate']:>6} {ci_str:>14} "
              f"{c['avg_price']:>7} {c['avg_buyer_earnings']:>6} {c['avg_seller_earnings']:>6}")
    print()

    model_results = compute_model_results(data)
    print()

    # Print hypothesis results
    print("=" * 80)
    print("HYPOTHESIS RESULTS")
    print("=" * 80)
    for r in model_results:
        if r["hypothesis"].startswith("H") or r["hypothesis"].startswith("Holdout") or r["hypothesis"].startswith("Info"):
            print(f"\n  {r['hypothesis']}: {r['test']}")
            print(f"    Effect: {r['effect_size']}")
            if r["p_value"]:
                print(f"    p-value: {r['p_value']}")
            if r["odds_ratio"]:
                print(f"    OR: {r['odds_ratio']} {r['or_ci']}")
            print(f"    Direction: {r['direction']}  Confidence: {r['confidence']}")
            if r["note"]:
                print(f"    Note: {r['note']}")

    print("\n" + "=" * 80)
    print("DESCRIPTIVE RATES")
    print("=" * 80)
    for r in model_results:
        if r["hypothesis"].startswith("Descriptive"):
            print(f"  {r['test']}: {r['effect_size']} [{r['ci_lower']}, {r['ci_upper']}] ({r['note']})")


if __name__ == "__main__":
    main()
