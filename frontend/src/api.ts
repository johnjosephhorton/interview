import type { AgentConfig, Defaults, Game, Session } from "./types";

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
  respondentConfig?: AgentConfig,
  game?: string
): Promise<Session> {
  return request("/sessions", {
    method: "POST",
    body: JSON.stringify({
      interviewer_config: interviewerConfig,
      respondent_config: respondentConfig,
      game,
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

export async function getGames(): Promise<Game[]> {
  return request("/games");
}
