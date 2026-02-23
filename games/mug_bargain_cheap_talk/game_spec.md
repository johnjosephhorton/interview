# Game Specification: Mug Bargain with Cheap Talk

## Overview

A seller owns a coffee mug. A buyer may want to purchase it. Each party has a private valuation. Before bargaining, parties may exchange costless, non-binding messages (cheap talk). Then they negotiate through alternating offers.

## Roles

- **Seller**: Owns the mug. Has a private willingness-to-accept (WTA).
- **Buyer**: Potential purchaser. Has a private willingness-to-pay (WTP).

## Payoffs

- **Deal at price P**: Seller earns (P − WTA), Buyer earns (WTP − P)
- **No deal**: Both earn $0

## Treatment Dimensions

### Communication (3 levels)
- `none`: No pre-play messages. Go straight to bargaining.
- `cheap_talk`: One simultaneous round of free-form messages before bargaining. Non-binding.
- `extended_talk`: Three alternating rounds of messages (Seller→Buyer→Seller→Buyer→Seller→Buyer) before bargaining.

### Value Gap (2 levels)
- `narrow`: Buyer WTP ~ U[8, 12], Seller WTA ~ U[6, 10]. Gains from trade likely.
- `wide`: Buyer WTP ~ U[5, 15], Seller WTA ~ U[5, 15]. Trade may be infeasible.

### Information Asymmetry (2 levels)
- `two_sided_private`: Neither party knows the other's valuation.
- `one_sided_buyer_known`: Buyer's WTP is common knowledge; Seller's WTA is private.

## Bargaining Protocol (held constant)

1. **Round 1**: Seller proposes a price
2. **Round 2**: Buyer accepts or counter-offers
3. **Round 3**: Seller accepts the counter-offer or makes a final take-it-or-leave-it price
4. **Round 4**: Buyer accepts or rejects the final offer

If any offer is accepted, the deal closes at that price. If the buyer rejects the final offer, no deal.

## Outcome Variables

| Variable | Type | Definition |
|----------|------|-----------|
| `deal` | binary | Whether a transaction occurred |
| `final_price` | continuous | Agreed price (null if no deal) |
| `surplus_captured` | continuous | (WTP − WTA) realized / (WTP − WTA) available |
| `price_split_ratio` | continuous | (P − WTA) / (WTP − WTA) |
| `rounds_to_agreement` | count | Bargaining rounds before deal |
| `comm_messages` | text[] | All communication-phase messages |
