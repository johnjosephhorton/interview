import type {
  AgentConfig,
  Defaults,
  GameDefaults,
  GameMessage,
  GameSession,
  Session,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json();
}

export async function createSession(
  interviewerConfig?: AgentConfig,
  respondentConfig?: AgentConfig
): Promise<Session> {
  return request("/sessions", {
    method: "POST",
    body: JSON.stringify({
      interviewer_config: interviewerConfig,
      respondent_config: respondentConfig,
    }),
  });
}

export async function getSession(id: string): Promise<Session> {
  return request(`/sessions/${id}`);
}

export async function deleteSession(id: string): Promise<void> {
  await request(`/sessions/${id}`, { method: "DELETE" });
}

export async function updateConfig(
  id: string,
  interviewerConfig?: AgentConfig,
  respondentConfig?: AgentConfig
): Promise<Session> {
  return request(`/sessions/${id}/config`, {
    method: "PATCH",
    body: JSON.stringify({
      interviewer_config: interviewerConfig,
      respondent_config: respondentConfig,
    }),
  });
}

export async function startSession(
  id: string
): Promise<{ message: { role: string; text: string } }> {
  return request(`/sessions/${id}/start`, { method: "POST" });
}

export async function sendMessage(
  id: string,
  text: string
): Promise<{
  respondent_message: { role: string; text: string };
  interviewer_message: { role: string; text: string };
}> {
  return request(`/sessions/${id}/messages`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export async function simulateTurn(
  id: string
): Promise<{
  respondent_message: { role: string; text: string };
  interviewer_message: { role: string; text: string };
}> {
  return request(`/sessions/${id}/simulate-turn`, { method: "POST" });
}

export async function simulateAll(
  id: string,
  maxTurns: number = 5
): Promise<{
  new_messages: { role: string; text: string }[];
  total_messages: number;
}> {
  return request(`/sessions/${id}/simulate-all?max_turns=${maxTurns}`, {
    method: "POST",
  });
}

export async function getTranscript(
  id: string,
  format: "json" | "csv" = "json"
): Promise<unknown> {
  return request(`/sessions/${id}/transcript?format=${format}`);
}

export async function getDefaults(): Promise<Defaults> {
  return request("/config/defaults");
}

// --- Game API ---

export async function createGameSession(
  gamePath?: string,
  paramOverrides?: Record<string, unknown>,
  managerConfig?: AgentConfig,
  playerConfig?: AgentConfig
): Promise<GameSession> {
  return request("/games/sessions", {
    method: "POST",
    body: JSON.stringify({
      game_path: gamePath,
      param_overrides: paramOverrides,
      manager_config: managerConfig,
      player_config: playerConfig,
    }),
  });
}

export async function getGameSession(id: string): Promise<GameSession> {
  return request(`/games/sessions/${id}`);
}

export async function deleteGameSession(id: string): Promise<void> {
  await request(`/games/sessions/${id}`, { method: "DELETE" });
}

export async function updateGameConfig(
  id: string,
  managerConfig?: AgentConfig,
  playerConfig?: AgentConfig
): Promise<GameSession> {
  return request(`/games/sessions/${id}/config`, {
    method: "PATCH",
    body: JSON.stringify({
      manager_config: managerConfig,
      player_config: playerConfig,
    }),
  });
}

export async function startGame(
  id: string
): Promise<{ messages: GameMessage[]; llm_calls: unknown[] }> {
  return request(`/games/sessions/${id}/start`, { method: "POST" });
}

export async function sendGameMove(
  id: string,
  text: string
): Promise<{ messages: GameMessage[]; llm_calls: unknown[] }> {
  return request(`/games/sessions/${id}/move`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export async function getGameTranscript(
  id: string,
  format: "json" | "csv" = "json"
): Promise<unknown> {
  return request(`/games/sessions/${id}/transcript?format=${format}`);
}

export async function getGameDefaults(): Promise<GameDefaults> {
  return request("/games/config/defaults");
}
