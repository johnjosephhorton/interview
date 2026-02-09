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

export interface Game {
  name: string;
  description: string;
}
