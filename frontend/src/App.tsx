import { useCallback, useEffect, useRef, useState } from "react";
import type { AgentConfig, Defaults, Message } from "./types";
import * as api from "./api";
import Layout from "./components/Layout";
import ChatPanel from "./components/ChatPanel";
import ConfigPanel from "./components/ConfigPanel";

export default function App() {
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

  // Debounce timer for config updates
  const configTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
  }, []);

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

  // Debounced config update
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

  if (!defaults || !interviewerConfig || !respondentConfig) {
    return (
      <div className="flex items-center justify-center h-screen text-gray-500">
        Loading...
      </div>
    );
  }

  return (
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
          interviewerConfig={interviewerConfig}
          respondentConfig={respondentConfig}
          onConfigChange={handleConfigChange}
        />
      }
    />
  );
}
