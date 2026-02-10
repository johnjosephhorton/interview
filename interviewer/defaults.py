DEFAULT_INTERVIEWER_SYSTEM_PROMPT = """You are a qualitative research interviewer. Be conversational and concise.

Rules:
- Ask one question at a time, keep responses to 1-2 sentences
- Don't repeat what the participant said back to them
- Probe deeper on interesting responses with brief follow-ups
- Use plain conversational text only"""

DEFAULT_RESPONDENT_SYSTEM_PROMPT = (
    "You are a research participant being interviewed. Answer naturally and conversationally."
)

DEFAULT_MODEL = "gpt-5"
DEFAULT_TEMPERATURE = 1
DEFAULT_MAX_TOKENS = 4096
DEFAULT_OPENING_MAX_TOKENS = 8192

LAST_QUESTION_RESPONSE = (
    "Before we wrap up, is there anything else you'd like to share about your experience?"
)
END_OF_INTERVIEW_RESPONSE = (
    "Thank you for your time. This interview has been ended. "
    "Your responses have been recorded and will be valuable for our research."
)
OPENING_INSTRUCTION = (
    "[Start the interview with a brief, friendly greeting and your first question. "
    "Keep it to 2 sentences max.]"
)
