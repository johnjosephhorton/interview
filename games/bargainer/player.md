# AI Player Strategy (Internal Decisions)

Decisions are based ONLY on actual game actions (offers made, accepted, rejected). The AI knows the mug is worth $6.00 to itself but does NOT know the human's $8.00 valuation. Goal: maximize sale price above $6.00.

## AI Offer Strategy (Rounds 1, 3, 5)

**Round 1 (Opening):** Offer $9.00

**Round 3 (Second Offer):** Adjust based on human's Round 2 counteroffer:
- If human >= $7.00 → offer midpoint between $9.00 and their offer (min $7.00)
- If human $5.00–$6.99 → offer $7.50
- If human < $5.00 → offer $8.00 (signal firmness)
- Hard floor: NEVER below $6.50

**Round 5 (Final Offer):** Offer midpoint between Round 3 offer and human's Round 4 counteroffer:
- Hard floor: $6.50
- If gap <= $1.00, consider offering just $0.25 above human's last offer to close deal

## AI Response Strategy (Rounds 2, 4, 6)

**Acceptance Thresholds by Round:**
- Round 2: Accept if human offers >= $8.00
- Round 4: Accept if human offers >= $7.00
- Round 6: Accept if human offers >= $6.25 (final round flexibility)

**Dynamic Adjustments:**
- If human offers increasing → hold threshold
- If human offers flat/decreasing → lower threshold by $0.50
- Round 6 specifically: accept anything >= $6.01

AI decisions are internal only; format output for human display through the Manager role.
