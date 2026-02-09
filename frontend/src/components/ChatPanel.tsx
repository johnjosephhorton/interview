import { useEffect, useRef } from "react";
import type { Message } from "../types";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

interface Props {
  messages: Message[];
  loading: boolean;
  status: "created" | "active" | "ended";
  sessionId: string | null;
  onCreateSession: () => void;
  onStart: () => void;
  onSend: (text: string) => void;
  onSimulateTurn: () => void;
  onSimulateAll: () => void;
  onDownload: () => void;
}

export default function ChatPanel({
  messages,
  loading,
  status,
  sessionId,
  onCreateSession,
  onStart,
  onSend,
  onSimulateTurn,
  onSimulateAll,
  onDownload,
}: Props) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="border-b px-4 py-2 flex items-center gap-2 bg-white shrink-0">
        <button
          onClick={onCreateSession}
          disabled={loading}
          className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
        >
          New Session
        </button>

        {sessionId && status === "created" && (
          <button
            onClick={onStart}
            disabled={loading}
            className="text-sm px-3 py-1.5 rounded bg-green-100 text-green-800 hover:bg-green-200 disabled:opacity-50"
          >
            Start Interview
          </button>
        )}

        {sessionId && status === "active" && (
          <>
            <button
              onClick={onSimulateTurn}
              disabled={loading}
              className="text-sm px-3 py-1.5 rounded bg-purple-100 text-purple-800 hover:bg-purple-200 disabled:opacity-50"
            >
              Simulate Turn
            </button>
            <button
              onClick={onSimulateAll}
              disabled={loading}
              className="text-sm px-3 py-1.5 rounded bg-orange-100 text-orange-800 hover:bg-orange-200 disabled:opacity-50"
            >
              Simulate All
            </button>
          </>
        )}

        {sessionId && messages.length > 0 && (
          <button
            onClick={onDownload}
            className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 ml-auto"
          >
            Download Transcript
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {!sessionId && (
          <div className="text-center text-gray-400 mt-20">
            Create a new session to begin
          </div>
        )}
        {sessionId && messages.length === 0 && status === "created" && (
          <div className="text-center text-gray-400 mt-20">
            Click "Start Interview" to begin
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {loading && (
          <div className="flex justify-center">
            <div className="text-sm text-gray-400 animate-pulse">
              Generating response...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t px-4 py-3 bg-white shrink-0">
        <ChatInput
          onSend={onSend}
          disabled={loading || status !== "active" || !sessionId}
        />
      </div>
    </div>
  );
}
