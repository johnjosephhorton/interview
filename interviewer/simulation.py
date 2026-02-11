from __future__ import annotations

from datetime import datetime, timezone

from .core import Interviewer
from .models import AgentConfig, GameConfig, Message, Transcript


class Simulation:
    """Orchestrates a multi-turn automated interview between Interviewer and SimulatedRespondent."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key

    async def run(
        self,
        interviewer_config: AgentConfig,
        respondent_config: AgentConfig,
        max_turns: int = 5,
        on_message: callable | None = None,
        game_config: GameConfig | None = None,
    ) -> Transcript:
        """Run a full automated interview.

        Args:
            interviewer_config: Config for the interviewer agent.
            respondent_config: Config for the respondent agent.
            max_turns: Number of interviewer→respondent exchanges (excluding opening/closing).
            on_message: Optional callback(Message) called after each message is generated.

        Returns:
            Transcript with all messages and metadata.
        """
        from .respondent import SimulatedRespondent

        interviewer = Interviewer(api_key=self._api_key)
        respondent = SimulatedRespondent(api_key=self._api_key)

        transcript = Transcript(
            interviewer_config=interviewer_config,
            respondent_config=respondent_config,
        )
        messages: list[Message] = []

        def _add_message(role: str, text: str, llm_call_info=None, player_llm_call_info=None):
            msg = Message(role=role, text=text)
            messages.append(msg)
            transcript.messages.append(msg)
            if llm_call_info:
                transcript.llm_calls.append(llm_call_info)
                transcript.total_input_tokens += llm_call_info.input_tokens
                transcript.total_output_tokens += llm_call_info.output_tokens
            if player_llm_call_info:
                transcript.llm_calls.append(player_llm_call_info)
                transcript.total_input_tokens += player_llm_call_info.input_tokens
                transcript.total_output_tokens += player_llm_call_info.output_tokens
            if on_message:
                on_message(msg)

        # Opening message
        opening = await interviewer.generate_response(
            messages, interviewer_config, message_type="opening_message",
            game_config=game_config,
        )
        _add_message("interviewer", opening.text, opening.llm_call_info, opening.player_llm_call_info)

        # Main conversation turns
        for _ in range(max_turns):
            # Respondent replies
            resp = await respondent.generate_response(messages, respondent_config)
            _add_message("respondent", resp.text, resp.llm_call_info)

            # Interviewer follows up
            follow_up = await interviewer.generate_response(
                messages, interviewer_config, message_type="next_message",
                game_config=game_config,
            )
            _add_message("interviewer", follow_up.text, follow_up.llm_call_info, follow_up.player_llm_call_info)

        # Last question
        last_q = await interviewer.generate_response(
            messages, interviewer_config, message_type="last_question",
            game_config=game_config,
        )
        _add_message("interviewer", last_q.text, last_q.llm_call_info)

        # Respondent answers last question
        resp = await respondent.generate_response(messages, respondent_config)
        _add_message("respondent", resp.text, resp.llm_call_info)

        # End of interview
        end = await interviewer.generate_response(
            messages, interviewer_config, message_type="end_of_interview",
            game_config=game_config,
        )
        _add_message("interviewer", end.text, end.llm_call_info)

        transcript.ended_at = datetime.now(timezone.utc).isoformat()
        return transcript
