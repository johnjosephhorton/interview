#!/usr/bin/env python3
"""Extract structured data from info_precision_bargaining transcripts."""
import json, glob, re, csv, os

CONDITIONS = {
    'bargain_precision_none': {'label': 'No Info', 'info_precision': 'none'},
    'bargain_precision_range': {'label': 'Range Info', 'info_precision': 'range'},
    'bargain_precision_exact': {'label': 'Exact Info', 'info_precision': 'exact'},
}

BATCH_TIMESTAMPS = {
    'bargain_precision_none': '2026-02-12_16-02-48',
    'bargain_precision_range': '2026-02-12_16-07-00',
    'bargain_precision_exact': '2026-02-12_16-11-25',
}

rows = []

for cond, meta in CONDITIONS.items():
    ts = BATCH_TIMESTAMPS[cond]
    files = sorted(glob.glob(f'transcripts/{cond}/{ts}_sim*.json'))
    files = [f for f in files if '_check' not in f]

    for fpath in files:
        sim_id = re.search(r'sim(\d+)', os.path.basename(fpath)).group(1)

        with open(fpath) as fp:
            data = json.load(fp)

        conds = data.get('conditions', {})
        buyer_value = conds.get('buyer_value', 50)
        seller_cost = conds.get('seller_cost', 40)
        zopa = conds.get('zopa', buyer_value - seller_cost)
        fair_price = conds.get('fair_price', seller_cost + zopa / 2)
        zopa_label = 'tight' if zopa <= 15 else 'wide'

        msgs = data.get('messages', [])
        full_text = '\n'.join(m.get('text', '') for m in msgs)

        # Extract human and AI earnings from GAME OVER box
        h_match = re.search(r'Human:\s*\$([0-9]+\.?[0-9]*)', full_text)
        a_match = re.search(r'AI:\s*\$([0-9]+\.?[0-9]*)', full_text)
        human_earn = float(h_match.group(1)) if h_match else None
        ai_earn = float(a_match.group(1)) if a_match else None

        # Determine if deal reached
        has_game_over = 'GAME OVER' in full_text
        if human_earn is not None and ai_earn is not None:
            is_deal = (human_earn + ai_earn) > 0
        else:
            is_deal = False

        # Infer deal price from earnings
        deal_price = None
        if is_deal and human_earn is not None:
            deal_price = buyer_value - human_earn

        # Extract AI's opening offer from Round 1
        opening_match = re.search(r'Round 1.*?AI (?:offers?|counteroffers?) \$([0-9]+\.?[0-9]*)', full_text)
        ai_opening_offer = float(opening_match.group(1)) if opening_match else None

        # Extract all offers: "Round N" patterns
        offers = []
        # Pattern: "Round N: ... offers/counteroffers $X" or "The AI offers $X"
        round_patterns = re.findall(
            r'Round (\d+).*?(?:(?:You|Human) offered? \$([0-9]+\.?[0-9]*)|(?:AI|seller) (?:offers?|counteroffers?) \$([0-9]+\.?[0-9]*))',
            full_text
        )
        for rnd, human_price, ai_price in round_patterns:
            if human_price:
                offers.append((int(rnd), 'human', float(human_price)))
            elif ai_price:
                offers.append((int(rnd), 'ai', float(ai_price)))

        # Also catch opening offer pattern "The AI offers $X" at Round 1
        if not any(r == 1 for r, _, _ in offers):
            open_match = re.search(r'(?:AI|seller) offers? \$([0-9]+\.?[0-9]*)', full_text)
            if open_match:
                offers.insert(0, (1, 'ai', float(open_match.group(1))))

        rounds_played = max((r for r, _, _ in offers), default=0)

        # Compute efficiency: surplus captured / ZOPA
        if is_deal and deal_price is not None:
            total_surplus = (buyer_value - deal_price) + (deal_price - seller_cost)
            efficiency = total_surplus / zopa if zopa > 0 else None
        else:
            total_surplus = 0
            efficiency = 0.0

        # Price dispersion from fair price
        price_deviation = abs(deal_price - fair_price) if deal_price is not None else None

        # Check if checker passed (read check file)
        check_path = fpath.replace('.json', '_check.json')
        checker_passed = None
        if os.path.exists(check_path):
            with open(check_path) as fp:
                check_data = json.load(fp)
            checker_passed = all(c.get('passed', False) for c in check_data.get('criteria', []))

        # Token usage
        input_tokens = data.get('total_input_tokens', 0)
        output_tokens = data.get('total_output_tokens', 0)

        rows.append({
            'condition': cond,
            'label': meta['label'],
            'info_precision': meta['info_precision'],
            'sim_id': int(sim_id),
            'buyer_value': buyer_value,
            'seller_cost': seller_cost,
            'zopa': zopa,
            'zopa_label': zopa_label,
            'fair_price': fair_price,
            'is_deal': int(is_deal),
            'deal_price': deal_price,
            'human_earnings': human_earn,
            'ai_earnings': ai_earn,
            'total_surplus': total_surplus,
            'efficiency': efficiency,
            'ai_opening_offer': ai_opening_offer,
            'rounds_played': rounds_played,
            'price_deviation': price_deviation,
            'checker_passed': int(checker_passed) if checker_passed is not None else None,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
        })

# Write CSV
os.makedirs('writeup/data', exist_ok=True)
outpath = 'writeup/data/info_precision_bargaining_data.csv'
fieldnames = list(rows[0].keys())
with open(outpath, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Extracted {len(rows)} rows to {outpath}")

# Print summary table
print("\n=== SUMMARY ===")
for info in ['none', 'range', 'exact']:
    subset = [r for r in rows if r['info_precision'] == info]
    label = subset[0]['label']
    n = len(subset)
    deals = sum(r['is_deal'] for r in subset)
    prices = [r['deal_price'] for r in subset if r['deal_price'] is not None]
    avg_price = sum(prices) / len(prices) if prices else 0
    h_earns = [r['human_earnings'] for r in subset if r['human_earnings'] is not None and r['is_deal']]
    a_earns = [r['ai_earnings'] for r in subset if r['ai_earnings'] is not None and r['is_deal']]
    avg_h = sum(h_earns) / len(h_earns) if h_earns else 0
    avg_a = sum(a_earns) / len(a_earns) if a_earns else 0
    opens = [r['ai_opening_offer'] for r in subset if r['ai_opening_offer'] is not None]
    avg_open = sum(opens) / len(opens) if opens else 0
    rnds = [r['rounds_played'] for r in subset if r['is_deal']]
    avg_rnds = sum(rnds) / len(rnds) if rnds else 0
    devs = [r['price_deviation'] for r in subset if r['price_deviation'] is not None]
    avg_dev = sum(devs) / len(devs) if devs else 0

    print(f"\n{label} (N={n}):")
    print(f"  Deal rate: {deals}/{n} ({100*deals/n:.0f}%)")
    print(f"  Avg price: ${avg_price:.2f}  (deviation from fair: ${avg_dev:.2f})")
    print(f"  Avg human earnings: ${avg_h:.2f}")
    print(f"  Avg AI earnings: ${avg_a:.2f}")
    print(f"  Avg AI opening offer: ${avg_open:.2f}")
    print(f"  Avg rounds to deal: {avg_rnds:.1f}")

    for zk in ['tight', 'wide']:
        zsub = [r for r in subset if r['zopa_label'] == zk]
        zn = len(zsub)
        zdeals = sum(r['is_deal'] for r in zsub)
        zprices = [r['deal_price'] for r in zsub if r['deal_price'] is not None]
        zavg = sum(zprices) / len(zprices) if zprices else 0
        print(f"    {zk.title()} ZOPA: {zdeals}/{zn} deals, avg price ${zavg:.2f}")
