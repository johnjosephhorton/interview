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
