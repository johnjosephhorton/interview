# Protocol: Bilateral Mug Bargain with Cheap Talk

## Overview

A buyer and seller negotiate over a coffee mug. The seller owns the mug; the buyer may want to purchase it. Each party has a private valuation. The experiment manipulates (1) whether pre-play communication is allowed, (2) the degree of value overlap between buyer and seller, and (3) whether information asymmetry is one-sided or two-sided.

## Participant Roles

- **Seller**: Owns the mug. Has a private willingness-to-accept (WTA). Will not sell below WTA.
- **Buyer**: May purchase the mug. Has a private willingness-to-pay (WTP). Will not pay above WTP.

Both agents are earnings-maximizers. Payoffs:
- If deal at price P: Seller earns (P − WTA), Buyer earns (WTP − P)
- If no deal: both earn $0

## Value Assignment

### Narrow value gap (b small)
- Buyer WTP ~ Uniform[$8, $12]
- Seller WTA ~ Uniform[$6, $10]
- Gains from trade exist ~75% of the time

### Wide value gap (b large)
- Buyer WTP ~ Uniform[$5, $15]
- Seller WTA ~ Uniform[$5, $15]
- Gains from trade exist ~50% of the time

Values are drawn independently per simulation using the condition-specific seed.

## Information Structure

### Two-sided private information
- Each party knows only their own valuation
- Neither knows the other's value or the distribution parameters (only that values are "somewhere between $5 and $15")

### One-sided (buyer WTP known)
- Seller's WTA is private
- Buyer's WTP is announced to both parties at the start
- This creates a pure Crawford-Sobel setup: seller = Sender, buyer = Receiver

## Phases per Session

### Phase 0: Value Assignment (hidden from agents)
The game manager draws WTP and WTA from the condition's distribution and injects them into prompts.

### Phase 1: Communication (treatment-dependent)

| Condition | Communication |
|-----------|--------------|
| `none` | Skip directly to Phase 2 |
| `cheap_talk` | Each party sends **one** free-form message simultaneously. Messages are shown to the counterpart before bargaining. |
| `extended_talk` | **Three** alternating rounds: Seller speaks → Buyer speaks → Seller speaks → Buyer speaks → Seller speaks → Buyer speaks. Then proceed to Phase 2. |

Messages are explicitly labeled as non-binding ("anything said here is cheap talk—you are not committed to any offer mentioned").

### Phase 2: Bargaining (3 rounds alternating offers)

1. **Round 1**: Seller proposes a price
2. **Round 2**: Buyer either accepts or counter-offers
3. **Round 3**: Seller either accepts the counter-offer or makes a final take-it-or-leave-it price
4. **Round 4**: Buyer accepts or rejects the final offer

If any offer is accepted, the deal closes at that price. If the buyer rejects the final offer, no deal occurs.

### Phase 3: Outcome Recording

Record:
- `deal`: boolean
- `final_price`: float or null
- `rounds_to_agreement`: integer (1-4) or null
- `buyer_wtp`: float (ground truth)
- `seller_wta`: float (ground truth)
- All messages exchanged in communication phase (for informativeness coding)

## Game-Over Detection

The manager outputs `══════════ GAME OVER ══════════` after Phase 2 concludes (deal or no-deal). Standard end-of-game markers per CLAUDE.md.

## Timing

- Communication phase: no time limit (LLM generates instantly)
- Bargaining phase: structured turns, no time limit
- Estimated wall-clock per simulation: ~30 seconds (6-12 LLM calls)
- Total: 360 simulations × 30s ≈ 3 hours at 1 concurrent session

## Compensation (human-in-the-loop mode)

If run with human subjects: participants receive a $5 show-up fee plus their earnings from the bargaining game (scaled to real dollars at 1:1).

## Ethics Notes

- No deception: all rules are explained truthfully to both parties
- Cheap talk is explicitly labeled as non-binding; participants are not misled about commitment
- No sensitive topics; standard economic game
