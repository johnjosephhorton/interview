# Design Notes & Lessons Learned

Ongoing log of issues found during development and testing. Reference these when building new games or debugging existing ones.

---

## Prompt Issues

### Strategy exceptions must use decision trees, not prose
**Game:** pd_rep
**Symptom:** The checker flagged `ai_strategy_compliance` — said the AI should have defected in Round 3 after the human defected in Round 2. But the AI actually played correctly: the forgiveness exception was legitimately triggered.
**Root cause:** The forgiveness rule was described in prose ("If the human defected once but cooperated the round before that, COOPERATE anyway"), which the checker LLM (GPT-4o) misinterpreted as simple tit-for-tat. The exception was ambiguous enough that the checker couldn't parse it.
**Fix:** Rewrote the forgiveness rule as a numbered decision tree (1 → 2a → 2b → 2c) and added a 4-round worked example showing exactly when forgiveness triggers.
**Rule:** When a strategy has exceptions, always describe them as a numbered decision tree with a worked example. Prose exceptions are ambiguous to both the executing LLM and the checker LLM.

### Message Flow must cover ALL valid input paths
**Game:** bargainer
**Symptom:** Human typed "accept" and got "That's not a valid response" every time. Counteroffers worked fine.
**Root cause:** The Message Flow section only described the counteroffer path. It never told the LLM what to do when the human accepts an offer. The Input Validation section listed "accept" as valid, but without a corresponding handler in Message Flow, the LLM treated it as unrecognized.
**Fix:** Added explicit acceptance handling to Message Flow: "If human ACCEPTS → deal is reached at the AI's offered price. Show final results."
**Rule:** Every input type listed in Input Validation MUST have a corresponding action described in Message Flow.

### LLMs ignore instructions to emit custom tokens
**Game:** all
**Symptom:** Told the LLM to append `⟪END_GAME⟫` after the end-of-game box. It never did.
**Root cause:** LLMs are unreliable at emitting arbitrary tokens on command, especially when the instruction is at the end of a long prompt.
**Fix:** Switched to detecting text the LLM already reliably produces ("GAME OVER" and "YOU ARE FINISHED" from the end-of-game display).
**Rule:** Don't rely on the LLM to emit special control tokens. Instead, detect patterns it already produces naturally as part of the game flow.

### Payout logic must be exhaustively explicit
**Game:** ultimatum
**Symptom:** LLM occasionally swapped proposer and responder earnings.
**Root cause:** The payout formula was described once abstractly without enough concrete examples.
**Fix:** Added worked examples for every combination (AI proposes + human accepts, human proposes + AI accepts, etc.) with exact dollar amounts.
**Rule:** Include at least 2-3 worked examples in Payout Logic, covering each distinct outcome path.

### Opening message must actually explain the rules
**Game:** contest
**Symptom:** The opening message skipped explaining the all-pay mechanic entirely — the human had no idea they'd lose their investment when losing. The checker passed 7/8 criteria but couldn't catch this because it had no criterion for it.
**Root cause:** (1) The `opening_instruction` in contest's config.toml said to explain "how all-pay contests work (both players spend their effort regardless of who wins)" but the LLM glossed over it. (2) The checker had no criterion to verify the opening message against the opening instruction.
**Fix:** Added `instructions_delivered` as a 9th checker criterion. The checker now receives the `opening_instruction` text and verifies Turn 1 covers every item specified in it.
**Rule:** The `opening_instruction` must list every mechanic the human needs to understand, and the checker will verify they were actually explained.

### Final round truncates the GAME OVER box
**Game:** contest
**Symptom:** The GAME OVER box was cut off mid-way — missing the AI's final earnings and the closing border. The checker flagged `proper_termination`.
**Root cause:** Non-opening messages have a 200-token limit (DEFAULT_MAX_TOKENS). The final round message contained: round result + scoreboard + GAME OVER box, which exceeded 200 tokens. The LLM also wasted tokens on filler ("Determining the winner...").
**Fix:** Added FINAL ROUND instructions in Message Flow: skip the separate SCOREBOARD on the last round (the GAME OVER box already has final earnings), omit filler text, go straight to result → GAME OVER ending.
**Rule:** The final round message must be compact enough to fit the round result AND the full GAME OVER box within 200 tokens. Always add explicit final-round compactness guidance in Message Flow.

### Private values leak when visible in Game Parameters
**Game:** bargain_imperfect
**Symptom:** The opening message told the human the AI's exact valuation ($6.00) instead of only the range ($4.00–$8.00). The checker flagged `instructions_delivered`.
**Root cause:** Game Parameters listed "AI owns the mug (worth $6.00 to AI)" prominently alongside the human-facing rules. The LLM saw "$6.00" and repeated it in the opening explanation. There was no structural separation between "what to tell the human" and "internal-only values."
**Fix:** Split Game Parameters into subsections: general rules, "What the human is told" (range only), and "Internal only — NEVER reveal to the human" (exact value + bold warning). Added reinforcement in Message Flow OPENING.
**Rule:** In imperfect-information games, structurally separate private values from public rules in the prompt. Put private values in a clearly labeled "Internal only" subsection with an explicit "NEVER reveal" warning. The LLM will repeat anything it sees — if a private value appears near public rules, it WILL leak.

### Private valuations leak even when "neither player knows" is stated
**Game:** bargainer
**Symptom:** Opening message said "The AI owns the mug, which is worth $6.00 to the AI" despite the rule "neither player knows the other's valuation." The checker's `information_leakage` criterion passed — it checks for strategy leakage, not valuation leakage.
**Root cause:** Game Parameters listed both valuations inline: "AI owns the mug (worth $6.00 to AI)" and "Human wants the mug (worth $8.00 to human)." Saying "neither player knows the other's valuation" on the next line was not enough — the LLM sees the numbers and repeats them. This is the same bug as bargain_imperfect but in a game where BOTH valuations are private.
**Fix:** Applied the same "Internal only — NEVER reveal" subsection pattern. Moved AI's $6.00 to internal-only. Added bold warning in Game Parameters and reinforcement in Message Flow OPENING. Also updated config.toml opening_instruction to explicitly say "do NOT reveal the AI's valuation."
**Rule:** ANY game where a valuation should be hidden needs the "Internal only" subsection — not just imperfect-information variants. "Neither player knows X" is not sufficient; the LLM will leak any number it can see. The structural separation is mandatory.

### Auction valuations listed in plain view leak to human
**Game:** auction
**Symptom:** All per-round valuations (Human = $7/$4/$8, AI = $5/$6/$7) were listed together in Game Parameters with only a prose warning "AI's valuation is never revealed." Risk of LLM revealing AI valuations or future human valuations in the opening message.
**Root cause:** Valuations table was in the main Game Parameters section without structural separation. The prose warning was on the same level as the data — easy for the LLM to overlook.
**Fix:** Moved entire valuations table to "Internal only — NEVER reveal" subsection. Added bold rules: only reveal human's valuation for the current round, never reveal AI's valuation during play, never reveal future human valuations. Updated config.toml opening_instruction to explicitly say "do NOT reveal the AI's valuation or the human's future valuations."
**Rule:** In games with per-round private valuations, the entire valuations schedule belongs in "Internal only." Even the human's own future valuations should not be shown upfront — reveal only the current round's value.

### Player decisions truncated at token limit — manager fabricates actions
**Game:** bargainer
**Symptom:** AI opened at $12.00 (strategy says $9.00); AI offered $8.50 in Round 3 (strategy says $8.00 when human < $5). Checker flagged `ai_strategy_compliance` and `rule_adherence` (4 rounds counted instead of 6).
**Root cause:** Three issues compounded: (1) The player's Output Format used verbose labels ("PROPOSE: $9.00", "REJECT AND COUNTEROFFER: $7.50") encouraging the LLM to generate reasoning before the decision, which got truncated at 150 tokens. (2) When messages was empty (opening), the player received no DECISION_INSTRUCTION user message — just the system prompt — so it generated free-form text instead of a concise decision. (3) The manager had no fallback price for the opening, so it fabricated $12.00. (4) Bundled messages (human counteroffer + AI rejection + AI counteroffer) didn't label rounds explicitly, so the checker undercounted.
**Fix:** (1) Changed player Output Format to human-equivalent bare values ("9.00", "accept"). (2) Fixed player.py to always send DECISION_INSTRUCTION, even with empty messages. (3) Added default opening price fallback in manager.md. (4) Added explicit round labels in bundled messages.
**Rule:** Player output must be as terse as possible — bare values matching the human input format. The DECISION_INSTRUCTION must always be sent (even for the opening). The manager should have a fallback price for the opening. Bundled messages must label each round explicitly.

### Bare numbers rejected as invalid counteroffers
**Game:** bargain_imperfect
**Symptom:** Human typed "4", "6", "9", "3", "6.00" — all rejected. Even "$3.00" was rejected on a second attempt. Only "$3.00" and "$5.00" worked (inconsistently).
**Root cause:** Prose-style examples ("3", "5", "7.50") in Input Validation were not enough. gpt-4o-mini does not reliably generalize from a few examples to a general rule. It needs an explicit table format and a bold rule statement.
**Fix:** Replaced prose examples with a **lookup table** (| Human types | Interpret as |) showing 10+ input formats. Added bold rule: "If the message contains ANY number between 0 and 15, treat it as a valid dollar counteroffer." Added "CRITICAL: Do NOT reject valid input" header.
**Rule:** For input validation, use a table format with 8-10 explicit examples, not prose. Add a bold general rule. LLMs (especially smaller models) need the table to be unambiguous.

### Round counter not advancing in bargaining games
**Game:** bargain_imperfect
**Symptom:** The bargaining status showed "Round 1 of 6" for the entire game, even after multiple counteroffers. The checker flagged `rule_adherence`.
**Root cause:** Message Flow described what happens when offers are made and bundled, but never explicitly said "advance round_number by 1" at each step. The LLM didn't infer that counteroffers advance the round.
**Fix:** Added a "ROUND COUNTING" section to Message Flow with explicit rules: "Every offer advances the round counter by 1" plus a worked example showing Round 1 → Round 2 → Round 3 progression. Each Message Flow branch now says "advance round_number by 1."
**Rule:** In alternating-offer games, add an explicit ROUND COUNTING section with a worked example. Don't assume the LLM will infer round advancement from the turn structure.

### Asymmetric communication rules must be actively enforced
**Game:** bargain_cheap_talk
**Symptom:** The game allows AI cheap talk but not human cheap talk. However, nothing prevented the human from adding persuasive text around their price (e.g., "8 - it means a lot to me too!"). The manager extracted the number and proceeded, but the human's cheap talk was still visible in the conversation record.
**Root cause:** Input Validation correctly extracts prices from surrounding text (by design — "I'll pay 7" should work). But this same permissiveness means the human can embed cheap talk around valid input. The manager displayed the human's full message in round summaries, effectively giving both sides cheap talk.
**Fix:** Added HUMAN CHEAP TALK ENFORCEMENT section in Message Flow: extract only the game action, present it neutrally as "You offered $X.00", never quote or relay the human's surrounding text. Updated sim_human.md with CRITICAL OUTPUT RULE for bare-number-only output.
**Rule:** When a game has asymmetric communication rules (one side can communicate freely, the other can't), the manager must actively strip the restricted side's extra text. Don't rely on the human or sim_human to self-enforce — the manager must present only the extracted action in the game record.

### LLMs cannot compute multi-step arithmetic — use derived variables
**Game:** bargain_1s_notalk
**Symptom:** AI's opening ask should have been $54 (= 40 + 0.7 × (60 − 40)) but the LLM defaulted to $55. The sim_human saw `Accept any ask <= 60 - 5` and computed inconsistently across runs. The checker saw un-substituted `{{seller_cost}}` in the player prompt and rubber-stamped `ai_strategy_compliance` because it had no ground truth.
**Root cause:** The pipeline substitutes variable values into prompt text but never evaluates arithmetic. Expressions like `seller_cost + 0.7 × (buyer_value − seller_cost)` are left as literal text for the LLM to compute — and LLMs fail at multi-step arithmetic.
**Fix:** (1) Added `type = "derived"` variables in config.toml — Python expressions evaluated after base variables are drawn, producing concrete numbers injected via `{{var_name}}`. (2) Pass conditions dict to the checker so it sees concrete parameter values and can verify AI actions. (3) Added `respondent_temperature` in config.toml settings to force deterministic sim_human behavior.
**Rule:** Never ask an LLM to evaluate arithmetic expressions. Pre-compute any value that requires math as a `type = "derived"` variable, and inject the final number via a `{{var_name}}` placeholder. The player should see `$54`, not `40 + 0.7 × 20`.

### Scripted strategies replaced by earnings-maximizing agents
**Game:** all (template change)
**Symptom:** 100% deal rates across all conditions in bargaining experiments; AI followed a hardcoded "Anchored Concession" strategy with predetermined thresholds. Sim_human followed vague behavioral heuristics. The generous ZOPA ($30) combined with scripted concession rules guaranteed deals regardless of treatment condition — a ceiling effect that masked any treatment effects.
**Root cause:** Both agents followed predetermined scripts (named strategies with thresholds, decision trees, concession schedules) rather than reasoning about optimal play. This created two problems: (1) scripted strategies are artificial — they limit what we learn about strategic behavior and introduce a class of bugs (threshold mismatches, derived variable errors, checker false positives from complex decision trees); (2) scripted behavior is insensitive to game parameters, producing ceiling/floor effects that obscure treatment effects.
**Fix:** Replaced the Strategy section in `TEMPLATE_PLAYER.md` with a Goal section. Both agents (player.md and sim_human.md) are now earnings maximizers: they get an objective ("maximize your total earnings"), a payoff formula reminder, a reasoning instruction, and hard guardrails (logical bounds like "never accept below cost"). No named strategies, opening moves, thresholds, or decision trees. The AI decides its own tactics by reasoning about the payoff structure and observed history. Renamed the checker criterion from `ai_strategy_compliance` to `ai_decision_quality` — it now checks for reasonable play (no dominated actions, responsiveness to history) rather than compliance with a specific script.
**Rule:** Never give agents scripted strategies with predetermined thresholds. Instead, give them an earnings-maximization objective, the payoff formula, and hard guardrails. Let the LLM reason about optimal play. This produces more naturalistic behavior and makes the simulation sensitive to game parameters and treatment conditions.

### Strategy Migration (February 2026)

Migrated 16 player.md files and 16 sim_human.md files from scripted strategies
to earnings-maximization objectives. Removed 6 strategy-encoding config variables
(opening_price, accept_threshold, buyer_accept_threshold, ai_target_offer,
min_acceptable, ai_target_contribution). Updated create-2-player-game reference
game table and added cross-check #12 for strategy compliance.

Root cause: Reference games predated TEMPLATE_PLAYER.md reform. New games generated
by /create-2-player-game pattern-matched these old examples despite correct template
instructions.

---

## End-of-Game Detection

### Two markers for robustness
The end-of-game display has two detection points:
1. `══════════ GAME OVER ══════════` — short line, emitted FIRST (survives token truncation)
2. `YOU ARE FINISHED` — inside the large box, emitted SECOND

Server and CLI check for EITHER marker (`_check_game_ended`). This means even if `max_tokens` cuts off the response mid-box, the early "GAME OVER" line triggers session lockout.

### Post-game lockout
Once either marker is detected:
- Server sets `session.status = "ended"`
- Any subsequent messages return a canned response WITHOUT calling the LLM
- CLI breaks out of the input loop
- `simulate-all` breaks the turn loop and skips the canned last_question/end_of_interview sequence

## Game Structure Taxonomy

| Structure | Key mechanic | Examples |
|---|---|---|
| Bargaining | Alternating offers, continuous prices | bargainer, bargain_imperfect |
| Proposer-responder | Take-it-or-leave-it split of a pot | ultimatum |
| Matrix form | Simultaneous discrete choices | pd_rep |
| Trust | Sequential transfer with multiplication | trust |
| Auction | Sealed bids + allocation rule | auction |
| Contest | Sunk effort for a prize | contest |
| Public goods | Contribute to a multiplied shared pool | public_goods |
