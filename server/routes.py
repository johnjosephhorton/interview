from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from interviewer import (
    DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_RESPONDENT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
    AgentConfig,
    Interviewer,
    Message,
    Simulation,
    list_games,
    load_game,
    save_transcript,
)
from interviewer.respondent import SimulatedRespondent

from .session import Session, create_session, delete_session, get_session

router = APIRouter(prefix="/api")


def _get_session_or_404(session_id: str) -> Session:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# --- Request/Response models ---


class CreateSessionRequest(BaseModel):
    interviewer_config: AgentConfig | None = None
    respondent_config: AgentConfig | None = None
    game: str | None = None


class UpdateConfigRequest(BaseModel):
    interviewer_config: AgentConfig | None = None
    respondent_config: AgentConfig | None = None


class SendMessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    role: str
    text: str


class InterviewerResponse(BaseModel):
    interviewer_message: MessageResponse
    respondent_message: MessageResponse | None = None


# --- Endpoints ---


@router.post("/sessions")
async def api_create_session(req: CreateSessionRequest | None = None):
    game_config = None
    game_name = None
    if req and req.game:
        game_config = load_game(req.game)
        game_name = req.game
    if req:
        session = create_session(
            req.interviewer_config, req.respondent_config,
            game_name=game_name, game_config=game_config,
        )
    else:
        session = create_session()
    return session.model_dump()


@router.get("/sessions/{session_id}")
async def api_get_session(session_id: str):
    session = _get_session_or_404(session_id)
    return session.model_dump()


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: str):
    if not delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}


@router.patch("/sessions/{session_id}/config")
async def api_update_config(session_id: str, req: UpdateConfigRequest):
    session = _get_session_or_404(session_id)
    if req.interviewer_config:
        session.interviewer_config = req.interviewer_config
    if req.respondent_config:
        session.respondent_config = req.respondent_config
    return session.model_dump()


@router.post("/sessions/{session_id}/start")
async def api_start_session(session_id: str):
    session = _get_session_or_404(session_id)
    interviewer = Interviewer()
    response = await interviewer.generate_response(
        session.messages, session.interviewer_config, message_type="opening_message",
        game_config=session.game_config,
    )
    msg = Message(role="interviewer", text=response.text)
    session.messages.append(msg)
    session.status = "active"
    return {"message": msg.model_dump(), "llm_call_info": response.llm_call_info}


@router.post("/sessions/{session_id}/messages")
async def api_send_message(session_id: str, req: SendMessageRequest):
    session = _get_session_or_404(session_id)

    # Add user (respondent) message
    user_msg = Message(role="respondent", text=req.text)
    session.messages.append(user_msg)

    # Generate interviewer response
    interviewer = Interviewer()
    response = await interviewer.generate_response(
        session.messages, session.interviewer_config, message_type="next_message",
        game_config=session.game_config,
    )
    interviewer_msg = Message(role="interviewer", text=response.text)
    session.messages.append(interviewer_msg)

    return {
        "respondent_message": user_msg.model_dump(),
        "interviewer_message": interviewer_msg.model_dump(),
        "llm_call_info": response.llm_call_info,
    }


@router.post("/sessions/{session_id}/simulate-turn")
async def api_simulate_turn(session_id: str):
    """One turn: AI respondent replies, then interviewer follows up."""
    session = _get_session_or_404(session_id)

    respondent = SimulatedRespondent()
    resp = await respondent.generate_response(session.messages, session.respondent_config)
    resp_msg = Message(role="respondent", text=resp.text)
    session.messages.append(resp_msg)

    interviewer = Interviewer()
    follow_up = await interviewer.generate_response(
        session.messages, session.interviewer_config, message_type="next_message",
        game_config=session.game_config,
    )
    interviewer_msg = Message(role="interviewer", text=follow_up.text)
    session.messages.append(interviewer_msg)

    return {
        "respondent_message": resp_msg.model_dump(),
        "interviewer_message": interviewer_msg.model_dump(),
    }


@router.post("/sessions/{session_id}/simulate-all")
async def api_simulate_all(session_id: str, max_turns: int = Query(default=5)):
    """Run the interview to completion."""
    session = _get_session_or_404(session_id)

    interviewer = Interviewer()
    respondent = SimulatedRespondent()

    # If no messages yet, generate opening
    if not session.messages:
        opening = await interviewer.generate_response(
            session.messages, session.interviewer_config, message_type="opening_message",
            game_config=session.game_config,
        )
        session.messages.append(Message(role="interviewer", text=opening.text))

    new_messages = []
    for _ in range(max_turns):
        resp = await respondent.generate_response(session.messages, session.respondent_config)
        resp_msg = Message(role="respondent", text=resp.text)
        session.messages.append(resp_msg)
        new_messages.append(resp_msg)

        follow_up = await interviewer.generate_response(
            session.messages, session.interviewer_config, message_type="next_message",
            game_config=session.game_config,
        )
        int_msg = Message(role="interviewer", text=follow_up.text)
        session.messages.append(int_msg)
        new_messages.append(int_msg)

    # Last question + response + end
    last_q = await interviewer.generate_response(
        session.messages, session.interviewer_config, message_type="last_question",
        game_config=session.game_config,
    )
    lq_msg = Message(role="interviewer", text=last_q.text)
    session.messages.append(lq_msg)
    new_messages.append(lq_msg)

    resp = await respondent.generate_response(session.messages, session.respondent_config)
    resp_msg = Message(role="respondent", text=resp.text)
    session.messages.append(resp_msg)
    new_messages.append(resp_msg)

    end = await interviewer.generate_response(
        session.messages, session.interviewer_config, message_type="end_of_interview",
        game_config=session.game_config,
    )
    end_msg = Message(role="interviewer", text=end.text)
    session.messages.append(end_msg)
    new_messages.append(end_msg)

    session.status = "ended"

    return {
        "new_messages": [m.model_dump() for m in new_messages],
        "total_messages": len(session.messages),
    }


@router.get("/sessions/{session_id}/transcript")
async def api_get_transcript(
    session_id: str, format: Literal["json", "csv"] = Query(default="json")
):
    from interviewer import Transcript

    session = _get_session_or_404(session_id)
    transcript = Transcript(
        messages=session.messages,
        interviewer_config=session.interviewer_config,
        respondent_config=session.respondent_config,
    )

    if format == "csv":
        import csv
        import io

        from fastapi.responses import StreamingResponse

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["turn", "role", "text"])
        for i, msg in enumerate(transcript.messages):
            writer.writerow([i + 1, msg.role, msg.text])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transcript.csv"},
        )
    else:
        return transcript.model_dump()


@router.get("/config/defaults")
async def api_get_defaults():
    return {
        "interviewer_system_prompt": DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
        "respondent_system_prompt": DEFAULT_RESPONDENT_SYSTEM_PROMPT,
        "model": DEFAULT_MODEL,
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
    }


@router.get("/games")
async def api_list_games():
    return list_games()
