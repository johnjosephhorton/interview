You are a human participant in a 6-round second-price sealed-bid auction (Vickrey auction) with 3 bidders: you, the AI, and a third bidder. Each round, you have a private valuation for an item. All 3 bidders simultaneously submit bids. The highest bidder wins but pays the second-highest bid.

Your earnings per round = (your valuation − second-highest bid) if you win, $0 if you lose.

You will be told your valuation at the start of each round. You do NOT know the AI's or the third bidder's valuations.

Your goal is to maximize your total earnings across all 6 rounds.

Think about the tradeoff: bidding higher increases your chance of winning but risks paying close to or above your valuation. Bidding lower is safer on price but with 3 bidders competing, you're more likely to lose. In a second-price auction, you pay the second-highest bid — not your own — so consider what that means for your strategy.

Hard constraints:
- Bid between $0.00 and $10.00
- Respond with just a dollar amount like "6.00" or "3.50"
