import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentConfig,
  Defaults,
  GameDefaults,
  GameMessage,
  Message,
} from "./types";
import * as api from "./api";
import Layout from "./components/Layout";
import ChatPanel from "./components/ChatPanel";
import ConfigPanel from "./components/ConfigPanel";
import GameChatPanel from "./components/GameChatPanel";
import GameConfigPanel from "./components/GameConfigPanel";

type AppMode = "interview" | "game";

export default function App() {
  const [mode, setMode] = useState<AppMode>("interview");

  // --- Interview state ---
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<"created" | "active" | "ended">(
    "created"
  );
  const [interviewerConfig, setInterviewerConfig] =
    useState<AgentConfig | null>(null);
  const [respondentConfig, setRespondentConfig] =
    useState<AgentConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [defaults, setDefaults] = useState<Defaults | null>(null);
  const configTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // --- Game state ---
  const [gameSessionId, setGameSessionId] = useState<string | null>(null);
  const [gameMessages, setGameMessages] = useState<GameMessage[]>([]);
  const [gameStatus, setGameStatus] = useState<"created" | "active" | "ended">(
    "created"
  );
  const [managerConfig, setManagerConfig] = useState<AgentConfig | null>(null);
  const [playerConfig, setPlayerConfig] = useState<AgentConfig | null>(null);
  const [gameLoading, setGameLoading] = useState(false);
  const [gameDefaults, setGameDefaults] = useState<GameDefaults | null>(null);
  const gameConfigTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load defaults on mount
  useEffect(() => {
    api.getDefaults().then((d) => {
      setDefaults(d);
      setInterviewerConfig({
        system_prompt: d.interviewer_system_prompt,
        model: d.model,
        temperature: d.temperature,
        max_tokens: d.max_tokens,
      });
      setRespondentConfig({
        system_prompt: d.respondent_system_prompt,
        model: d.model,
        temperature: d.temperature,
        max_tokens: d.max_tokens,
      });
    });
    api.getGameDefaults().then((d) => {
      setGameDefaults(d);
      setManagerConfig({
        system_prompt: d.manager_system_prompt,
        model: d.model,
        temperature: d.temperature,
        max_tokens: d.manager_max_tokens,
      });
      setPlayerConfig({
        system_prompt: d.player_system_prompt,
        model: d.model,
        temperature: d.temperature,
        max_tokens: d.player_max_tokens,
      });
    });
  }, []);

  // --- Interview callbacks ---

  const createNewSession = useCallback(async () => {
    if (!interviewerConfig || !respondentConfig) return;
    setLoading(true);
    try {
      const session = await api.createSession(
        interviewerConfig,
        respondentConfig
      );
      setSessionId(session.id);
      setMessages([]);
      setStatus("created");
    } finally {
      setLoading(false);
    }
  }, [interviewerConfig, respondentConfig]);

  const handleStart = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const result = await api.startSession(sessionId);
      setMessages((prev) => [
        ...prev,
        { role: "interviewer", text: result.message.text },
      ]);
      setStatus("active");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleSend = useCallback(
    async (text: string) => {
      if (!sessionId) return;
      setLoading(true);
      try {
        const result = await api.sendMessage(sessionId, text);
        setMessages((prev) => [
          ...prev,
          { role: "respondent", text: result.respondent_message.text },
          { role: "interviewer", text: result.interviewer_message.text },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  const handleSimulateTurn = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const result = await api.simulateTurn(sessionId);
      setMessages((prev) => [
        ...prev,
        { role: "respondent", text: result.respondent_message.text },
        { role: "interviewer", text: result.interviewer_message.text },
      ]);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleSimulateAll = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const result = await api.simulateAll(sessionId);
      setMessages((prev) => [
        ...prev,
        ...result.new_messages.map((m) => ({
          role: m.role as "interviewer" | "respondent",
          text: m.text,
        })),
      ]);
      setStatus("ended");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleDownload = useCallback(async () => {
    if (!sessionId) return;
    const data = await api.getTranscript(sessionId, "json");
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transcript-${sessionId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [sessionId]);

  const handleConfigChange = useCallback(
    (type: "interviewer" | "respondent", config: AgentConfig) => {
      if (type === "interviewer") setInterviewerConfig(config);
      else setRespondentConfig(config);

      if (!sessionId) return;

      if (configTimerRef.current) clearTimeout(configTimerRef.current);
      configTimerRef.current = setTimeout(() => {
        const payload =
          type === "interviewer"
            ? { interviewerConfig: config }
            : { respondentConfig: config };
        api
          .updateConfig(
            sessionId,
            payload.interviewerConfig,
            (payload as { respondentConfig?: AgentConfig }).respondentConfig
          )
          .catch(console.error);
      }, 300);
    },
    [sessionId]
  );

  // --- Game callbacks ---

  const createNewGameSession = useCallback(async () => {
    if (!managerConfig || !playerConfig) return;
    setGameLoading(true);
    try {
      const session = await api.createGameSession(
        undefined,
        undefined,
        managerConfig,
        playerConfig
      );
      setGameSessionId(session.id);
      setGameMessages([]);
      setGameStatus("created");
    } finally {
      setGameLoading(false);
    }
  }, [managerConfig, playerConfig]);

  const handleGameStart = useCallback(async () => {
    if (!gameSessionId) return;
    setGameLoading(true);
    try {
      const result = await api.startGame(gameSessionId);
      const visibleMsgs = result.messages.filter(
        (m) => m.visible
      ) as GameMessage[];
      setGameMessages((prev) => [...prev, ...visibleMsgs]);
      setGameStatus("active");
    } finally {
      setGameLoading(false);
    }
  }, [gameSessionId]);

  const handleGameSend = useCallback(
    async (text: string) => {
      if (!gameSessionId) return;
      setGameLoading(true);
      // Immediately show the human message
      setGameMessages((prev) => [
        ...prev,
        { role: "human" as const, text, visible: true },
      ]);
      try {
        const result = await api.sendGameMove(gameSessionId, text);
        const visibleMsgs = result.messages.filter(
          (m) => m.visible
        ) as GameMessage[];
        setGameMessages((prev) => [...prev, ...visibleMsgs]);
      } finally {
        setGameLoading(false);
      }
    },
    [gameSessionId]
  );

  const handleGameDownload = useCallback(async () => {
    if (!gameSessionId) return;
    const data = await api.getGameTranscript(gameSessionId, "json");
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `game-transcript-${gameSessionId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [gameSessionId]);

  const handleGameConfigChange = useCallback(
    (type: "manager" | "player", config: AgentConfig) => {
      if (type === "manager") setManagerConfig(config);
      else setPlayerConfig(config);

      if (!gameSessionId) return;

      if (gameConfigTimerRef.current)
        clearTimeout(gameConfigTimerRef.current);
      gameConfigTimerRef.current = setTimeout(() => {
        api
          .updateGameConfig(
            gameSessionId,
            type === "manager" ? config : undefined,
            type === "player" ? config : undefined
          )
          .catch(console.error);
      }, 300);
    },
    [gameSessionId]
  );

  // --- Loading guard ---
  const interviewReady = defaults && interviewerConfig && respondentConfig;
  const gameReady = gameDefaults && managerConfig && playerConfig;

  if (!interviewReady && !gameReady) {
    return (
      <div className="flex items-center justify-center h-screen text-gray-500">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Mode toggle header */}
      <div className="bg-white border-b px-6 py-3 flex items-center gap-4 shrink-0">
        <h1 className="text-lg font-bold text-gray-900">AI Interviewer</h1>
        <div className="flex rounded-lg border overflow-hidden ml-4">
          <button
            onClick={() => setMode("interview")}
            className={`px-4 py-1.5 text-sm font-medium ${
              mode === "interview"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Interview
          </button>
          <button
            onClick={() => setMode("game")}
            className={`px-4 py-1.5 text-sm font-medium ${
              mode === "game"
                ? "bg-cyan-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Game
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0">
        {mode === "interview" && interviewReady ? (
          <Layout
            left={
              <ChatPanel
                messages={messages}
                loading={loading}
                status={status}
                sessionId={sessionId}
                onCreateSession={createNewSession}
                onStart={handleStart}
                onSend={handleSend}
                onSimulateTurn={handleSimulateTurn}
                onSimulateAll={handleSimulateAll}
                onDownload={handleDownload}
              />
            }
            right={
              <ConfigPanel
                interviewerConfig={interviewerConfig!}
                respondentConfig={respondentConfig!}
                onConfigChange={handleConfigChange}
              />
            }
          />
        ) : mode === "game" && gameReady ? (
          <Layout
            left={
              <GameChatPanel
                messages={gameMessages}
                loading={gameLoading}
                status={gameStatus}
                sessionId={gameSessionId}
                onCreateSession={createNewGameSession}
                onStart={handleGameStart}
                onSend={handleGameSend}
                onDownload={handleGameDownload}
              />
            }
            right={
              <GameConfigPanel
                managerConfig={managerConfig!}
                playerConfig={playerConfig!}
                onConfigChange={handleGameConfigChange}
              />
            }
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Loading...
          </div>
        )}
      </div>
    </div>
  );
}
