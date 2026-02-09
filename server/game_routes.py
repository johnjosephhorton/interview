from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from interviewer import AgentConfig, GameRunner
from interviewer.game_defaults import (
    DEFAULT_GAME_MANAGER_SYSTEM_PROMPT,
    DEFAULT_GAME_MAX_TOKENS,
    DEFAULT_GAME_MODEL,
    DEFAULT_GAME_PLAYER_MAX_TOKENS,
    DEFAULT_GAME_PLAYER_SYSTEM_PROMPT,
    DEFAULT_GAME_TEMPERATURE,
)

from .game_session import (
    GameSession,
    create_game_session,
    delete_game_session,
    get_game_orchestrator,
    get_game_session,
)

game_router = APIRouter(prefix="/api/games")


def _get_game_session_or_404(session_id: str) -> GameSession:
    session = get_game_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    return session


# --- Request/Response models ---


class CreateGameSessionRequest(BaseModel):
    game_path: str | None = None
    param_overrides: dict[str, Any] | None = None
    manager_config: AgentConfig | None = None
    player_config: AgentConfig | None = None


class UpdateGameConfigRequest(BaseModel):
    manager_config: AgentConfig | None = None
    player_config: AgentConfig | None = None


class SendGameMoveRequest(BaseModel):
    text: str


# --- Endpoints ---


@game_router.post("/sessions")
async def api_create_game_session(req: CreateGameSessionRequest | None = None):
    if req and req.game_path:
        try:
            realized = GameRunner.load_game(req.game_path, req.param_overrides)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        session = create_game_session(
            manager_config=realized.manager_config,
            player_config=realized.player_config,
            realized_params=realized.realized_params,
            game_name=realized.name,
            human_instructions=realized.human_instructions,
        )
    elif req:
        session = create_game_session(req.manager_config, req.player_config)
    else:
        session = create_game_session()
    return session.model_dump()


@game_router.get("/sessions/{session_id}")
async def api_get_game_session(session_id: str):
    session = _get_game_session_or_404(session_id)
    return session.model_dump()


@game_router.delete("/sessions/{session_id}")
async def api_delete_game_session(session_id: str):
    if not delete_game_session(session_id):
        raise HTTPException(status_code=404, detail="Game session not found")
    return {"status": "deleted"}


@game_router.patch("/sessions/{session_id}/config")
async def api_update_game_config(session_id: str, req: UpdateGameConfigRequest):
    session = _get_game_session_or_404(session_id)
    if req.manager_config:
        session.manager_config = req.manager_config
    if req.player_config:
        session.player_config = req.player_config
    return session.model_dump()


@game_router.post("/sessions/{session_id}/start")
async def api_start_game(session_id: str):
    """Generate opening game message, potentially involving a player turn."""
    session = _get_game_session_or_404(session_id)
    orchestrator = get_game_orchestrator(session_id)
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not found")

    new_msgs, llm_calls = await orchestrator.process_opening(
        session.manager_config, session.player_config
    )

    session.messages.extend(new_msgs)
    session.status = "active"

    visible_messages = [m.model_dump() for m in new_msgs if m.visible]
    return {
        "messages": visible_messages,
        "llm_calls": [c.model_dump() for c in llm_calls],
    }


@game_router.post("/sessions/{session_id}/move")
async def api_send_game_move(session_id: str, req: SendGameMoveRequest):
    """Process a human move through the manager-player pipeline."""
    session = _get_game_session_or_404(session_id)
    orchestrator = get_game_orchestrator(session_id)
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not found")

    new_msgs, llm_calls = await orchestrator.process_human_input(
        req.text, session.messages, session.manager_config, session.player_config
    )

    session.messages.extend(new_msgs)

    visible_messages = [m.model_dump() for m in new_msgs if m.visible]
    return {
        "messages": visible_messages,
        "llm_calls": [c.model_dump() for c in llm_calls],
    }


@game_router.get("/sessions/{session_id}/transcript")
async def api_get_game_transcript(
    session_id: str, format: Literal["json", "csv"] = Query(default="json")
):
    from interviewer.game_models import GameTranscript

    session = _get_game_session_or_404(session_id)
    transcript = GameTranscript(
        messages=session.messages,
        manager_config=session.manager_config,
        player_config=session.player_config,
        realized_params=session.realized_params,
        game_name=session.game_name,
    )

    if format == "csv":
        import csv
        import io

        from fastapi.responses import StreamingResponse

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["turn", "role", "text", "visible"])
        for i, msg in enumerate(transcript.messages):
            writer.writerow([i + 1, msg.role, msg.text, msg.visible])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=game_transcript.csv"},
        )
    else:
        return transcript.model_dump()


@game_router.get("/config/defaults")
async def api_get_game_defaults():
    return {
        "manager_system_prompt": DEFAULT_GAME_MANAGER_SYSTEM_PROMPT,
        "player_system_prompt": DEFAULT_GAME_PLAYER_SYSTEM_PROMPT,
        "model": DEFAULT_GAME_MODEL,
        "temperature": DEFAULT_GAME_TEMPERATURE,
        "manager_max_tokens": DEFAULT_GAME_MAX_TOKENS,
        "player_max_tokens": DEFAULT_GAME_PLAYER_MAX_TOKENS,
    }


@game_router.get("/available")
async def api_list_available_games():
    """List all available game definitions."""
    return GameRunner.list_games("prompts")
