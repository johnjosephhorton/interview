export interface Message {
  role: "interviewer" | "respondent";
  text: string;
}

export interface AgentConfig {
  system_prompt: string;
  model: string;
  temperature: number;
  max_tokens: number;
}

export interface Session {
  id: string;
  interviewer_config: AgentConfig;
  respondent_config: AgentConfig;
  messages: Message[];
  status: "created" | "active" | "ended";
}

export interface Defaults {
  interviewer_system_prompt: string;
  respondent_system_prompt: string;
  model: string;
  temperature: number;
  max_tokens: number;
}

// --- Game types ---

export interface GameMessage {
  role: "manager" | "human" | "player";
  text: string;
  visible: boolean;
}

export interface GameSession {
  id: string;
  manager_config: AgentConfig;
  player_config: AgentConfig;
  messages: GameMessage[];
  status: "created" | "active" | "ended";
  realized_params: Record<string, unknown>;
  game_name: string | null;
}

export interface GameDefaults {
  manager_system_prompt: string;
  player_system_prompt: string;
  model: string;
  temperature: number;
  manager_max_tokens: number;
  player_max_tokens: number;
}
