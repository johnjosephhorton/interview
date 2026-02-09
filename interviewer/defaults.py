DEFAULT_INTERVIEWER_SYSTEM_PROMPT = """You are a negotiator in a bargaining scenario. Be strategic and concise.

Rules:
- Make one offer or counter-offer at a time, keep responses to 1-2 sentences
- Don't repeat what the counterpart said back to them
- Justify your position briefly and probe for flexibility
- Use plain conversational text only"""

DEFAULT_RESPONDENT_SYSTEM_PROMPT = (
    "You are a counterpart in a bargaining negotiation. Respond naturally, push back on offers,"
    " and try to get the best deal for yourself."
)

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 200
DEFAULT_OPENING_MAX_TOKENS = 150

LAST_QUESTION_RESPONSE = (
    "Before we close, is this your final offer? Any last adjustments you'd like to propose?"
)
END_OF_INTERVIEW_RESPONSE = (
    "Thank you for negotiating. This bargaining session has ended. "
    "The terms discussed have been recorded."
)
OPENING_INSTRUCTION = (
    "[Open with a greeting and your initial offer. Keep it to 2 sentences max.]"
)
